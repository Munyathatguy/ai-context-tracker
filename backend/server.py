import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

sys.path.insert(0, "/app/ai-context-tracker")
from ai_context_tracker.models import resolve_model
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


@api_router.get("/tracker/sessions")
async def list_sessions():
    sessions = SessionState.list_sessions(STATE_DIR)
    latest_id = None
    ptr = STATE_DIR / "latest.json"
    if ptr.is_file():
        latest_id = json.loads(ptr.read_text()).get("session_id")
    return {"sessions": sessions, "latest_session_id": latest_id}


@api_router.get("/tracker/sessions/{session_id}")
async def get_session(session_id: str):
    st = SessionState.load(STATE_DIR, session_id)
    if not st:
        raise HTTPException(status_code=404, detail="session not found")
    spec = resolve_model(st.model)
    total = st.usage.get("total", 0)
    pct_used = min(100.0, 100.0 * total / spec["context_window"]) if spec["context_window"] else 0.0
    return {
        "session": st.__dict__,
        "model_spec": spec,
        "pct_used": round(pct_used, 2),
        "pct_remaining": round(100.0 - pct_used, 2),
    }


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
