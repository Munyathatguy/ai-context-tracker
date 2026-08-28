"""Iteration 3 tests: Config API (GET/PUT), regression on sessions & stream."""
import os
import yaml
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ai-tracker-20.preview.emergentagent.com").rstrip("/")
CFG_PATH = Path("/root/.ai-context-tracker/config.yaml")


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Config GET ---
def test_config_get_defaults(client):
    r = client.get(f"{BASE_URL}/api/tracker/config")
    assert r.status_code == 200
    d = r.json()
    for k in ["alert_thresholds", "red_alert_threshold", "danger_threshold",
              "auto_handoff", "timezone", "features", "config_path"]:
        assert k in d, f"missing {k}"
    assert d["config_path"] == "/root/.ai-context-tracker/config.yaml"
    assert isinstance(d["alert_thresholds"], list)
    assert isinstance(d["features"], dict)


# --- Config PUT valid ---
def test_config_put_valid_and_persist(client):
    payload = {
        "alert_thresholds": [35, 15],
        "timezone": "Europe/London",
        "features": {"cost_tracking": False},
    }
    r = client.put(f"{BASE_URL}/api/tracker/config", json=payload)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["alert_thresholds"] == [35, 15]
    assert d["timezone"] == "Europe/London"
    assert d["features"]["cost_tracking"] is False
    # file persisted
    assert CFG_PATH.is_file()
    on_disk = yaml.safe_load(CFG_PATH.read_text())
    assert on_disk["alert_thresholds"] == [35, 15]
    assert on_disk["timezone"] == "Europe/London"
    assert on_disk["features"]["cost_tracking"] is False
    # GET reflects
    g = client.get(f"{BASE_URL}/api/tracker/config").json()
    assert g["alert_thresholds"] == [35, 15]
    assert g["timezone"] == "Europe/London"


# --- Config PUT invalid tz ---
def test_config_put_invalid_timezone(client):
    r = client.put(f"{BASE_URL}/api/tracker/config", json={"timezone": "Not/AZone"})
    assert r.status_code == 422


# --- Config PUT thresholds filtered / all-invalid rejected ---
def test_config_put_thresholds_all_invalid(client):
    r = client.put(f"{BASE_URL}/api/tracker/config", json={"alert_thresholds": [0, 100, 200]})
    assert r.status_code == 422


def test_config_put_thresholds_filter_and_sort(client):
    r = client.put(f"{BASE_URL}/api/tracker/config",
                   json={"alert_thresholds": [15, 100, 40, 0, 5]})
    assert r.status_code == 200
    assert r.json()["alert_thresholds"] == [40, 15, 5]


# --- Restore defaults ---
def test_zz_restore_defaults(client):
    r = client.put(f"{BASE_URL}/api/tracker/config", json={
        "alert_thresholds": [30, 20, 10],
        "timezone": "UTC",
        "features": {
            "token_tracking": True, "time_awareness": True, "context_health": True,
            "session_continuity": True, "model_awareness": True, "task_tracking": True,
            "cost_tracking": True, "turn_counter": True,
        },
    })
    assert r.status_code == 200
    d = r.json()
    assert d["alert_thresholds"] == [30, 20, 10]
    assert d["timezone"] == "UTC"
    assert d["features"]["cost_tracking"] is True


# --- Regression ---
def test_sessions_list(client):
    r = client.get(f"{BASE_URL}/api/tracker/sessions")
    assert r.status_code == 200
    d = r.json()
    assert "sessions" in d and isinstance(d["sessions"], list)
    assert "latest_session_id" in d


def test_session_detail(client):
    r = client.get(f"{BASE_URL}/api/tracker/sessions/a1aae646106f")
    assert r.status_code == 200
    d = r.json()
    assert d["session"]["session_id"] == "a1aae646106f"
    assert "model_spec" in d


def test_session_detail_404(client):
    r = client.get(f"{BASE_URL}/api/tracker/sessions/nonexistent-xyz")
    assert r.status_code == 404
