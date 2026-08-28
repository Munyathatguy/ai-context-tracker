# PRD — ai-context-tracker

## Original Problem Statement
A free, open-source MCP (Model Context Protocol) server that injects real-time operational awareness into any compatible AI client — token budgets, time awareness, context health, session continuity, and crash recovery. Targets developers using Claude Code, OpenAI Agents SDK, terminal tools. P0–P7 features, 3 providers (OpenAI/Anthropic/Google), Python 3.11+, stdio transport, local JSON state, YAML config, no cloud dependency.

## User Choices
- Deliverable structure: agent's choice → Python package (core) + companion web dashboard (visualization)
- CLI dashboard: YES (htop-style, included in v1)
- Handoffs: BOTH auto (at danger threshold) + manual tool
- Name: ai-context-tracker
- Scope: Full Phases 1–5

## Architecture
- **Core package** `/app/ai-context-tracker/` — pip-installable (`pip install -e .`), entry point `ai-context-tracker` CLI
  - `tracker.py` ContextTracker engine (usage, cost, alerts, handoffs, model switch, tasks)
  - `server.py` FastMCP stdio server: 8 tools + `awareness_briefing` prompt; every response has `[AWARENESS]` header
  - `providers/` OpenAI/Anthropic/Google adapters (native count_tokens endpoints, admin usage APIs, duck-typed usage extraction) via httpx; keys env-only
  - `state.py` atomic JSON persistence in `~/.ai-context-tracker` (override `ACT_STATE_DIR`); `models.py` registry (context windows, pricing, capabilities, fuzzy resolve); `alerts.py` warn/danger/red; `dashboard.py` rich live CLI; `cli.py` serve/dashboard/sessions/init
  - `tests/` 24 pytest unit tests (all passing)
- **Companion web dashboard**: FastAPI (`/api/tracker/sessions`, `/api/tracker/sessions/{id}` reading ACT_STATE_DIR) + React dark "command center" UI (Chivo/JetBrains Mono, recharts gauge, phosphor icons)
- Demo seeder: `/app/scripts/seed_demo.py` (2 sessions, alerts, tasks, handoff)
- Pinned `mcp<2` (FastMCP v1 API); starlette pinned for fastapi compat

## Implemented (2026-06)
- P0 token tracking + configurable thresholds + dual alerting + red-alert wrap-up
- P1 time awareness header; P2 count_tokens pre-check + danger advice + create_handoff (JSON+MD)
- P3 persistence after every exchange + resume_session; P4 model registry/switch briefing/get_model_info
- P5 update_task checklist; P6 cost tracking (editable pricing); P7 turn counter
- CLI dashboard, README, MIT license, .mcp.json template, config.example.yaml
- Web dashboard verified end-to-end (testing agent iteration_1: 100% backend, 100% frontend)

## Backlog / Next
- P1: PyPI publish workflow (GitHub Action), demo GIF, CONTRIBUTING.md
- P2: streamable HTTP transport, rate-limit header surfacing tool, auto-resume prompt on server restart detection
- P2: web dashboard SSE live push instead of polling
