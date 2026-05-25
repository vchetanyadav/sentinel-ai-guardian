import os
from dotenv import load_dotenv
import httpx

load_dotenv()

api_key = os.environ.get("PHOENIX_API_KEY", "")
endpoint = os.environ.get("PHOENIX_ENDPOINT", "https://app.phoenix.arize.com")

print("=" * 60)
print("Environment check")
print("=" * 60)
print(f"Endpoint: {repr(endpoint)}")
print(f"API key length: {len(api_key)}")
print(f"Key starts with: {api_key[:8]}...")
print(f"Key ends with:   ...{api_key[-4:]}")
print(f"Key has spaces:  {' ' in api_key}")
print(f"Key has quotes:  {chr(34) in api_key or chr(39) in api_key}")
print()

# Test 1: api-key header (Phoenix Cloud auth)
print("=" * 60)
print("Test 1: 'api-key' header (Phoenix Cloud standard)")
print("=" * 60)
try:
    r = httpx.get(f"{endpoint}/v1/prompts", headers={"api-key": api_key}, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Body:   {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 2: Bearer header (default client behavior)
print("=" * 60)
print("Test 2: 'Authorization: Bearer' header")
print("=" * 60)
try:
    r = httpx.get(f"{endpoint}/v1/prompts", headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Body:   {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test 3: Check what setup_prompts.py is *actually* doing
print("=" * 60)
print("Test 3: Inspect setup_prompts.py")
print("=" * 60)
try:
    with open("setup_prompts.py", "r") as f:
        content = f.read()
    # Find the Client(...) call
    if "headers=" in content and "api-key" in content:
        print("✅ setup_prompts.py contains headers={'api-key': ...}")
    elif "api_key=" in content:
        print("❌ setup_prompts.py still uses api_key= (the broken pattern)")
        print("    Find the Client(...) call and change to headers={'api-key': ...}")
    else:
        print("⚠️  Could not detect auth pattern in setup_prompts.py")
except Exception as e:
    print(f"Error reading setup_prompts.py: {e}")