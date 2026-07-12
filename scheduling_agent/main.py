"""
main.py

Step 7 - Local test website for the Smart Asset Re-routing & Scheduling
Optimizer module.

This is a STANDALONE FastAPI app for YOUR testing only - it wraps your
agent (agents/scheduling_agent.py) and your database in a simple local
website with two views:
    - Chat: talk to the Hospital Scheduling Optimization Assistant
    - Dashboard: see which assets are currently down, and browse all
      appointments in the database

This does NOT touch your teammates' code or files. It's a separate
local tool that only runs on your own machine when you start it.

Run with:
    py -m uvicorn main:app --reload

Then open in your browser:
    http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "database"))

from db import db  # noqa: E402

# NOTE: We can't do `from scheduling_agent import build_agent, run_query` here.
# This file lives inside a folder that is ALSO named `scheduling_agent`
# (because the root app.py does `from scheduling_agent.main import app`),
# so Python resolves that import against the already-imported package
# (the folder itself), not the agents/scheduling_agent.py file we actually
# want. Loading it directly by file path avoids the name collision.
import importlib.util as _ilu

_agent_module_path = os.path.join(os.path.dirname(__file__), "agents", "scheduling_agent.py")
_spec = _ilu.spec_from_file_location("scheduling_agent_impl", _agent_module_path)
_scheduling_agent_impl = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_scheduling_agent_impl)
build_agent = _scheduling_agent_impl.build_agent
run_query = _scheduling_agent_impl.run_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Hospital Scheduling Optimizer - Test Website")

# Build the agent once at startup, reuse for every chat request.
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        logger.info("Building agent (first request)...")
        _agent = build_agent()
    return _agent


# --------------------------------------------------------------------------
# Request/response models
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class AssetStatus(BaseModel):
    asset_id: str
    asset_name: Optional[str]
    asset_type: Optional[str]
    department: Optional[str]
    status: Optional[str]


class Appointment(BaseModel):
    schedule_id: int
    patient_name: str
    asset_id: str
    scheduled_datetime: str
    status: str


# --------------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message to the Hospital Scheduling Optimization Assistant."""
    try:
        agent = get_agent()
        reply = run_query(agent, request.message)
        return ChatResponse(reply=reply)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/assets/non-operational", response_model=List[AssetStatus])
def get_non_operational_assets():
    """Return every asset whose CURRENT status is not 'Operational'."""
    query = """
        WITH current_status AS (
            SELECT DISTINCT ON (asset_id)
                asset_id, status, start_time, end_time
            FROM asset_status_log
            ORDER BY asset_id, (end_time IS NULL) DESC, start_time DESC
        )
        SELECT a.asset_id, a.asset_name, a.asset_type, a.department, cs.status
        FROM asset a
        JOIN current_status cs ON cs.asset_id = a.asset_id
        WHERE cs.status <> 'Operational'
        ORDER BY a.asset_id
    """
    with db.engine.connect() as conn:
        rows = conn.execute(text(query)).mappings().all()
    return [AssetStatus(**dict(r)) for r in rows]


@app.get("/api/appointments", response_model=List[Appointment])
def get_appointments(asset_id: Optional[str] = None):
    """Return all appointments, optionally filtered by asset_id."""
    query = """
        SELECT
            ps.schedule_id,
            COALESCE(p.first_name || ' ' || p.last_name, 'Unknown') AS patient_name,
            ps.asset_id,
            ps.scheduled_datetime,
            ps.status
        FROM procedure_schedule ps
        JOIN person p ON p.person_id = ps.patient_id
    """
    params = {}
    if asset_id:
        query += " WHERE ps.asset_id = :asset_id"
        params["asset_id"] = asset_id
    query += " ORDER BY ps.scheduled_datetime ASC"

    with db.engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    return [
        Appointment(
            schedule_id=r["schedule_id"],
            patient_name=r["patient_name"],
            asset_id=r["asset_id"],
            scheduled_datetime=r["scheduled_datetime"].strftime("%Y-%m-%d %H:%M"),
            status=r["status"] or "Scheduled",
        )
        for r in rows
    ]


# --------------------------------------------------------------------------
# Serve the frontend (static/index.html)
# --------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")