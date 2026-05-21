import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

# Phoenix tracing setup — MUST run before any Gemini calls
from phoenix.otel import register
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

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

# Load the policy once at startup
POLICY = Path(__file__).parent.joinpath("policy.md").read_text()

# This is the "good" prompt — RefundBot v13.
# We'll define v14 (the bad one) in Phoenix later.
SYSTEM_PROMPT_V13 = f"""You are RefundBot, the customer support assistant for NimbusCart.

You answer refund and return questions using ONLY the official NimbusCart 
refund policy provided below.

CRITICAL RULES:
- Never approve a refund outside the stated policy.
- If a request falls outside policy, politely decline and explain why.
- If unsure, say "Let me connect you with a human agent" — never guess.
- Cite the specific policy section in your answer.

--- NIMBUSCART REFUND POLICY ---
{POLICY}
"""

app = FastAPI(title="RefundBot", version="13.0")

class Question(BaseModel):
    customer_id: str
    message: str

class Answer(BaseModel):
    answer: str
    customer_id: str

@app.get("/health")
def health():
    return {"status": "ok", "version": "v13"}

@app.post("/ask", response_model=Answer)
def ask(q: Question):
    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT_V13}\n\nCustomer ({q.customer_id}): {q.message}\nRefundBot:",
    )
    return Answer(answer=response.text, customer_id=q.customer_id)