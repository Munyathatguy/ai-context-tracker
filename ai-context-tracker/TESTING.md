# Testing Guide — ai-context-tracker

How to verify every feature yourself, from unit tests to a full end-to-end run with a real AI client.

## 0. Prerequisites

```bash
cd ai-context-tracker
python -m venv .venv && source .venv/bin/activate   # Python 3.11+
pip install -e ".[dev]"
```

No API keys are required for anything except exact token counting and org usage (section 6).

## 1. Unit tests (31 tests, ~1s)

```bash
pytest -q
```

Covers: alert engine, cost math, persistence/resume, model switch briefing, turn history, rate-limit alerts, resume offer, provider usage extraction (mocked HTTP), and all MCP tool functions.

## 2. Poke the MCP server directly (no AI client needed)

The tools are plain Python functions — you can drive a full session from the REPL:

```bash
python
```
```python
import os; os.environ["ACT_STATE_DIR"] = "/tmp/act-test"
import ai_context_tracker.server as srv

print(srv.get_status())                        # [AWARENESS] header + JSON status
print(srv.update_task("write report", "in_progress"))
print(srv.record_usage(50_000, 8_000, summary="drafted section 1"))
print(srv.record_usage(90_000, 12_000))        # crosses 30% & 20% thresholds -> WARNING/DANGER
print(srv.record_usage(30_000, 5_000))         # red zone -> RED ALERT + auto handoff
print(srv.count_tokens("hello " * 200))
print(srv.create_handoff("finish report", "sections 1-2 done", "section 3", "kept it short"))
print(srv.get_model_info("gpt-5.1"))
```

Now simulate a crash + new session:

```python
import ai_context_tracker.server as srv2
srv2._tracker = None
print(srv2.get_status())      # -> "💾 Previous session detected ... call resume_session"
print(srv2.resume_session())  # -> restored tasks, summaries, handoff
```

## 3. MCP Inspector (interactive tool UI)

```bash
npx @modelcontextprotocol/inspector ai-context-tracker serve
```

Open the printed URL, hit **Connect**, and call the 8 tools from the Tools tab. Also check the **Prompts** tab for `awareness_briefing`.

## 4. Real client: Claude Code

```bash
claude mcp add context-tracker -- ai-context-tracker serve
claude
```

Then in the conversation: *"Call get_status"*, *"Record usage of 120000 input and 15000 output tokens"*, *"Create a handoff for what we did"*. Every tool response should start with the `[AWARENESS]` line. For any other MCP client, drop `examples/mcp.json` into your project root.

## 5. CLI dashboard (htop mode)

Terminal 1:
```bash
ai-context-tracker dashboard
```
Terminal 2 — feed it data and watch the bar/tables move live:
```bash
python - <<'EOF'
from ai_context_tracker import ContextTracker
t = ContextTracker(); t.resume()
t.record_usage(20_000, 4_000, summary="dashboard smoke test",
               rl_remaining_tokens=60_000, rl_limit_tokens=80_000)
EOF
```
Also try: `ai-context-tracker sessions` and `ai-context-tracker init`.

## 6. Exact counting & org usage (needs your keys)

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # exact count_tokens
export OPENAI_ADMIN_KEY=sk-admin-...    # org usage report
python -c "from ai_context_tracker.providers import AnthropicProvider as P; print(P().count_tokens('claude-sonnet-4-5','hello world'))"
python -c "from ai_context_tracker.providers import OpenAIProvider as P; print(P().get_org_usage(7))"
```

Without keys you get a chars/4 estimate and a clear "admin key not set" message — that's expected, not a bug.

## 7. Web dashboard checklist (companion app)

Seed demo data (`python scripts/seed_demo.py` from the repo root), start backend + frontend, then verify. Re-run the seed script any time to reset the demo state (delete `~/.ai-context-tracker` first for a clean slate).

| # | Check | Expect |
|---|-------|--------|
| 1 | Sidebar | 3 sessions, LIVE badge on latest |
| 2 | Context gauge | 84.4% used, yellow |
| 3 | Token breakdown | input/output/cached/reasoning bars + total 168,800 |
| 4 | Alerts panel | WARN + DANGER cards, rate-limit headroom bar 28.1% |
| 5 | Burn Rate chart | 7-point dual line (tokens + cost); gemini session shows "not enough turns" |
| 6 | Handoff card click | full-detail dialog (goals/progress/remaining/decisions) |
| 7 | Gear icon | edit thresholds to `35, 15`, save, reopen — persisted to config.yaml |
| 8 | Compare icon | claude vs gpt-5.1 side by side, green = cheaper |
| 9 | Speaker icon | mute toggles and survives reload |
| 10 | Hover a session | archive + trash icons; trash needs a second confirming click |
| 11 | Live stream | run the snippet from section 5 — dashboard updates within ~1s, no refresh |
| 12 | Org usage panel | fetch shows admin-key hint (or real numbers with keys set) |

## 8. What "correct" alert behavior looks like

- Each threshold (default 30/20/10% remaining) fires **exactly once** per session
- Red alert (≤10%) tells the AI to **stop expanding and wrap up**
- At the danger threshold (≤15%) a handoff is **auto-saved** once (if `auto_handoff: true`)
- Rate-limit alert fires once when headroom ≤10%

## Found a bug?

Open an issue with the failing step number from this guide plus your `config.yaml` (never include API keys).
