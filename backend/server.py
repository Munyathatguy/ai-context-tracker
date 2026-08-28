import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from typing import List, Optional
from zoneinfo import ZoneInfo

import yaml

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

sys.path.insert(0, "/app/ai-context-tracker")
from ai_context_tracker.config import load_config
from ai_context_tracker.models import resolve_model
from ai_context_tracker.providers import get_provider
from ai_context_tracker.state import SessionState

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

STATE_DIR = Path(os.environ['ACT_STATE_DIR'])

app = FastAPI(title="ai-context-tracker companion API")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "ai-context-tracker companion API"}


def _detail(st: SessionState) -> dict:
    spec = resolve_model(st.model)
    total = st.usage.get("total", 0)
    pct_used = min(100.0, 100.0 * total / spec["context_window"]) if spec["context_window"] else 0.0
    return {
        "session": st.__dict__,
        "model_spec": spec,
        "pct_used": round(pct_used, 2),
        "pct_remaining": round(100.0 - pct_used, 2),
    }


def _latest_id() -> str | None:
    ptr = STATE_DIR / "latest.json"
    if ptr.is_file():
        try:
            return json.loads(ptr.read_text()).get("session_id")
        except json.JSONDecodeError:
            return None
    return None


@api_router.get("/tracker/sessions")
async def list_sessions():
    return {"sessions": SessionState.list_sessions(STATE_DIR), "latest_session_id": _latest_id()}


@api_router.get("/tracker/sessions/{session_id}")
async def get_session(session_id: str):
    st = SessionState.load(STATE_DIR, session_id)
    if not st:
        raise HTTPException(status_code=404, detail="session not found")
    return _detail(st)


@api_router.get("/tracker/stream")
async def stream(session_id: str = ""):
    async def gen():
        last = None
        while True:
            sid = session_id or _latest_id()
            st = SessionState.load(STATE_DIR, sid) if sid else None
            payload = json.dumps({
                "sessions": SessionState.list_sessions(STATE_DIR),
                "latest_session_id": _latest_id(),
                "detail": _detail(st) if st else None,
            })
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            else:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.7)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


CONFIG_PATH = STATE_DIR / "config.yaml"


def _fix_latest():
    remaining = SessionState.list_sessions(STATE_DIR)
    ptr = STATE_DIR / "latest.json"
    cur = _latest_id()
    if cur and any(s["session_id"] == cur for s in remaining):
        return
    if remaining:
        ptr.write_text(json.dumps({"session_id": remaining[0]["session_id"]}))
    elif ptr.is_file():
        ptr.unlink()


@api_router.post("/tracker/sessions/{session_id}/archive")
async def archive_session(session_id: str):
    f = STATE_DIR / "sessions" / f"{session_id}.json"
    if not f.is_file():
        raise HTTPException(status_code=404, detail="session not found")
    dest = STATE_DIR / "archive"
    dest.mkdir(parents=True, exist_ok=True)
    f.rename(dest / f.name)
    _fix_latest()
    return {"archived": session_id}


@api_router.delete("/tracker/sessions/{session_id}")
async def delete_session(session_id: str):
    f = STATE_DIR / "sessions" / f"{session_id}.json"
    if not f.is_file():
        raise HTTPException(status_code=404, detail="session not found")
    f.unlink()
    _fix_latest()
    return {"deleted": session_id}


@api_router.get("/tracker/org-usage")
async def org_usage(provider: str = "openai", days: int = 7):
    p = get_provider(provider)
    if not p:
        raise HTTPException(status_code=422, detail=f"unknown provider: {provider}")
    return await asyncio.to_thread(p.get_org_usage, max(1, min(days, 31)))


class TrackerConfigUpdate(BaseModel):
    alert_thresholds: Optional[List[int]] = None
    red_alert_threshold: Optional[int] = None
    danger_threshold: Optional[int] = None
    auto_handoff: Optional[bool] = None
    timezone: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    features: Optional[dict] = None


def _effective_config() -> dict:
    cfg = load_config(str(CONFIG_PATH))
    return {
        "alert_thresholds": cfg.alert_thresholds,
        "red_alert_threshold": cfg.red_alert_threshold,
        "danger_threshold": cfg.danger_threshold,
        "auto_handoff": cfg.auto_handoff,
        "timezone": cfg.timezone,
        "provider": cfg.provider,
        "model": cfg.model,
        "features": cfg.features,
        "config_path": str(CONFIG_PATH),
    }


@api_router.get("/tracker/config")
async def get_tracker_config():
    return _effective_config()


@api_router.put("/tracker/config")
async def update_tracker_config(update: TrackerConfigUpdate):
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    if "timezone" in changes:
        try:
            ZoneInfo(changes["timezone"])
        except Exception:
            raise HTTPException(status_code=422, detail=f"Unknown timezone: {changes['timezone']}")
    for k in ("red_alert_threshold", "danger_threshold"):
        if k in changes and not 1 <= int(changes[k]) <= 99:
            raise HTTPException(status_code=422, detail=f"{k} must be between 1 and 99")
    if "alert_thresholds" in changes:
        ts = sorted({int(t) for t in changes["alert_thresholds"] if 1 <= int(t) <= 99}, reverse=True)
        if not ts:
            raise HTTPException(status_code=422, detail="alert_thresholds must contain values between 1 and 99")
        changes["alert_thresholds"] = ts
    existing = {}
    if CONFIG_PATH.is_file():
        existing = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    if "features" in changes:
        merged = dict(existing.get("features") or {})
        merged.update(changes["features"])
        changes["features"] = merged
    existing.update(changes)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(existing, sort_keys=False))
    return _effective_config()


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
