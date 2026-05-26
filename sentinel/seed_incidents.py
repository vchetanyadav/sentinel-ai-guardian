import os, time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

fs = firestore.Client(project=os.environ["GCP_PROJECT"])

now = datetime.now(timezone.utc)

HISTORICAL_INCIDENTS = [
    {
        "id": "INC-1716192000",
        "title": "Latency spike in refund queries (p95 > 8s)",
        "severity": "medium",
        "hypothesis": "Model cold-start after deploy. Resolved automatically after 12 min.",
        "proposed_action": "Monitor; auto-resolved",
        "status": "resolved",
        "postmortem": "p95 latency briefly spiked to 9.2s during a deployment window. Sentinel detected and monitored, but no remediation was needed — metrics self-recovered within 12 minutes as warm instances scaled up. Marked as informational.",
        "created_at": now - timedelta(days=8, hours=3),
    },
    {
        "id": "INC-1716364800",
        "title": "Hallucinated refund window (60-day claims)",
        "severity": "high",
        "hypothesis": "RefundBot started citing 60-day return windows after a prompt edit introduced ambiguity.",
        "proposed_action": "Rollback to prompt v11",
        "status": "resolved",
        "postmortem": "Prompt v12 removed the explicit '30-day' wording in favor of a softer phrasing, causing Gemini to generalize incorrectly. Rolled back to v11 within 6 minutes of detection. 4 customers were quoted incorrect windows during the regression window; CS team contacted them.",
        "created_at": now - timedelta(days=6, hours=14),
    },
    {
        "id": "INC-1716537600",
        "title": "Repeated 'human agent' deferrals — accuracy dropped to 64%",
        "severity": "medium",
        "hypothesis": "Over-cautious prompt v12.1 caused RefundBot to defer 38% of in-policy refunds to humans.",
        "proposed_action": "Rollback to prompt v12",
        "status": "rejected_by_human",
        "postmortem": "Sentinel proposed rollback to v12, but operator (chetan) rejected — preferring to investigate whether a more permissive variant could be tuned. No remediation taken via Sentinel; addressed manually outside the system.",
        "created_at": now - timedelta(days=4, hours=8),
    },
    {
        "id": "INC-1716710400",
        "title": "Approving final-sale refunds — policy violation pattern detected",
        "severity": "high",
        "hypothesis": "Prompt v13 introduced 'try to help' language that softened the final-sale rule.",
        "proposed_action": "Rollback to prompt v12",
        "status": "resolved",
        "postmortem": "Eval accuracy dropped from 89% to 62% over 90 minutes. Sentinel pinpointed v13 as the cause and rolled back to v12. Post-fix verification: accuracy restored to 88%. Estimated 11 final-sale refunds incorrectly approved before detection; refunded as a goodwill gesture but flagged for finance review.",
        "created_at": now - timedelta(days=2, hours=20),
    },
    {
        "id": "INC-1716883200",
        "title": "Error rate spike — Gemini API timeouts",
        "severity": "low",
        "hypothesis": "Upstream Gemini API briefly returned 503s. Not a prompt or model issue.",
        "proposed_action": "No action; upstream incident",
        "status": "resolved",
        "postmortem": "RefundBot error rate jumped to 4.2% for 11 minutes due to upstream Gemini API instability. Sentinel correctly classified this as an upstream issue and did not propose remediation. Error rate self-recovered.",
        "created_at": now - timedelta(days=1, hours=5),
    },
]

for inc in HISTORICAL_INCIDENTS:
    incident_id = inc.pop("id")
    fs.collection("incidents").document(incident_id).set(inc)
    print(f"✅ Seeded {incident_id} — {inc['title'][:50]}")

print(f"\n✅ Seeded {len(HISTORICAL_INCIDENTS)} historical incidents")