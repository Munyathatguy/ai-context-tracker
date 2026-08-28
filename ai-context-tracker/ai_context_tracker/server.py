"""MCP server exposing awareness tools over stdio."""
import json
from datetime import UTC, datetime

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .models import capabilities_line, resolve_model
from .providers import get_provider
from .state import SessionState
from .timefmt import humanize_gap
from .tracker import ContextTracker

mcp = FastMCP("ai-context-tracker")
_tracker: ContextTracker | None = None


def get_tracker() -> ContextTracker:
    global _tracker
    if _tracker is None:
        _tracker = ContextTracker(load_config())
        prev = SessionState.load_latest(_tracker.config.state_dir)
        if prev and prev.turn > 0 and prev.session_id != _tracker.state.session_id:
            gap = (datetime.now(UTC) - datetime.fromisoformat(prev.last_message_at)).total_seconds()
            _tracker.resume_offer = (
                f"💾 Previous session detected: {prev.session_id} (model {prev.model}, turn {prev.turn}, "
                f"{prev.usage['total']:,} tokens, last active {humanize_gap(gap)}). "
                "Ask the user if they want to continue it — call resume_session to restore tasks, "
                "summaries and handoffs, or ignore to start fresh.")
    return _tracker


def _wrap(body: str, extra_alerts: list | None = None) -> str:
    t = get_tracker()
    lines = [f"[AWARENESS] {t.header()}"]
    offer = getattr(t, "resume_offer", None)
    if offer:
        lines.append(offer)
        t.resume_offer = None
    for a in (extra_alerts or []):
        lines.append(a["message"] if isinstance(a, dict) else str(a))
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


@mcp.tool()
def get_status() -> str:
    """Current session status: token usage, remaining context, time, cost, tasks and alerts."""
    t = get_tracker()
    return _wrap(json.dumps(t.status(), indent=2), t.state.active_alerts[-2:])


@mcp.tool()
def record_usage(input_tokens: int, output_tokens: int, cached_tokens: int = 0,
                 reasoning_tokens: int = 0, model: str = "", summary: str = "",
                 rate_limit_remaining_tokens: int = -1, rate_limit_limit_tokens: int = -1) -> str:
    """Record token usage from the latest API exchange. Call this every turn with the usage
    numbers from the response metadata. Optionally pass the model id, a one-line summary
    of what happened this turn (used for crash recovery), and rate-limit headroom from the
    response headers (e.g. x-ratelimit-remaining-tokens / x-ratelimit-limit-tokens)."""
    t = get_tracker()
    result = t.record_usage(
        input_tokens, output_tokens, cached_tokens, reasoning_tokens, model, summary,
        rl_remaining_tokens=rate_limit_remaining_tokens if rate_limit_remaining_tokens >= 0 else None,
        rl_limit_tokens=rate_limit_limit_tokens if rate_limit_limit_tokens > 0 else None)
    body = [f"Recorded. Session total: {t.state.usage['total']:,} tokens ({t.pct_used():.1f}% of context window used)."]
    if result["model_switch_brief"]:
        body.append(result["model_switch_brief"])
    if result["auto_handoff"]:
        body.append("An automatic handoff summary was saved (danger threshold reached).")
    return _wrap("\n".join(body), result["alerts"])


@mcp.tool()
def count_tokens(text: str, model: str = "") -> str:
    """Pre-count tokens for text using the provider's native count endpoint (exact counts).
    Falls back to a chars/4 estimate when no API key is configured."""
    t = get_tracker()
    model = model or t.state.model or t.config.model
    spec = resolve_model(model, t.config.model_overrides)
    provider = get_provider(spec["provider"]) or get_provider(t.config.provider)
    n = provider.count_tokens(spec["id"], text) if provider else len(text) // 4
    projected = t.state.usage["total"] + n
    pct = 100.0 * projected / spec["context_window"]
    body = (f"count: {n:,} tokens | if sent, context would be {projected:,}/{spec['context_window']:,} "
            f"({pct:.1f}% full)")
    if pct >= 100 - t.config.danger_threshold:
        body += " — DANGER: this request would push the context into the danger zone. Consider a handoff."
    return _wrap(body)


@mcp.tool()
def create_handoff(goals: str, progress: str, remaining_tasks: str, key_decisions: str = "") -> str:
    """Create a structured session handoff summary (goals, progress, remaining tasks, key
    decisions), persisted to disk as JSON + markdown for resuming in a fresh session."""
    t = get_tracker()
    h = t.create_handoff(goals, progress, remaining_tasks, key_decisions)
    return _wrap(f"Handoff saved for session {t.state.session_id} at {h['created_at']}. "
                 f"A new session can load it via resume_session.")


@mcp.tool()
def resume_session(session_id: str = "") -> str:
    """Load the most recent saved session (or a specific session_id) and inject its state:
    task checklist, last message summaries, token usage, model config and latest handoff."""
    t = get_tracker()
    t.resume_offer = None
    st = t.resume(session_id)
    if not st:
        return _wrap("No saved session found. Starting fresh.")
    lines = [f"RESUMED session {st.session_id} — model {st.model}, turn {st.turn}, "
             f"{st.usage['total']:,} tokens used, ${st.cost_usd:.4f} spent."]
    if st.tasks:
        lines.append("Task checklist:")
        lines += [f"  [{x['status']}] {x['title']}" for x in st.tasks]
    if st.message_summaries:
        lines.append("Recent activity:")
        lines += [f"  - {s['text']}" for s in st.message_summaries]
    if st.handoffs:
        h = st.handoffs[-1]
        lines.append(f"Latest handoff ({h['created_at']}): goals={h['goals']} | progress={h['progress']} | remaining={h['remaining_tasks']}")
    return _wrap("\n".join(lines))


@mcp.tool()
def update_task(title: str, status: str, task_id: str = "") -> str:
    """Register progress on a multi-step task. status: todo | in_progress | done.
    The checklist persists to disk and survives crashes."""
    t = get_tracker()
    task = t.update_task(title, status, task_id)
    done = sum(1 for x in t.state.tasks if x["status"] == "done")
    checklist = "\n".join(f"  [{x['status']}] {x['title']}" for x in t.state.tasks)
    return _wrap(f"Task '{task['title']}' -> {task['status']} ({done}/{len(t.state.tasks)} done)\n{checklist}")


@mcp.tool()
def get_model_info(model: str = "") -> str:
    """Model self-awareness: context window, max output and capabilities of the active (or given) model."""
    t = get_tracker()
    spec = resolve_model(model or t.state.model or t.config.model, t.config.model_overrides)
    return _wrap(capabilities_line(spec) + f"\nPricing: ${spec['price_in']}/M input, ${spec['price_out']}/M output (approx, user-editable)")


@mcp.tool()
def get_org_usage(days: int = 1) -> str:
    """Organization/account-level usage from the provider Admin API (requires admin key in env)."""
    t = get_tracker()
    provider = get_provider(t.config.provider)
    return _wrap(json.dumps(provider.get_org_usage(days), indent=2))


@mcp.prompt()
def awareness_briefing() -> str:
    """Baseline operational awareness briefing to inject at conversation start."""
    t = get_tracker()
    spec = t.model_spec
    return (f"{t.header()}\n{capabilities_line(spec)}\n"
            "Operational protocol: after each API exchange call record_usage with the usage numbers; "
            "use update_task to track multi-step work; if an alert says context is low, wrap up and call create_handoff; "
            "at the start of a new session call resume_session to recover prior state.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
