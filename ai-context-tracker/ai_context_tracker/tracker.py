from datetime import datetime, timezone

from .alerts import evaluate
from .config import Config, load_config
from .models import resolve_model, capabilities_line
from .state import SessionState, utcnow
from .timefmt import time_line


class ContextTracker:
    """Core engine shared by the MCP server, CLI dashboard and SDK wrappers."""

    def __init__(self, config: Config | None = None, state: SessionState | None = None):
        self.config = config or load_config()
        self.state = state or SessionState(model=self.config.model, provider=self.config.provider)
        if not self.state.model_history:
            self.state.model_history = [self.state.model] if self.state.model else []

    # -- model ----------------------------------------------------------
    @property
    def model_spec(self) -> dict:
        return resolve_model(self.state.model, self.config.model_overrides)

    def _detect_model_switch(self, model: str) -> str | None:
        if not model or resolve_model(model)["id"] == resolve_model(self.state.model)["id"] and self.state.model:
            if model:
                self.state.model = model
            return None
        prev = self.state.model
        self.state.model = model
        self.state.provider = resolve_model(model)["provider"]
        self.state.model_history.append(model)
        if not prev:
            return None
        spec = self.model_spec
        tasks = [t for t in self.state.tasks if t["status"] != "done"]
        brief = (f"MODEL SWITCH: you are now {spec['id']} (previously {prev}). "
                 f"{capabilities_line(spec)}. Session so far: turn {self.state.turn}, "
                 f"{self.state.usage['total']:,} tokens used")
        if tasks:
            brief += ". Open tasks: " + "; ".join(f"[{t['status']}] {t['title']}" for t in tasks)
        if self.state.message_summaries:
            brief += ". Last activity: " + self.state.message_summaries[-1]["text"]
        return brief

    # -- usage ----------------------------------------------------------
    def record_usage(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0,
                     reasoning_tokens: int = 0, model: str = "", summary: str = "") -> dict:
        switch_brief = self._detect_model_switch(model) if model else None
        u = self.state.usage
        u["input"] += input_tokens
        u["output"] += output_tokens
        u["cached"] += cached_tokens
        u["reasoning"] += reasoning_tokens
        u["total"] = u["input"] + u["output"] + u["reasoning"]
        self.state.turn += 1
        self.state.last_message_at = utcnow()
        self.state.add_summary(summary)
        spec = self.model_spec
        self.state.cost_usd += (input_tokens * spec["price_in"] + output_tokens * spec["price_out"]) / 1_000_000
        new_alerts = []
        if self.config.features.get("token_tracking", True):
            new_alerts = evaluate(self.pct_remaining(), self.config.alert_thresholds,
                                  self.config.red_alert_threshold, self.state.alerts_fired)
            for a in new_alerts:
                self.state.alerts_fired.append(a["threshold"])
                self.state.active_alerts.append({**a, "at": utcnow()})
        auto_handoff = None
        if (self.config.auto_handoff and self.pct_remaining() <= self.config.danger_threshold
                and not any(h.get("auto") for h in self.state.handoffs)):
            auto_handoff = self.create_handoff(
                goals="(auto-generated at danger threshold)",
                progress=self.state.message_summaries[-1]["text"] if self.state.message_summaries else "see task list",
                remaining="; ".join(t["title"] for t in self.state.tasks if t["status"] != "done") or "unknown",
                decisions="", auto=True)
        self.save()
        return {"alerts": new_alerts, "model_switch_brief": switch_brief, "auto_handoff": auto_handoff}

    def pct_used(self) -> float:
        cw = self.model_spec["context_window"]
        return min(100.0, 100.0 * self.state.usage["total"] / cw) if cw else 0.0

    def pct_remaining(self) -> float:
        return 100.0 - self.pct_used()

    # -- tasks / handoffs -------------------------------------------------
    def update_task(self, title: str, status: str, task_id: str = "") -> dict:
        status = status if status in ("todo", "in_progress", "done") else "todo"
        task = next((t for t in self.state.tasks if t["id"] == task_id or t["title"] == title), None)
        if task:
            task["status"], task["title"] = status, title
            task["updated_at"] = utcnow()
        else:
            task = {"id": f"t{len(self.state.tasks) + 1}", "title": title, "status": status, "updated_at": utcnow()}
            self.state.tasks.append(task)
        self.save()
        return task

    def create_handoff(self, goals: str, progress: str, remaining: str, decisions: str = "", auto: bool = False) -> dict:
        handoff = {
            "created_at": utcnow(), "auto": auto, "goals": goals, "progress": progress,
            "remaining_tasks": remaining, "key_decisions": decisions,
            "model": self.state.model, "turn": self.state.turn,
            "usage": dict(self.state.usage), "cost_usd": round(self.state.cost_usd, 4),
            "tasks": list(self.state.tasks),
        }
        self.state.handoffs.append(handoff)
        d = self.config.state_dir / "handoffs"
        d.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        import json
        (d / f"{self.state.session_id}-{stamp}.json").write_text(json.dumps(handoff, indent=2))
        md = (f"# Session Handoff — {self.state.session_id}\n\n- **When:** {handoff['created_at']}\n"
              f"- **Model:** {self.state.model} | Turn {self.state.turn} | {self.state.usage['total']:,} tokens\n\n"
              f"## Goals\n{goals}\n\n## Progress\n{progress}\n\n## Remaining\n{remaining}\n\n## Key Decisions\n{decisions or 'n/a'}\n")
        (d / f"{self.state.session_id}-{stamp}.md").write_text(md)
        self.save()
        return handoff

    # -- status ----------------------------------------------------------
    def header(self) -> str:
        parts = []
        if self.config.features.get("time_awareness", True):
            parts.append(time_line(self.config.timezone, self.state.started_at, self.state.last_message_at))
        if self.config.features.get("turn_counter", True):
            parts.append(f"Turn {self.state.turn}")
        if self.config.features.get("token_tracking", True):
            spec = self.model_spec
            parts.append(f"Tokens: {self.state.usage['total']:,}/{spec['context_window']:,} ({self.pct_used():.1f}% used, {self.pct_remaining():.1f}% left)")
        if self.config.features.get("cost_tracking", True):
            parts.append(f"Cost: ${self.state.cost_usd:.4f}")
        return " | ".join(parts)

    def status(self) -> dict:
        spec = self.model_spec
        return {
            "session_id": self.state.session_id,
            "model": spec["id"],
            "provider": spec["provider"],
            "context_window": spec["context_window"],
            "max_output": spec["max_output"],
            "capabilities": spec["capabilities"],
            "turn": self.state.turn,
            "usage": self.state.usage,
            "pct_used": round(self.pct_used(), 2),
            "pct_remaining": round(self.pct_remaining(), 2),
            "cost_usd": round(self.state.cost_usd, 4),
            "started_at": self.state.started_at,
            "last_message_at": self.state.last_message_at,
            "tasks": self.state.tasks,
            "active_alerts": self.state.active_alerts,
            "handoffs": len(self.state.handoffs),
        }

    def save(self):
        self.state.save(self.config.state_dir)

    def resume(self, session_id: str = "") -> "SessionState | None":
        st = (SessionState.load(self.config.state_dir, session_id) if session_id
              else SessionState.load_latest(self.config.state_dir))
        if st:
            self.state = st
        return st
