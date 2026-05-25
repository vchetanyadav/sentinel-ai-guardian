import os, sys
from dotenv import load_dotenv
from phoenix.client import Client
from phoenix.client.types import PromptVersion
from prompt_content import CONTENTS

load_dotenv()

phoenix = Client(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

def deploy(label: str):
    if label not in CONTENTS:
        raise SystemExit(f"Unknown '{label}'. Use 'v13' or 'v14'.")
    
    new_version = phoenix.prompts.create(
        name="refundbot-system-prompt",
        version=PromptVersion(
            [{"role": "system", "content": CONTENTS[label]}],
            model_name="gemini-2.5-flash",
            description=f"Deployment of {label} content",
        ),
    )
    print(f"✅ Deployed {label} as new latest version")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inject_regression.py <v13|v14>")
        sys.exit(1)
    deploy(sys.argv[1])