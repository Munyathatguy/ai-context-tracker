import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_FEATURES = {
    "token_tracking": True,
    "time_awareness": True,
    "context_health": True,
    "session_continuity": True,
    "model_awareness": True,
    "task_tracking": True,
    "cost_tracking": True,
    "turn_counter": True,
}


@dataclass
class Config:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5"
    timezone: str = "UTC"
    alert_thresholds: list = field(default_factory=lambda: [30, 20, 10])
    red_alert_threshold: int = 10
    danger_threshold: int = 15
    auto_handoff: bool = True
    features: dict = field(default_factory=lambda: dict(DEFAULT_FEATURES))
    state_dir: Path = field(default_factory=lambda: Path(os.environ.get("ACT_STATE_DIR", str(Path.home() / ".ai-context-tracker"))))
    pricing_overrides: dict = field(default_factory=dict)
    model_overrides: dict = field(default_factory=dict)

    def __post_init__(self):
        self.state_dir = Path(self.state_dir)
        self.alert_thresholds = sorted({int(t) for t in self.alert_thresholds}, reverse=True)
        if self.alert_thresholds:
            self.red_alert_threshold = min(self.red_alert_threshold, self.alert_thresholds[-1])


def _search_paths():
    env = os.environ.get("ACT_CONFIG")
    paths = [Path(env)] if env else []
    paths += [Path.cwd() / "config.yaml", Path.home() / ".ai-context-tracker" / "config.yaml"]
    return paths


def load_config(path: str | None = None) -> Config:
    candidates = [Path(path)] if path else _search_paths()
    data = {}
    for p in candidates:
        if p.is_file():
            data = yaml.safe_load(p.read_text()) or {}
            break
    known = {f for f in Config.__dataclass_fields__}
    kwargs = {k: v for k, v in data.items() if k in known}
    if "features" in kwargs:
        merged = dict(DEFAULT_FEATURES)
        merged.update(kwargs["features"] or {})
        kwargs["features"] = merged
    return Config(**kwargs)
