"""Seed realistic demo sessions by driving the real tracker end-to-end."""
import os
import sys

sys.path.insert(0, "/app/ai-context-tracker")
os.environ.setdefault("ACT_STATE_DIR", "/root/.ai-context-tracker")

from ai_context_tracker.config import Config
from ai_context_tracker.tracker import ContextTracker

state_dir = os.environ["ACT_STATE_DIR"]

# Session 1: active Claude session deep into its context window (warn alert fired)
t = ContextTracker(Config(state_dir=state_dir, model="claude-sonnet-4-5", provider="anthropic",
                          timezone="America/New_York"))
t.update_task("Design MCP server architecture", "done")
t.update_task("Implement provider adapters (OpenAI/Anthropic/Google)", "done")
t.update_task("Build token alert engine with thresholds", "in_progress")
t.update_task("Write README + PyPI packaging", "todo")
turns = [
    (4200, 1800, 0, 0, "Reviewed repo structure and planned the adapter interfaces"),
    (9800, 3400, 1200, 0, "Implemented OpenAI provider with count_tokens endpoint"),
    (15600, 5200, 3800, 0, "Implemented Anthropic + Google adapters, unit tests passing"),
    (22400, 7800, 6200, 0, "Built alert engine; wired warn/danger/red levels"),
    (31000, 9600, 9400, 0, "Refactored state persistence to atomic JSON writes"),
    (38500, 11200, 12800, 0, "Debugging threshold edge case at exactly 30% remaining"),
]
for inp, out, cached, reasoning, summary in turns:
    t.record_usage(inp, out, cached, reasoning, model="claude-sonnet-4-5", summary=summary)
t.create_handoff(
    goals="Ship v0.1 of ai-context-tracker with all P0-P7 features",
    progress="Provider adapters and alert engine complete; state persistence hardened",
    remaining="Finish threshold edge case; README; PyPI publish",
    decisions="stdio transport for v1; JSON state files over SQLite; env-only API keys")

# Session 2: earlier GPT session (finished, light usage)
t2 = ContextTracker(Config(state_dir=state_dir, model="gpt-5.1", provider="openai"))
t2.update_task("Prototype awareness header format", "done")
t2.record_usage(2800, 1200, 0, 450, model="gpt-5.1", summary="Prototyped [AWARENESS] header format")
t2.record_usage(5200, 2400, 800, 900, model="gpt-5.1", summary="Validated header against Claude Code output")

# Session 1 is latest
t.record_usage(6200, 2100, 4100, 0, model="claude-sonnet-4-5",
               summary="Fixed edge case; alerts now fire exactly once per threshold")
print("seeded:", t.state.session_id, t2.state.session_id, "-> pct used:", round(t.pct_used(), 1))
