import os, json, time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.environ["GCP_PROJECT"],
    location="global",
)

PROMPT = """Generate 25 realistic, varied customer refund questions for NimbusCart, 
an online clothing retailer. Include a mix of:

- Clearly within policy (worn under 30 days, defective items, wrong item shipped)
- Clearly outside policy (40+ days late, final sale items, change of mind, used items)
- Genuinely ambiguous edge cases (29 days late, "tags removed but unworn", gift returns)

Write in a natural conversational tone — these should sound like real frustrated 
or hopeful customers. Vary length from 1 sentence to 3 sentences. Include some 
typos and casual language.

Return ONLY a JSON array of strings. No commentary, no markdown, no code fences."""

questions = []
batches = 8  # 8 × 25 = 200 questions

for i in range(batches):
    print(f"Generating batch {i+1}/{batches}...")
    r = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT,
    )
    text = r.text.strip()
    # Strip any markdown code fences Gemini sometimes adds
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    batch = json.loads(text.strip())
    questions.extend(batch)
    time.sleep(2)

# Deduplicate
questions = list(dict.fromkeys(questions))

with open("synthetic_questions.json", "w") as f:
    json.dump(questions, f, indent=2)

print(f"\n✅ Saved {len(questions)} unique questions to synthetic_questions.json")