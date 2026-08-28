# ai-context-tracker (monorepo)

Real-time operational awareness for AI sessions — token budgets, time awareness, context health, crash recovery — delivered as an MCP server, plus a live companion web dashboard.

## Repo layout

| Path | What it is |
|------|------------|
| [`ai-context-tracker/`](ai-context-tracker/) | **The product**: pip-installable Python MCP server + CLI dashboard. Start with its [README](ai-context-tracker/README.md). |
| `backend/` | FastAPI companion API — reads local session state, serves REST + SSE live stream for the web dashboard |
| `frontend/` | React web dashboard — context gauge, burn-rate chart, alerts, handoff reader, session compare, config editor |
| `scripts/seed_demo.py` | Seeds realistic demo sessions so the dashboards have data |
| `tests/` | Platform test artifacts |

## Documentation

- [Package README](ai-context-tracker/README.md) — install, client setup (Claude Code / OpenAI SDK / `.mcp.json`), tools reference
- [TESTING.md](ai-context-tracker/TESTING.md) — step-by-step guide to verify every feature yourself
- [ROADMAP.md](ai-context-tracker/ROADMAP.md) — shipped features + everything planned
- [CHANGELOG.md](ai-context-tracker/CHANGELOG.md) — release notes
- [CONTRIBUTING.md](ai-context-tracker/CONTRIBUTING.md) — dev setup, guidelines, release process

## Quick start (package only)

```bash
cd ai-context-tracker
pip install -e ".[dev]"
pytest                       # 31 tests
ai-context-tracker init      # starter config.yaml
ai-context-tracker serve     # MCP server over stdio
ai-context-tracker dashboard # live CLI view
```

## Quick start (web dashboard)

Backend expects `MONGO_URL`, `DB_NAME`, `ACT_STATE_DIR` env vars; frontend expects `REACT_APP_BACKEND_URL`.

```bash
python scripts/seed_demo.py            # demo data
cd backend && pip install -r requirements.txt && uvicorn server:app --port 8001
cd frontend && yarn && yarn start
```

## CI / Publishing

GitHub Actions inside `ai-context-tracker/.github/workflows/` run tests on push and publish to PyPI on GitHub Releases (one-time [Trusted Publisher](https://docs.pypi.org/trusted-publishers/) setup on pypi.org, workflow `publish.yml`). Note: for the workflows to trigger, they must live at the **repository root** `.github/workflows/` — if you publish the package folder as its own repo they're already in place; if you keep this monorepo, copy them to the repo root.

MIT licensed.
