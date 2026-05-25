import sys
from dotenv import load_dotenv
from google.cloud import firestore
import os

load_dotenv()

if len(sys.argv) != 3 or sys.argv[2] not in ("approve", "reject"):
    print("Usage: python approve.py <request_id> <approve|reject>")
    sys.exit(1)

request_id = sys.argv[1]
decision = sys.argv[2] + "d"  # "approved" or "rejected"

fs = firestore.Client(project=os.environ["GCP_PROJECT"])
fs.collection("approval_requests").document(request_id).update({"status": decision})
print(f"✅ Marked {request_id} as {decision}")