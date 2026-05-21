from google import genai

client = genai.Client(
    vertexai=True,
    project="sentinel-hackathon-496705",
    location="global",
)

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="In one sentence, what is your model name and version?",
)

print(response.text)