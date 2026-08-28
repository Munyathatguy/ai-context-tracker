import pytest

import ai_context_tracker.server as srv
from ai_context_tracker.config import Config
from ai_context_tracker.integrations import parse_rate_limit_headers
from ai_context_tracker.tracker import ContextTracker


def test_rate_limit_stored_and_header(tmp_path):
    t = ContextTracker(Config(state_dir=tmp_path, model="claude-sonnet-4-5"))
    r = t.record_usage(100, 50, rl_remaining_tokens=48_000, rl_limit_tokens=80_000)
    assert t.state.rate_limits["pct_remaining"] == 60.0
    assert r["alerts"] == []
    assert "RL headroom: 60.0%" in t.header()


def test_rate_limit_alert_fires_once_below_10pct(tmp_path):
    t = ContextTracker(Config(state_dir=tmp_path, model="claude-sonnet-4-5"))
    r = t.record_usage(100, 50, rl_remaining_tokens=5_000, rl_limit_tokens=80_000)
    assert any(a["threshold"] == "rate_limit" and "429" in a["message"] for a in r["alerts"])
    r = t.record_usage(100, 50, rl_remaining_tokens=4_000, rl_limit_tokens=80_000)
    assert not any(a["threshold"] == "rate_limit" for a in r["alerts"])


def test_parse_rate_limit_headers():
    rem, lim = parse_rate_limit_headers({"x-ratelimit-remaining-tokens": "1500", "x-ratelimit-limit-tokens": "80000"})
    assert (rem, lim) == (1500, 80000)
    rem, lim = parse_rate_limit_headers({"Anthropic-Ratelimit-Input-Tokens-Remaining": "900",
                                         "Anthropic-Ratelimit-Input-Tokens-Limit": "40000"})
    assert (rem, lim) == (900, 40000)
    assert parse_rate_limit_headers(None) == (None, None)
    assert parse_rate_limit_headers({"x-ratelimit-remaining-tokens": "junk"}) == (None, None)


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ACT_STATE_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    srv._tracker = None
    yield tmp_path
    srv._tracker = None


def test_resume_offer_on_restart(isolated_env):
    prior = ContextTracker(Config(state_dir=isolated_env, model="claude-sonnet-4-5"))
    prior.update_task("half-finished work", "in_progress")
    prior.record_usage(5000, 2000, summary="was mid-refactor when crash happened")
    sid = prior.state.session_id
    srv._tracker = None  # simulate MCP server restart
    out = srv.get_status()
    assert "Previous session detected" in out and sid in out
    out2 = srv.get_status()
    assert "Previous session detected" not in out2  # offered once


def test_resume_offer_cleared_by_resume(isolated_env):
    prior = ContextTracker(Config(state_dir=isolated_env, model="gpt-5.1"))
    prior.record_usage(1000, 500, summary="prior work")
    srv._tracker = None
    out = srv.resume_session()
    assert "RESUMED session" in out and "Previous session detected" not in out


def test_record_usage_tool_accepts_rate_limits(isolated_env):
    srv.record_usage(100, 50, rate_limit_remaining_tokens=20_000, rate_limit_limit_tokens=80_000)
    assert srv.get_tracker().state.rate_limits["pct_remaining"] == 25.0
    assert "RL headroom: 25.0%" in srv.get_status()
