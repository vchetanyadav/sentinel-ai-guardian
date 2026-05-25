import json, random, time, requests
from datetime import datetime, timedelta

REFUNDBOT_URL = "http://127.0.0.1:8080/ask"  # change to Cloud Run URL if deployed
QUESTIONS = json.load(open("synthetic_questions.json"))

print(f"Seeding {len(QUESTIONS)} questions over the next ~30 minutes...")
print("This will populate Phoenix with realistic-looking historical traffic.")
print()

random.shuffle(QUESTIONS)

for i, q in enumerate(QUESTIONS):
    customer_id = f"c{random.randint(1000, 9999)}"
    try:
        r = requests.post(
            REFUNDBOT_URL,
            json={"customer_id": customer_id, "message": q},
            timeout=30,
        )
        status = "✓" if r.status_code == 200 else f"✗({r.status_code})"
    except Exception as e:
        status = f"err: {e}"
    
    print(f"[{i+1}/{len(QUESTIONS)}] {status}  {q[:60]}...")
    
    # Pace ~1 request per 10 seconds for realistic traffic spread
    time.sleep(random.uniform(7, 13))