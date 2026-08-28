from ai_context_tracker.alerts import evaluate
from ai_context_tracker.config import Config
from ai_context_tracker.models import resolve_model, capabilities_line
from ai_context_tracker.state import SessionState
from ai_context_tracker.tracker import ContextTracker


def make_tracker(tmp_path, **cfg):
    config = Config(state_dir=tmp_path, model=cfg.pop("model", "claude-sonnet-4-5"), **cfg)
    return ContextTracker(config)


def test_resolve_model_exact_and_fuzzy():
    assert resolve_model("gpt-5.1")["context_window"] == 400_000
    assert resolve_model("claude-sonnet-4-5-20250929")["id"] == "claude-sonnet-4-5"
    assert resolve_model("models/gemini-2.5-pro-latest")["provider"] == "google"
    assert resolve_model("totally-unknown")["context_window"] == 128_000


def test_capabilities_line():
    line = capabilities_line(resolve_model("claude-sonnet-5"))
    assert "200,000 context" in line and "CANNOT" in line


def test_alerts_fire_once_and_red():
    alerts = evaluate(25.0, [30, 20, 10], 10, [])
    assert [a["threshold"] for a in alerts] == [30]
    alerts = evaluate(8.0, [30, 20, 10], 10, [30])
    assert [a["threshold"] for a in alerts] == [20, 10]
    assert alerts[-1]["level"] == "red" and "STOP" in alerts[-1]["message"]


def test_record_usage_accumulates_and_costs(tmp_path):
    t = make_tracker(tmp_path)
    t.record_usage(1000, 500, cached_tokens=100, reasoning_tokens=50)
    t.record_usage(2000, 1000)
    assert t.state.usage["total"] == 1000 + 500 + 50 + 2000 + 1000
    assert t.state.turn == 2
    expected = (3000 * 3.0 + 1500 * 15.0) / 1_000_000
    assert abs(t.state.cost_usd - expected) < 1e-9


def test_threshold_alert_and_auto_handoff(tmp_path):
    t = make_tracker(tmp_path, alert_thresholds=[30, 20, 10], danger_threshold=15)
    r = t.record_usage(150_000, 0)  # 75% used -> 25% remaining -> warn at 30
    assert [a["threshold"] for a in r["alerts"]] == [30]
    r = t.record_usage(25_000, 15_000)  # 95% used -> 5% left -> 20 & 10 fire, auto handoff
    assert {a["threshold"] for a in r["alerts"]} == {20, 10}
    assert r["auto_handoff"] is not None
    assert any(h["auto"] for h in t.state.handoffs)
    r = t.record_usage(10, 10)  # no repeat alerts
    assert r["alerts"] == []


def test_persistence_and_resume(tmp_path):
    t = make_tracker(tmp_path)
    t.update_task("write tests", "in_progress")
    t.record_usage(100, 50, summary="wrote first test")
    sid = t.state.session_id
    t2 = ContextTracker(Config(state_dir=tmp_path))
    st = t2.resume()
    assert st.session_id == sid
    assert st.tasks[0]["title"] == "write tests"
    assert st.message_summaries[-1]["text"] == "wrote first test"


def test_model_switch_brief(tmp_path):
    t = make_tracker(tmp_path, model="claude-sonnet-4-5")
    t.record_usage(100, 50, model="claude-sonnet-4-5")
    r = t.record_usage(100, 50, model="gpt-5.1")
    assert r["model_switch_brief"] and "gpt-5.1" in r["model_switch_brief"]
    assert t.model_spec["context_window"] == 400_000


def test_summaries_keep_last_three(tmp_path):
    t = make_tracker(tmp_path)
    for i in range(5):
        t.record_usage(10, 10, summary=f"turn {i}")
    assert [s["text"] for s in t.state.message_summaries] == ["turn 2", "turn 3", "turn 4"]


def test_turn_history_tracks_burn(tmp_path):
    t = make_tracker(tmp_path)
    t.record_usage(100, 50)
    t.record_usage(200, 100)
    assert [h["turn"] for h in t.state.turn_history] == [1, 2]
    assert t.state.turn_history[-1]["total"] == 450
    assert t.state.turn_history[-1]["cost"] > t.state.turn_history[0]["cost"]


def test_list_sessions(tmp_path):
    make_tracker(tmp_path).record_usage(10, 10)
    make_tracker(tmp_path).record_usage(20, 20)
    assert len(SessionState.list_sessions(tmp_path)) == 2
