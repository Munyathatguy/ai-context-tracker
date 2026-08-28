"""Iteration 4 backend tests: org-usage, archive/delete sessions, turn_history."""
import os
import sys
import json
import subprocess
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ai-tracker-20.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api/tracker"
STATE_DIR = Path("/root/.ai-context-tracker")

SEEDED = {"3aacc4b13b92", "0b15287ef875", "b98b6f902048"}


# ------------------- Org Usage API -------------------
class TestOrgUsage:
    def test_anthropic_missing_admin_key(self):
        r = requests.get(f"{API}/org-usage", params={"provider": "anthropic"})
        assert r.status_code == 200
        data = r.json()
        assert "error" in data
        assert "ANTHROPIC_ADMIN_KEY" in data["error"]

    def test_openai_missing_admin_key(self):
        r = requests.get(f"{API}/org-usage", params={"provider": "openai"})
        assert r.status_code == 200
        data = r.json()
        assert "error" in data
        assert "OPENAI_ADMIN_KEY" in data["error"]

    def test_google_note(self):
        r = requests.get(f"{API}/org-usage", params={"provider": "google"})
        assert r.status_code == 200
        data = r.json()
        assert "note" in data

    def test_bogus_provider_422(self):
        r = requests.get(f"{API}/org-usage", params={"provider": "bogus"})
        assert r.status_code == 422


# ------------------- turn_history -------------------
class TestTurnHistory:
    def test_latest_session_has_turn_history(self):
        # Pin to seeded claude session which has 7 turns (avoid xdist race with throwaway creation)
        sid = "3aacc4b13b92"
        rd = requests.get(f"{API}/sessions/{sid}")
        assert rd.status_code == 200
        session = rd.json().get("session", rd.json())
        history = session.get("turn_history")
        assert isinstance(history, list)
        assert len(history) == 7
        totals = []
        for entry in history:
            for k in ("turn", "total", "input", "output", "cost", "at"):
                assert k in entry, f"missing {k} in {entry}"
            totals.append(entry["total"])
        # monotonically increasing totals
        assert totals == sorted(totals)
        assert len(set(totals)) >= 1


# ------------------- Helpers to create throwaway sessions -------------------
def _create_throwaway_session():
    """Create a fresh session by calling ContextTracker directly."""
    code = (
        "import sys; sys.path.insert(0, '/app/ai-context-tracker');"
        "from ai_context_tracker.tracker import ContextTracker;"
        "from ai_context_tracker.config import Config;"
        "import os; os.environ['ACT_STATE_DIR']='/root/.ai-context-tracker';"
        "t = ContextTracker(Config(state_dir='/root/.ai-context-tracker'));"
        "t.record_usage(10, 10);"
        "print(t.state.session_id)"
    )
    res = subprocess.run(
        ["python", "-c", code], capture_output=True, text=True, timeout=30
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    sid = res.stdout.strip().splitlines()[-1]
    assert len(sid) >= 8
    return sid


# ------------------- Archive API -------------------
class TestArchive:
    def test_archive_moves_file_and_removes_from_list(self):
        sid = _create_throwaway_session()
        assert sid not in SEEDED
        src = STATE_DIR / "sessions" / f"{sid}.json"
        assert src.exists()

        # Sanity: appears in list
        listing = requests.get(f"{API}/sessions").json()
        ids = [s["session_id"] for s in listing["sessions"]]
        assert sid in ids

        r = requests.post(f"{API}/sessions/{sid}/archive")
        assert r.status_code == 200, r.text

        # File moved
        assert not src.exists()
        assert (STATE_DIR / "archive" / f"{sid}.json").exists()

        # Gone from list
        listing2 = requests.get(f"{API}/sessions").json()
        ids2 = [s["session_id"] for s in listing2["sessions"]]
        assert sid not in ids2

        # latest fixed if it pointed at archived session
        assert listing2.get("latest_session_id") not in (sid, None) or len(ids2) == 0

    def test_archive_unknown_id_404(self):
        r = requests.post(f"{API}/sessions/deadbeef1234/archive")
        assert r.status_code == 404


# ------------------- Delete API -------------------
class TestDelete:
    def test_delete_removes_file(self):
        sid = _create_throwaway_session()
        assert sid not in SEEDED
        src = STATE_DIR / "sessions" / f"{sid}.json"
        assert src.exists()

        r = requests.delete(f"{API}/sessions/{sid}")
        assert r.status_code in (200, 204), r.text
        assert not src.exists()

        listing = requests.get(f"{API}/sessions").json()
        ids = [s["session_id"] for s in listing["sessions"]]
        assert sid not in ids

    def test_delete_unknown_id_404(self):
        r = requests.delete(f"{API}/sessions/deadbeef9999")
        assert r.status_code == 404


# ------------------- Cleanup: restore latest pointer to seeded claude session -------------------
def teardown_module(module):
    # Ensure latest.json points to a seeded session (prefer claude 3aacc4b13b92)
    latest_file = STATE_DIR / "latest.json"
    try:
        cur = json.loads(latest_file.read_text()).get("session_id")
    except Exception:
        cur = None
    if cur not in SEEDED:
        latest_file.write_text(json.dumps({"session_id": "3aacc4b13b92"}))
