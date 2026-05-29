import asyncio
import json
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
import time
import asyncio
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

# ─── Live Sentinel runs (streaming via SSE) ───────────────────────────

from sse_starlette.sse import EventSourceResponse
from fastapi import BackgroundTasks
import threading
from event_logger import EventLogger

# In-memory store for active runs and their event queues
_active_runs: dict[str, asyncio.Queue] = {}
_run_results: dict[str, str] = {}  # run_id -> "completed" | "failed"


async def _stream_run_events(run_id: str):
    """Yield SSE events as Sentinel produces them."""
    queue = _active_runs.get(run_id)
    if not queue:
        yield {"event": "error", "data": json.dumps({"message": "Run not found"})}
        return
    
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=180)
        except asyncio.TimeoutError:
            yield {"event": "error", "data": json.dumps({"message": "Timeout"})}
            break
        
        if event is None:  # sentinel signal for "done"
            yield {"event": "done", "data": json.dumps({"run_id": run_id})}
            break
        
        yield {"event": event["type"], "data": json.dumps(event)}


@app.post("/api/sentinel/run")
async def trigger_sentinel():
    """Kick off Sentinel in a background thread; return a run_id for the client to subscribe to."""
    run_id = f"live-{int(time.time())}"
    queue: asyncio.Queue = asyncio.Queue()
    _active_runs[run_id] = queue
    
    loop = asyncio.get_event_loop()
    
    def run_in_thread():
        try:
            asyncio.run(_run_sentinel_with_streaming(run_id, queue, loop))
            _run_results[run_id] = "completed"
        except Exception as e:
            print(f"Run {run_id} failed: {e}")
            _run_results[run_id] = "failed"
        finally:
            # Signal end-of-stream
            loop.call_soon_threadsafe(queue.put_nowait, None)
    
    threading.Thread(target=run_in_thread, daemon=True).start()
    return {"run_id": run_id}


async def _run_sentinel_with_streaming(run_id: str, queue: asyncio.Queue, main_loop):
    """Run Sentinel and push every event into the queue for SSE streaming."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    from agent import create_sentinel
    
    def push(event_dict):
        """Push a serialized event onto the queue from a sync context."""
        main_loop.call_soon_threadsafe(queue.put_nowait, event_dict)
    
    agent = create_sentinel()
    runner = InMemoryRunner(agent=agent, app_name="sentinel-live")
    
    user_id = "ui-operator"
    session = await runner.session_service.create_session(
        app_name="sentinel-live",
        user_id=user_id,
    )
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            "RefundBot may have a regression. Check the last 15 minutes of traffic, "
            "diagnose any issues, propose a fix, and resolve it under human oversight."
        ))],
    )
    
    logger = EventLogger(run_id=run_id)
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                ts = datetime.now(timezone.utc).isoformat()
                
                if part.text:
                    if "🔍" in part.text:
                        for line in part.text.split("\n"):
                            if "🔍" in line:
                                label = line.split("🔍", 1)[1].strip()
                                logger.log_plan_step(label)
                                push({"type": "plan_step", "timestamp": ts, "label": label})
                    else:
                        logger.log_message(part.text)
                        push({"type": "message", "timestamp": ts, "text": part.text})
                
                if part.function_call:
                    args = dict(part.function_call.args)
                    logger.log_tool_call(part.function_call.name, args)
                    push({
                        "type": "tool_call",
                        "timestamp": ts,
                        "name": part.function_call.name,
                        "args": args,
                    })
                
                if part.function_response:
                    response = part.function_response.response
                    logger.log_tool_result(response)
                    push({
                        "type": "tool_result",
                        "timestamp": ts,
                        "result": EventLogger._serializable(response),
                    })
    
    logger.save()


@app.get("/api/sentinel/stream/{run_id}")
async def stream_sentinel(run_id: str):
    """Subscribe to live events from a running Sentinel session."""
    return EventSourceResponse(_stream_run_events(run_id))