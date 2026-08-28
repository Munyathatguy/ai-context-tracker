# Contributing to ai-context-tracker

Thanks for helping make AI sessions self-aware! All contributions are welcome — bug reports, provider adapters, docs, tests.

## Development setup

```bash
git clone https://github.com/you/ai-context-tracker
cd ai-context-tracker
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Guidelines

- **Tests required**: every feature or fix ships with a pytest case. Provider calls must be mocked (`monkeypatch` on `httpx`) — CI has no API keys.
- **No new heavy dependencies**: the runtime deps are `mcp`, `pyyaml`, `httpx`, `rich`. Keep it that way.
- **Security invariants** (non-negotiable):
  - API keys are read only from environment variables, never written to config or state files.
  - State files contain session metadata only — never full message content.
  - No network calls except to the configured provider APIs. No telemetry.
- **Style**: standard library first, small functions, minimal comments. Match the existing code.

## Adding a provider

1. Create `ai_context_tracker/providers/<name>_provider.py` subclassing `ProviderAdapter` (`count_tokens`, `get_org_usage`).
2. Register it in `providers/__init__.py` `PROVIDERS`.
3. Extend `extract_usage` in `providers/base.py` if the usage payload shape differs.
4. Add model specs to `models.py` `MODEL_REGISTRY` and mocked tests in `tests/test_providers.py`.

## Pull requests

- One focused change per PR, with a clear description of the behavior before/after.
- CI (pytest on Python 3.11 and 3.12) must pass.

## Releases (maintainers)

1. Bump `version` in `pyproject.toml` and `__version__` in `ai_context_tracker/__init__.py`.
2. Tag and publish a GitHub Release — the `publish.yml` workflow builds and uploads to PyPI via Trusted Publishing (configure the `pypi` environment + trusted publisher on pypi.org once).
