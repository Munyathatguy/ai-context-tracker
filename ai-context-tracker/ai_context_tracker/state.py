import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    model: str = ""
    provider: str = ""
    started_at: str = field(default_factory=utcnow)
    last_message_at: str = field(default_factory=utcnow)
    turn: int = 0
    usage: dict = field(default_factory=lambda: {"input": 0, "output": 0, "cached": 0, "reasoning": 0, "total": 0})
    cost_usd: float = 0.0
    tasks: list = field(default_factory=list)
    turn_history: list = field(default_factory=list)
    message_summaries: list = field(default_factory=list)
    handoffs: list = field(default_factory=list)
    alerts_fired: list = field(default_factory=list)
    active_alerts: list = field(default_factory=list)
    model_history: list = field(default_factory=list)
    rate_limits: dict = field(default_factory=dict)
    org_usage: dict = field(default_factory=dict)

    # -- persistence ----------------------------------------------------
    @staticmethod
    def sessions_dir(state_dir: Path) -> Path:
        d = Path(state_dir) / "sessions"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, state_dir: Path):
        d = self.sessions_dir(state_dir)
        path = d / f"{self.session_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2))
        tmp.replace(path)
        (Path(state_dir) / "latest.json").write_text(json.dumps({"session_id": self.session_id, "updated_at": utcnow()}))

    @classmethod
    def load(cls, state_dir: Path, session_id: str) -> "SessionState | None":
        path = cls.sessions_dir(state_dir) / f"{session_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text())
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})

    @classmethod
    def load_latest(cls, state_dir: Path) -> "SessionState | None":
        ptr = Path(state_dir) / "latest.json"
        if ptr.is_file():
            sid = json.loads(ptr.read_text()).get("session_id")
            if sid:
                return cls.load(state_dir, sid)
        sessions = cls.list_sessions(state_dir)
        return cls.load(state_dir, sessions[0]["session_id"]) if sessions else None

    @classmethod
    def list_sessions(cls, state_dir: Path) -> list[dict]:
        out = []
        for p in cls.sessions_dir(state_dir).glob("*.json"):
            try:
                data = json.loads(p.read_text())
                out.append({
                    "session_id": data.get("session_id", p.stem),
                    "model": data.get("model", ""),
                    "started_at": data.get("started_at", ""),
                    "last_message_at": data.get("last_message_at", ""),
                    "turn": data.get("turn", 0),
                    "total_tokens": data.get("usage", {}).get("total", 0),
                    "cost_usd": data.get("cost_usd", 0.0),
                })
            except (json.JSONDecodeError, OSError):
                continue
        out.sort(key=lambda s: s.get("last_message_at", ""), reverse=True)
        return out

    def add_summary(self, text: str):
        if text:
            self.message_summaries = (self.message_summaries + [{"at": utcnow(), "text": text}])[-3:]
