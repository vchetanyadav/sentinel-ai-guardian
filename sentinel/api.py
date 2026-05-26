import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore

load_dotenv()

fs = firestore.Client(project=os.environ["GCP_PROJECT"])

app = FastAPI(title="Sentinel API", version="0.1")

# Allow Next.js dev server to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Incidents ────────────────────────────────────────────────────────

@app.get("/api/incidents")
def list_incidents(limit: int = 50):
    """Return all incidents, newest first."""
    docs = (
        fs.collection("incidents")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    incidents = []
    for doc in docs:
        d = doc.to_dict()
        # Convert Firestore timestamps to ISO strings for JSON
        for ts_field in ("created_at", "updated_at", "resolved_at"):
            if ts_field in d and d[ts_field] is not None:
                d[ts_field] = d[ts_field].isoformat() if hasattr(d[ts_field], "isoformat") else str(d[ts_field])
        incidents.append(d)
    return {"incidents": incidents}


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    doc = fs.collection("incidents").document(incident_id).get()
    if not doc.exists:
        raise HTTPException(404, "Incident not found")
    d = doc.to_dict()
    for ts_field in ("created_at", "updated_at", "resolved_at"):
        if ts_field in d and d[ts_field] is not None:
            d[ts_field] = d[ts_field].isoformat() if hasattr(d[ts_field], "isoformat") else str(d[ts_field])
    return d


# ─── Approval queue ───────────────────────────────────────────────────

class ApprovalDecision(BaseModel):
    decision: str  # "approve" or "reject"


@app.get("/api/approvals/pending")
def pending_approvals():
    """Return pending approval requests, newest first."""
    docs = (
        fs.collection("approval_requests")
        .where("status", "==", "pending")
        .stream()
    )
    pending = []
    for doc in docs:
        d = doc.to_dict()
        if "created_at" in d and d["created_at"] is not None:
            d["created_at"] = d["created_at"].isoformat() if hasattr(d["created_at"], "isoformat") else str(d["created_at"])
        pending.append(d)
    return {"pending": pending}


@app.post("/api/approvals/{request_id}/decide")
def decide_approval(request_id: str, decision: ApprovalDecision):
    if decision.decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be 'approve' or 'reject'")
    new_status = "approved" if decision.decision == "approve" else "rejected"
    fs.collection("approval_requests").document(request_id).update(
        {"status": new_status}
    )
    return {"ok": True, "request_id": request_id, "status": new_status}


# ─── Runs (fixture playback) ──────────────────────────────────────────

RUNS_DIR = Path(__file__).parent / "runs"


@app.get("/api/runs")
def list_runs():
    if not RUNS_DIR.exists():
        return {"runs": []}
    runs = []
    for f in sorted(RUNS_DIR.glob("run_*.json"), reverse=True):
        with open(f) as fp:
            data = json.load(fp)
        runs.append({"run_id": data["run_id"], "event_count": len(data["events"])})
    return {"runs": runs}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    path = RUNS_DIR / f"run_{run_id}.json"
    if not path.exists():
        raise HTTPException(404, "Run not found")
    with open(path) as f:
        return json.load(f)


# ─── Health ───────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinel-api"}