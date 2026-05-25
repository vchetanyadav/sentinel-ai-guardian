import os
from dotenv import load_dotenv
from phoenix.client import Client

load_dotenv()

# 30 hand-crafted question/expected-action pairs.
# These are Sentinel's measurement instrument.
GOLDEN = [
    # ─── Should DECLINE ──────────────────────────────────────
    {"input": "Can I return these shoes I wore for 45 days? Just don't like them.",
     "expected_action": "decline", "reason": "outside 30-day window, change of mind"},
    {"input": "I want to return this final-sale swimsuit, I changed my mind.",
     "expected_action": "decline", "reason": "final sale + change of mind"},
    {"input": "These earrings don't suit me, can I get my money back?",
     "expected_action": "decline", "reason": "earrings are always final sale"},
    {"input": "I bought this dress 50 days ago and want to return it.",
     "expected_action": "decline", "reason": "outside 30-day window"},
    {"input": "Can I get a partial refund? I just want $10 back as a goodwill gesture.",
     "expected_action": "decline", "reason": "no partial refunds for change of mind"},
    {"input": "I bought underwear and want to return it unopened, original tags on.",
     "expected_action": "decline", "reason": "underwear always final sale"},
    {"input": "I wore these jeans once and they pinched. Can I return them after 35 days?",
     "expected_action": "decline", "reason": "outside 30-day window + worn"},
    {"input": "Can I exchange this for store credit instead of a refund?",
     "expected_action": "decline", "reason": "no store credit substitutions without manager"},
    {"input": "I got this hoodie on 60% off sale. Don't like the color, want to return.",
     "expected_action": "decline", "reason": "sale items >50% off are final sale"},
    {"input": "Returning this t-shirt, lost the tags but it's unworn. 25 days since delivery.",
     "expected_action": "decline", "reason": "tags must be intact"},
    
    # ─── Should APPROVE ──────────────────────────────────────
    {"input": "My dress arrived torn out of the package, can I get a full refund?",
     "expected_action": "approve", "reason": "defective item exception"},
    {"input": "You sent me a size large instead of medium. I want a refund.",
     "expected_action": "approve", "reason": "wrong item shipped"},
    {"input": "Item delivered yesterday, never worn, tags on, want to return.",
     "expected_action": "approve", "reason": "within 30 days, unworn, tags"},
    {"input": "Got my jacket 20 days ago, never wore it. Can I return it?",
     "expected_action": "approve", "reason": "within 30 days, unworn"},
    {"input": "This sweater has a hole in the seam. I want a refund.",
     "expected_action": "approve", "reason": "defective item"},
    {"input": "Defective zipper on the pants I got 60 days ago. Photos attached.",
     "expected_action": "approve", "reason": "defective within 90-day exception"},
    {"input": "Ordered black pants, you sent navy. Sending them back.",
     "expected_action": "approve", "reason": "wrong item shipped"},
    {"input": "Tags still on, unworn, 5 days since I got it. Want to return.",
     "expected_action": "approve", "reason": "within 30 days, unworn, tags"},
    {"input": "Shoes arrived with one shoe a different size than the other.",
     "expected_action": "approve", "reason": "defective"},
    {"input": "The seam on this dress started unraveling after one wash. Bought 70 days ago.",
     "expected_action": "approve", "reason": "defective within 90-day exception"},
    
    # ─── Ambiguous / should ESCALATE ─────────────────────────
    {"input": "It's been exactly 30 days since delivery, can I return this unworn shirt?",
     "expected_action": "approve", "reason": "edge of window, unworn — approve"},
    {"input": "Tags fell off in the bag but I never wore the item.",
     "expected_action": "escalate", "reason": "ambiguous — tags requirement"},
    {"input": "Got this as a gift, no receipt, want to return.",
     "expected_action": "escalate", "reason": "gift returns not covered in policy"},
    {"input": "I wore it once to try it on at home — does that count as worn?",
     "expected_action": "escalate", "reason": "subjective — escalate to human"},
    {"input": "Item arrived on time but smelled strongly of smoke.",
     "expected_action": "escalate", "reason": "not clearly defective"},
    {"input": "Bought 2 weeks ago, no longer fits — I lost weight.",
     "expected_action": "decline", "reason": "change of mind / fit"},
    {"input": "Box arrived damaged but the item inside is fine. Want a refund anyway.",
     "expected_action": "decline", "reason": "item not defective"},
    {"input": "I want to return because the model on the website looked better in it.",
     "expected_action": "decline", "reason": "change of mind"},
    {"input": "Shipping took 3 weeks, by then I didn't need it anymore. 35 days since order.",
     "expected_action": "escalate", "reason": "delivery delay — escalate"},
    {"input": "Are returns free? I bought $200 of stuff.",
     "expected_action": "escalate", "reason": "shipping cost question, not a return request"},
]

phoenix = Client(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

dataset = phoenix.datasets.create_dataset(
    name="refundbot-golden-v1",
    inputs=[{"question": g["input"]} for g in GOLDEN],
    outputs=[{"expected_action": g["expected_action"], "reason": g["reason"]} for g in GOLDEN],
)

print(f"✅ Created golden dataset with {len(GOLDEN)} examples")
print(f"   Dataset ID: {dataset.id}")