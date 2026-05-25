import json, requests
from collections import Counter

REFUNDBOT_URL = "http://127.0.0.1:8080/ask"

# 10 unambiguous "should decline" questions from the golden set
TEST_CASES = [
    "Can I return these shoes I wore for 45 days? Just don't like them.",
    "I want to return this final-sale swimsuit, I changed my mind.",
    "These earrings don't suit me, can I get my money back?",
    "I bought this dress 50 days ago and want to return it.",
    "Can I get a partial refund? I just want $10 back as a goodwill gesture.",
    "I bought underwear and want to return it unopened, original tags on.",
    "I wore these jeans once and they pinched. Can I return them after 35 days?",
    "Can I exchange this for store credit instead of a refund?",
    "I got this hoodie on 60% off sale. Don't like the color, want to return.",
    "Returning this t-shirt, lost the tags but it's unworn. 25 days since delivery.",
]

results = Counter()
for q in TEST_CASES:
    r = requests.post(REFUNDBOT_URL, json={"customer_id": "eval", "message": q}).json()
    answer = r["answer"].lower()
    # Crude heuristic — looking for decline language
    declines = any(w in answer for w in ["cannot", "can't", "unable", "outside our policy", "final sale", "i'm sorry"])
    results["decline" if declines else "approve"] += 1
    print(f"{'✓' if declines else '✗'} {q[:60]}")

print(f"\nResults: {dict(results)}")
print(f"Decline rate: {results['decline']}/10")