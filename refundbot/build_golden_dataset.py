import os
from dotenv import load_dotenv
from phoenix.client import Client

load_dotenv()

# 30 hand-crafted question/expected-action pairs
GOLDEN = [
    # Should DECLINE
    {"input": "Can I return these shoes I wore for 45 days? Just don't like them.", "expected_action": "decline"},
    {"input": "I want to return this final-sale swimsuit, I changed my mind.", "expected_action": "decline"},
    {"input": "These earrings don't suit me, can I get my money back?", "expected_action": "decline"},
    {"input": "I bought this dress 50 days ago and want to return it.", "expected_action": "decline"},
    {"input": "Can I get a partial refund? Just want $10 back as a goodwill gesture.", "expected_action": "decline"},
    {"input": "I bought underwear and want to return it unopened, original tags on.", "expected_action": "decline"},
    {"input": "I wore these jeans once and they pinched. Return them after 35 days?", "expected_action": "decline"},
    {"input": "Can I exchange this for store credit instead of a refund?", "expected_action": "decline"},
    {"input": "Got this hoodie on 60% off sale. Don't like the color, want to return.", "expected_action": "decline"},
    {"input": "Returning this t-shirt, lost the tags but it's unworn. 25 days since delivery.", "expected_action": "decline"},
    {"input": "Bought 2 weeks ago, no longer fits — I lost weight.", "expected_action": "decline"},
    {"input": "Box arrived damaged but item inside is fine. Want a refund anyway.", "expected_action": "decline"},
    {"input": "I want to return because the model on the website looked better.", "expected_action": "decline"},
    # Should APPROVE
    {"input": "My dress arrived torn out of the package, can I get a full refund?", "expected_action": "approve"},
    {"input": "You sent me a size large instead of medium. Want a refund.", "expected_action": "approve"},
    {"input": "Item delivered yesterday, never worn, tags on, want to return.", "expected_action": "approve"},
    {"input": "Got my jacket 20 days ago, never wore it. Return it?", "expected_action": "approve"},
    {"input": "This sweater has a hole in the seam. I want a refund.", "expected_action": "approve"},
    {"input": "Defective zipper on the pants I got 60 days ago. Photos attached.", "expected_action": "approve"},
    {"input": "Ordered black pants, you sent navy. Sending them back.", "expected_action": "approve"},
    {"input": "Tags still on, unworn, 5 days since I got it. Want to return.", "expected_action": "approve"},
    {"input": "Shoes arrived with one shoe a different size than the other.", "expected_action": "approve"},
    {"input": "The seam on this dress started unraveling after one wash. Bought 70 days ago.", "expected_action": "approve"},
    {"input": "Exactly 30 days since delivery, unworn shirt — can I return?", "expected_action": "approve"},
]

phoenix = Client(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

# Phoenix expects two parallel lists: inputs and outputs (one per example)
inputs = [{"question": g["input"]} for g in GOLDEN]
outputs = [{"expected_action": g["expected_action"]} for g in GOLDEN]

dataset = phoenix.datasets.create_dataset(
    name="refundbot-golden-v1",
    inputs=inputs,
    outputs=outputs,
)

print(f"✅ Created golden dataset 'refundbot-golden-v1'")
print(f"   {len(GOLDEN)} examples")