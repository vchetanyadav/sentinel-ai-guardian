import os
from google import genai

client = genai.Client(
    vertexai=True,
    project=os.environ["sentinel-hackathon-496705"],
    location="global",   # ← changed from us-central1
)

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",   # ← changed from gemini-3-pro
    contents="In one sentence, what is your model name and version?",
)

print(response.text)
