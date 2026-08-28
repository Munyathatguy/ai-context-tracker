import pytest

import ai_context_tracker.server as srv
from ai_context_tracker.config import Config
from ai_context_tracker.tracker import ContextTracker


@pytest.fixture(autouse=True)
def fresh_tracker(tmp_path):
    srv._tracker = ContextTracker(Config(state_dir=tmp_path, model="claude-sonnet-4-5"))
    yield
    srv._tracker = None


def test_get_status_has_awareness_header():
    out = srv.get_status()
    assert out.startswith("[AWARENESS]")
    assert "Current time:" in out and "Turn 0" in out and "Cost: $" in out


def test_record_usage_tool_and_alerts():
    out = srv.record_usage(150_000, 0)
    assert "75.0% of context window used" in out
    assert "WARNING" in out  # 25% remaining crosses 30 threshold


def test_red_alert_wrap_up_instruction():
    out = srv.record_usage(185_000, 0)
    assert "RED ALERT" in out and "wrapping up" in out.lower() or "STOP" in out


def test_count_tokens_tool():
    out = srv.count_tokens("hello world " * 100)
    assert "count:" in out and "context would be" in out


def test_task_and_handoff_and_resume():
    srv.update_task("build feature", "in_progress")
    out = srv.update_task("build feature", "done")
    assert "(1/1 done)" in out
    srv.create_handoff("ship v1", "core done", "docs remaining", "used stdio transport")
    srv.record_usage(100, 50, summary="finished feature")
    sid = srv.get_tracker().state.session_id
    srv._tracker = ContextTracker(Config(state_dir=srv.get_tracker().config.state_dir))
    out = srv.resume_session()
    assert sid in out and "build feature" in out and "ship v1" in out


def test_model_info_tool():
    out = srv.get_model_info("gpt-5.1")
    assert "400,000 context" in out and "Pricing" in out


def test_awareness_briefing_prompt():
    out = srv.awareness_briefing()
    assert "record_usage" in out and "resume_session" in out
