import os
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

# Phoenix tracing setup — MUST run before any Gemini calls
from phoenix.otel import register
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
from phoenix.client import Client as PhoenixClient

load_dotenv()

# Register tracer with Phoenix Cloud
tracer_provider = register(
    project_name="refundbot-prod",
    endpoint=f"{os.environ['PHOENIX_ENDPOINT']}/v1/traces",
    headers={"api_key": os.environ["PHOENIX_API_KEY"]},
    auto_instrument=False,
)
GoogleGenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# Gemini client
gemini = genai.Client(
    vertexai=True,
    project=os.environ["GCP_PROJECT"],
    location="global",
)

# Phoenix client — for fetching the latest prompt version
phoenix_client = PhoenixClient(
    base_url=os.environ["PHOENIX_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

# Fallback policy if Phoenix is unreachable
POLICY = Path(__file__).parent.joinpath("policy.md").read_text()
FALLBACK_PROMPT = f"""You are RefundBot. Use ONLY this policy:\n\n{POLICY}"""

# Short cache so we don't hit Phoenix on every request, but rollback is still fast
_cache = {"text": None, "fetched_at": 0.0}
_CACHE_TTL_SECONDS = 5

def get_active_prompt() -> str:
    """Fetch the latest version of the production prompt from Phoenix."""
    now = time.time()
    if _cache["text"] and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return _cache["text"]

    try:
        prompt = phoenix_client.prompts.get(prompt_identifier="refundbot-system-prompt")
        formatted = prompt.format()
        # Phoenix returns an OpenAIPrompt object with a .messages attribute (list of dicts)
        messages = getattr(formatted, "messages", None)
        if not messages:
            raise RuntimeError(f"OpenAIPrompt had no messages; type={type(formatted).__name__}")
        text = messages[0]["content"]
        _cache["text"] = text
        _cache["fetched_at"] = now
        return text
    except Exception as e:
        print(f"⚠️  Failed to fetch prompt from Phoenix: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return _cache["text"] or FALLBACK_PROMPT


app = FastAPI(title="RefundBot", version="dynamic")


class Question(BaseModel):
    customer_id: str
    message: str


class Answer(BaseModel):
    answer: str
    customer_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/prompt")
def debug_prompt():
    """Returns what get_active_prompt() actually fetches right now."""
    text = get_active_prompt()
    return {
        "first_200_chars": text[:200],
        "length": len(text),
        "looks_like_v14": "customer happiness" in text.lower() or "always approve" in text.lower(),
        "looks_like_v13": "never approve a refund outside" in text.lower() or "critical rules" in text.lower(),
        "looks_like_fallback": text.startswith("You are RefundBot. Use ONLY this policy:"),
    }


@app.post("/ask", response_model=Answer)
def ask(q: Question):
    system_prompt = get_active_prompt()
    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\nCustomer ({q.customer_id}): {q.message}\nRefundBot:",
    )
    return Answer(answer=response.text, customer_id=q.customer_id)