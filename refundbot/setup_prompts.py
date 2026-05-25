import os
from dotenv import load_dotenv
from phoenix.client import Client
from phoenix.client.types import PromptVersion
from prompt_content import V13_GOOD, V14_BAD

load_dotenv()

phoenix = Client(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

# Create v14 first so v13 ends up as the latest (= production)
v14 = phoenix.prompts.create(
    name="refundbot-system-prompt",
    prompt_description="RefundBot customer support system prompt",
    version=PromptVersion(
        [{"role": "system", "content": V14_BAD}],
        model_name="gemini-2.5-flash",
        description="v14-BROKEN: customer-happiness-first, over-approves",
    ),
)
print(f"Created v14 (broken)")

v13 = phoenix.prompts.create(
    name="refundbot-system-prompt",
    version=PromptVersion(
        [{"role": "system", "content": V13_GOOD}],
        model_name="gemini-2.5-flash",
        description="v13-GOOD: cautious, strict policy adherence",
    ),
)
print(f"Created v13 (good) — now the latest = production")
print("\n✅ Setup complete")