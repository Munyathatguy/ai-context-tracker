# ai-context-tracker

**Real-time operational awareness for any MCP-compatible AI client.** Token budgets, time awareness, context health, session continuity, crash recovery, model awareness, task tracking, cost tracking — injected straight into your AI's context.

Runs entirely on your machine. No backend, no database, no telemetry.

## Why

AI models are flying blind: they don't know what time it is, how full their context window is, how much the session costs, or what they were doing before a crash. This MCP server gives them (and you) ground truth.

## Install

```bash
pip install ai-context-tracker        # from PyPI (planned)
# or from source:
git clone https://github.com/you/ai-context-tracker && cd ai-context-tracker
pip install -e .
```

## Setup

1. **API keys** — environment variables only, never stored in files:
   - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` (standard keys: exact token counting)
   - `OPENAI_ADMIN_KEY`, `ANTHROPIC_ADMIN_KEY` (optional: org-level usage reports)
2. **Config** — `ai-context-tracker init` writes a starter `config.yaml` (provider, timezone, alert thresholds, feature toggles).
3. **Add to your client:**

Claude Code:
```bash
claude mcp add context-tracker -- ai-context-tracker serve
```

Any client via `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "context-tracker": {
      "command": "ai-context-tracker",
      "args": ["serve"]
    }
  }
}
```

OpenAI Agents SDK (Python):
```python
from agents.mcp import MCPServerStdio
server = MCPServerStdio(params={"command": "ai-context-tracker", "args": ["serve"]})
```

## Tools exposed to the AI

| Tool | Purpose |
|------|---------|
| `get_status` | token usage, % context remaining, time, cost, tasks, alerts |
| `record_usage` | log per-exchange token usage (input/output/cached/reasoning) |
| `count_tokens` | exact pre-request count via provider native endpoints |
| `create_handoff` | structured session summary saved as JSON + markdown |
| `resume_session` | reload last saved session after crash/disconnect |
| `update_task` | persistent multi-step task checklist |
| `get_model_info` | model self-awareness: context window, limits, capabilities |
| `get_org_usage` | org-level usage via provider Admin APIs |

Every tool response is prefixed with an awareness header:

```
[AWARENESS] Current time: 2026-06-14 3:42 PM EST | Session started: 2:15 PM | Last message: 12 min ago | Turn 47 | Tokens: 128,450/200,000 (64.2% used, 35.8% left) | Cost: $1.8420
```

Alerts fire at your configured thresholds (default 30/20/10% remaining) — both to the user and into the AI's context. At the red threshold the AI is instructed to stop expanding and wrap up. At the danger threshold a handoff summary is auto-saved (configurable).

## CLI dashboard

htop for your AI session:

```bash
ai-context-tracker dashboard    # live view: context bar, token breakdown, tasks, alerts, cost
ai-context-tracker sessions     # list saved sessions
```

## SDK-side usage capture (optional)

MCP servers can't intercept your client's HTTP traffic, so usage is captured either by the AI calling `record_usage` each turn (the awareness briefing instructs it to), or directly in your own scripts:

```python
from ai_context_tracker import ContextTracker
from ai_context_tracker.integrations import track_response

tracker = ContextTracker()
resp = client.messages.create(...)          # any OpenAI / Anthropic / Google response
track_response(resp, tracker, summary="answered the user's question")
```

Both paths write to the same local state file, so the MCP tools and the CLI dashboard always agree.

## State & security

- State lives in `~/.ai-context-tracker/` (override with `ACT_STATE_DIR`): session JSON + handoff JSON/markdown.
- State files contain metadata only — never full message content.
- No network calls except to the configured provider APIs. No telemetry.

## Provider support

| Provider | Per-request tokens | Org usage API | Exact count endpoint |
|----------|-------------------|---------------|----------------------|
| OpenAI | ✅ response usage | ✅ `/v1/organization/usage/completions` | ✅ `/v1/responses/input_tokens` |
| Anthropic | ✅ response usage | ✅ usage report API | ✅ `/v1/messages/count_tokens` |
| Google Gemini | ✅ `usage_metadata` | AI Studio / BigQuery | ✅ `countTokens` |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Documentation

- [TESTING.md](TESTING.md) — verify every feature yourself, step by step
- [ROADMAP.md](ROADMAP.md) — shipped + planned features
- [CHANGELOG.md](CHANGELOG.md) — release notes
- [CONTRIBUTING.md](CONTRIBUTING.md) — dev setup and guidelines

MIT licensed. Contributions welcome.
