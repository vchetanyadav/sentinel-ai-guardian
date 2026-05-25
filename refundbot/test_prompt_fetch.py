import os, json
from dotenv import load_dotenv
from phoenix.client import Client

load_dotenv()

phoenix = Client(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

print("Calling phoenix.prompts.get(prompt_identifier='refundbot-system-prompt')...")
try:
    prompt = phoenix.prompts.get(prompt_identifier="refundbot-system-prompt")
    print(f"✅ Got prompt object: type={type(prompt).__name__}")
    print(f"   Available methods/attrs: {[a for a in dir(prompt) if not a.startswith('_')]}")
    print()
    
    print("Calling prompt.format()...")
    try:
        formatted = prompt.format()
        print(f"✅ format() returned: type={type(formatted).__name__}")
        if isinstance(formatted, dict):
            print(f"   Keys: {list(formatted.keys())}")
            print(f"   Full output:")
            print(json.dumps(formatted, indent=2, default=str)[:2000])
        else:
            print(f"   Value (first 500 chars): {str(formatted)[:500]}")
    except Exception as e:
        print(f"❌ format() failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ prompts.get() failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()