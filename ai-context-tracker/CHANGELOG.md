# Changelog

All notable changes to ai-context-tracker.

## [0.1.0] — 2026-06

Initial release.

### MCP server (stdio)
- 8 tools: `get_status`, `record_usage`, `count_tokens`, `create_handoff`, `resume_session`, `update_task`, `get_model_info`, `get_org_usage`
- `awareness_briefing` prompt for baseline context injection
- `[AWARENESS]` header on every tool response: local time, session start, message gap, turn, tokens vs context window, cost, rate-limit headroom

### Token & alerting (P0)
- Cumulative session tracking (input/output/cached/reasoning) vs model context window
- Fully configurable alert thresholds (any count/levels), each fires exactly once
- Red alert instructs the AI to stop expanding and wrap up
- Dual alerting: AI context + user-facing output

### Time awareness (P1) / Context health (P2)
- Timestamp, session start, elapsed and message-gap injection (user timezone)
- Exact pre-request counting via provider endpoints (OpenAI `input_tokens`, Anthropic `count_tokens`, Google `countTokens`) with chars/4 fallback
- Danger-zone advice + auto handoff at configurable threshold

### Continuity (P3)
- Atomic JSON state after every exchange; last-3 message summaries
- `create_handoff` (manual + auto) saved as JSON and markdown
- `resume_session` restores tasks/summaries/usage/handoffs
- Auto resume offer injected once when the server restarts over a prior session

### Model awareness (P4) / Tasks (P5) / Cost (P6) / Turns (P7)
- Model registry (context window, max output, capabilities, pricing) with fuzzy id resolution and user overrides
- Mid-session model-switch detection with briefing for the new model
- Persistent task checklist; per-model USD cost; turn counter
- Per-turn burn history (`turn_history`, capped at 500 entries)

### Rate limits
- Headroom captured from response headers (OpenAI `x-ratelimit-*`, Anthropic `anthropic-ratelimit-*`) or passed explicitly; alert at ≤10%

### Providers
- OpenAI, Anthropic, Google Gemini adapters (count tokens, org usage via Admin APIs, duck-typed usage extraction from SDK/dict responses)

### Tooling
- CLI: `serve`, `dashboard` (live htop-style view), `sessions`, `init`
- SDK-side capture: `integrations.track_response(response, tracker, headers=...)`
- Companion web dashboard (React + FastAPI, in repo root): SSE live stream, context gauge, token breakdown, burn-rate chart, alerts + rate-limit bar, handoff reader dialog, session compare, config/threshold editor, org-usage panel, sound alerts, session archive/delete
- CI workflow (pytest on 3.11/3.12) and PyPI Trusted Publishing workflow
- 31 unit tests, all provider HTTP mocked

### Security
- API keys from environment variables only; state files contain metadata, never message content; no telemetry
