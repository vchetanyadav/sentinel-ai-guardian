import os
import time
import uuid
import random
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# Phoenix client (for prompts + datasets + experiments)
from phoenix.client import Client as PhoenixClient
from phoenix.client.types import PromptVersion

phoenix = PhoenixClient(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

# Firestore (for incidents + approvals)
from google.cloud import firestore
fs = firestore.Client(project=os.environ["GCP_PROJECT"])

# Gemini (for grading evaluation outputs)
from google import genai
gemini = genai.Client(
    vertexai=True,
    project=os.environ["GCP_PROJECT"],
    location=os.environ["GCP_LOCATION"],
)

# v13 content for rollback — we keep a known-good baseline locally
# (Sentinel will use this content when proposing a rollback)
import sys
from pathlib import Path
# Add refundbot folder to path so we can reuse its prompt content
sys.path.insert(0, str(Path(__file__).parent.parent / "refundbot"))
from prompt_content import V13_GOOD, V14_BAD


# ─── Metric computation tool ──────────────────────────────────────────

def compute_metric_window(window_minutes: int = 15) -> dict:
    """Compute eval-pass rate, p95 latency, and error rate for RefundBot 
    over the last N minutes vs the 24-hour baseline.
    
    Args:
        window_minutes: How many minutes back to look. Default 15.
    
    Returns:
        Dict with 'window' (recent metrics) and 'baseline_24h' (baseline metrics).
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)
    baseline_start = now - timedelta(hours=24)

    try:
        recent = phoenix.spans.get_spans_dataframe(
            project_identifier="refundbot-prod",
            start_time=window_start,
            end_time=now,
        )
        baseline = phoenix.spans.get_spans_dataframe(
            project_identifier="refundbot-prod",
            start_time=baseline_start,
            end_time=window_start,
        )
    except Exception as e:
        return {"error": f"Failed to fetch spans: {e}"}

    def summarize(df, label):
        if df is None or df.empty:
            return {"count": 0, "label": label}
        latencies_ms = (df["end_time"] - df["start_time"]).dt.total_seconds() * 1000
        error_rate = 0.0
        if "status_code" in df.columns:
            error_rate = float((df["status_code"] == "ERROR").mean())
        return {
            "count": int(len(df)),
            "p95_latency_ms": float(latencies_ms.quantile(0.95)) if len(latencies_ms) else 0.0,
            "error_rate": error_rate,
            "label": label,
        }

    return {
        "window": summarize(recent, f"last_{window_minutes}_min"),
        "baseline_24h": summarize(baseline, "last_24h_excluding_window"),
        "window_minutes": window_minutes,
    }


# ─── Regression detector ──────────────────────────────────────────────

def detect_regression(
    current_value: float,
    baseline_value: float,
    metric_name: str,
    threshold_pct: float = 15.0,
) -> dict:
    """Determine whether a metric represents a significant regression vs baseline."""
    if baseline_value == 0:
        return {"is_regression": False, "reason": "no_baseline_data", "metric": metric_name}
    
    delta_pct = ((current_value - baseline_value) / baseline_value) * 100
    is_reg = abs(delta_pct) > threshold_pct
    
    return {
        "is_regression": is_reg,
        "metric": metric_name,
        "current_value": current_value,
        "baseline_value": baseline_value,
        "delta_percent": round(delta_pct, 1),
        "direction": "worse" if delta_pct < 0 else "better",
    }


# ─── Phoenix prompt management tools ──────────────────────────────────

def list_phoenix_prompts(prompt_name: str = "refundbot-system-prompt") -> dict:
    """List recent prompt versions and their descriptions."""
    try:
        latest = phoenix.prompts.get(prompt_identifier=prompt_name)
        latest_text = latest.format().messages[0]["content"]
        
        if "customer happiness" in latest_text.lower() or "new policy update" in latest_text.lower():
            current_flavor = "v14 (broken)"
        elif "critical rules" in latest_text.lower() and "never approve" in latest_text.lower():
            current_flavor = "v13 (good)"
        else:
            current_flavor = "unknown"
        
        return {
            "prompt_name": prompt_name,
            "current_version_id": latest.id,
            "current_flavor": current_flavor,
            "known_versions": ["v13 (good)", "v14 (broken)"],
            "first_300_chars": latest_text[:300],
        }
    except Exception as e:
        return {"error": str(e)}


def deploy_prompt_version(version_label: Literal["v13", "v14"]) -> dict:
    """Deploy a specific prompt version (v13 or v14) as the new latest.
    Used by Sentinel to ROLL BACK from a bad prompt to a good one.
    """
    contents = {"v13": V13_GOOD, "v14": V14_BAD}
    if version_label not in contents:
        return {"error": f"Unknown version '{version_label}'"}
    
    try:
        new_version = phoenix.prompts.create(
            name="refundbot-system-prompt",
            version=PromptVersion(
                [{"role": "system", "content": contents[version_label]}],
                model_name="gemini-2.5-flash",
                description=f"Sentinel-deployed {version_label} rollback",
            ),
        )
        return {
            "deployed": version_label,
            "new_version_id": new_version.id,
            "action": "rollback" if version_label == "v13" else "deploy_new",
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Dataset evaluation tool ──────────────────────────────────────────

def _classify_response(answer: str) -> str:
    """Classify RefundBot's response as 'approve' or 'decline'.
    
    Approval signals win over decline signals because v13 often opens
    declines with 'I'm sorry, but...' which would otherwise be a false negative.
    """
    answer_lower = answer.lower()
    
    approved = any(phrase in answer_lower for phrase in [
        "process that", "process your refund", "process the refund",
        "i'll process", "i will process",
        "issued to your original", "full refund will",
        "refund right away", "of course", "happy to help",
        "approve your refund", "approved",
    ])
    declined = any(phrase in answer_lower for phrase in [
        "cannot issue", "can't issue", "unable to",
        "outside our policy", "outside of policy", "not eligible",
        "do not offer", "we don't offer", "do not accept",
        "unfortunately, we", "we are unable",
    ])
    
    # Approval signals win when both detected
    if approved:
        return "approve"
    if declined:
        return "decline"
    # Default to decline for ambiguous responses (v13 is cautious by nature)
    return "decline"


def run_dataset_evaluation(against_version: Literal["current", "v13", "v14"] = "current") -> dict:
    """Run RefundBot against the refundbot-golden-v1 dataset to measure accuracy.
    
    Args:
        against_version: 'current' uses whatever Phoenix currently has as latest;
                         'v13' or 'v14' deploys that version first, then evaluates.
    """
    # If asked to test a specific version, deploy it first
    if against_version in ("v13", "v14"):
        deploy_result = deploy_prompt_version(against_version)
        if "error" in deploy_result:
            return {"error": f"Could not deploy {against_version}: {deploy_result['error']}"}
        time.sleep(8)  # let the 5-second prompt cache in RefundBot expire (with safety margin)
    
    # Pull the golden dataset (handle both dict and object shapes)
    try:
        dataset = phoenix.datasets.get_dataset(dataset="refundbot-golden-v1")
        examples = dataset["examples"] if isinstance(dataset, dict) else dataset.examples
    except Exception as e:
        return {"error": f"Could not fetch golden dataset: {e}"}
    
    refundbot_url = f"{os.environ['REFUNDBOT_URL']}/ask"
    correct = 0
    by_category = {"approve": {"correct": 0, "total": 0}, "decline": {"correct": 0, "total": 0}}
    
    # Deterministic random sample to balance approve/decline cases.
    # Same seed → same 15 examples every run → consistent accuracy.
    rng = random.Random(42)
    sampled = rng.sample(list(examples), min(15, len(examples)))
    
    for ex in sampled:
        # Examples can be dict-like or attribute-like depending on client version
        inp = ex["input"] if isinstance(ex, dict) else ex.input
        out = ex["output"] if isinstance(ex, dict) else ex.output
        
        question = inp.get("question") or inp.get("input") or str(inp)
        expected = out.get("expected_action") or out.get("output")
        
        try:
            r = requests.post(refundbot_url, json={"customer_id": "eval", "message": question}, timeout=20)
            answer = r.json()["answer"]
        except Exception:
            continue
        
        actual = _classify_response(answer)
        
        if expected in by_category:
            by_category[expected]["total"] += 1
            if actual == expected:
                by_category[expected]["correct"] += 1
                correct += 1
    
    total_evaluated = sum(v["total"] for v in by_category.values())
    accuracy = correct / total_evaluated if total_evaluated else 0.0
    
    return {
        "accuracy": round(accuracy, 2),
        "correct": correct,
        "total_evaluated": total_evaluated,
        "by_category": by_category,
        "tested_version": against_version,
    }


# ─── Incident management tools ────────────────────────────────────────

def open_incident(
    title: str,
    severity: Literal["low", "medium", "high"],
    hypothesis: str,
    proposed_action: str,
) -> dict:
    """Create an incident record in Firestore."""
    incident_id = f"INC-{int(time.time())}"
    doc = {
        "id": incident_id,
        "title": title,
        "severity": severity,
        "hypothesis": hypothesis,
        "proposed_action": proposed_action,
        "status": "investigating",
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    fs.collection("incidents").document(incident_id).set(doc)
    return {"incident_id": incident_id, "status": "created"}


def update_incident(
    incident_id: str,
    status: str,
    postmortem: str = "",
) -> dict:
    """Update an incident with a new status and optional postmortem."""
    fs.collection("incidents").document(incident_id).update({
        "status": status,
        "postmortem": postmortem,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    return {"updated": True, "incident_id": incident_id, "status": status}


# ─── Human approval gate ──────────────────────────────────────────────

def request_human_approval(
    incident_id: str,
    proposed_action: str,
    rationale: str,
) -> dict:
    """Request human approval before executing a remediation.
    BLOCKS until the human approves or rejects via Firestore (timeout: 5 minutes).
    """
    request_id = str(uuid.uuid4())
    
    fs.collection("approval_requests").document(request_id).set({
        "request_id": request_id,
        "incident_id": incident_id,
        "proposed_action": proposed_action,
        "rationale": rationale,
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    
    print(f"\n{'='*60}")
    print(f"🔔 APPROVAL REQUIRED")
    print(f"{'='*60}")
    print(f"Incident: {incident_id}")
    print(f"Proposed action: {proposed_action}")
    print(f"Rationale: {rationale}")
    print(f"\nTo approve, run in another terminal:")
    print(f"  python approve.py {request_id} approve")
    print(f"To reject:")
    print(f"  python approve.py {request_id} reject")
    print(f"{'='*60}\n")
    
    # Poll Firestore for status change (max 5 min)
    deadline = time.time() + 300
    while time.time() < deadline:
        doc = fs.collection("approval_requests").document(request_id).get()
        status = doc.to_dict().get("status")
        if status == "approved":
            return {"approved": True, "request_id": request_id}
        if status == "rejected":
            return {"approved": False, "request_id": request_id, "reason": "human_rejected"}
        time.sleep(2)
    
    return {"approved": False, "request_id": request_id, "reason": "timeout"}