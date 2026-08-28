# Roadmap — ai-context-tracker

Everything shipped so far, plus every feature we're considering. Contributions welcome — pick anything below and open a PR (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## ✅ Shipped (v0.1.0)

- P0–P7 core: token tracking, configurable multi-level alerts (warn/danger/red), time awareness, context health + exact `count_tokens`, session persistence & `resume_session`, model registry/switch briefing, `update_task` checklist, cost tracking, turn counter
- 8 MCP tools + `awareness_briefing` prompt, `[AWARENESS]` header on every response
- Auto + manual handoffs (JSON + markdown on disk)
- Auto resume offer when the MCP server restarts after a crash
- Rate-limit headroom tracking (from response headers) with <10% alert
- htop-style CLI dashboard (`ai-context-tracker dashboard`), `sessions`, `init` commands
- Companion web dashboard: SSE live stream, context gauge, token breakdown, burn-rate chart, handoff reader, session compare, threshold/config editor, org-usage panel, sound alerts, archive/delete cleanup
- CI (pytest 3.11/3.12) + PyPI Trusted Publishing workflows

## 🔜 Near-term (v0.2)

- **Archive browser & restore** — list archived sessions in dashboard/CLI with one-click restore (`POST /sessions/{id}/restore`)
- **Handoff export** — copy-to-clipboard / download handoff as markdown to paste into a fresh chat
- **Local tokenizer fallback** — offline counting via `tiktoken` when no API key is available (today: chars/4 estimate)
- **Budget caps** — per-session and per-day USD limits with a hard-stop red alert ("you've spent $X of your $Y budget")
- **Weekly digest** — aggregate tokens/cost across all sessions (day/week/month) in dashboard + CLI
- **Auto-resume injection** — optionally inject the last handoff into the awareness briefing automatically on new sessions (today: offer only)
- **Live demo mode** — dashboard button simulating an active session so alerts can be previewed without an AI client
- **Un-archive / retention policy** — auto-purge sessions older than N days (configurable)

## 🧭 Mid-term (v0.3+)

- **Streamable HTTP transport** — remote/shared hosting of the MCP server; multiple clients sharing one tracker
- **Provider expansion** — Azure OpenAI, AWS Bedrock, Mistral, DeepSeek, xAI Grok, OpenRouter, Ollama/local models
- **Notifications** — Slack / Discord / desktop notifications when danger or red alerts fire
- **Context compaction assistant** — detect bloated context, suggest which earlier turns to summarize or drop
- **Prompt-cache advisor** — spot repeated prefixes and recommend provider prompt caching (with estimated savings)
- **Rate-limit pacing advice** — compute a safe requests/min pace from remaining headroom and inject it
- **Usage export** — CSV/JSON export of per-turn history and session summaries
- **Pricing auto-update** — pull the per-model pricing table from a community-maintained registry (opt-in, still overridable)
- **MCP resources** — expose session state and handoffs as MCP resources, not just tools
- **Project grouping** — tag sessions by project/repo; per-project burn and budget views

## 🌌 Long-term ideas

- **Team mode** — org-wide usage dashboards built on provider Admin APIs; per-developer breakdowns
- **VS Code companion** — status-bar widget with live context % and cost for the active session
- **Grafana/Prometheus exporter** — scrapeable metrics endpoint for observability stacks
- **Benchmark mode** — run the same task across models and compare tokens/cost/quality side by side
- **Encrypted state** — optional at-rest encryption of session files
- **Plugin system** — custom alert channels and custom awareness header sections
- **TUI upgrades** — sparklines, multi-session view, keybindings, mouse support
- **Docker image / pipx & uvx one-liners** — zero-install ways to run the server
- **i18n** — localized dashboard and alert messages

## Non-goals

- No cloud service, no accounts, no telemetry — this stays a local-first, auditable tool
- No storing of message content — session metadata only, ever
