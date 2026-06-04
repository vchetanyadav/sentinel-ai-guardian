@echo off
gcloud run deploy sentinel-api ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --clear-base-image ^
  --set-env-vars GCP_PROJECT=sentinel-hackathon-496705,GCP_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=sentinel-hackathon-496705,GOOGLE_CLOUD_LOCATION=global,PHOENIX_ENDPOINT=https://app.phoenix.arize.com/s/chetany009,REFUNDBOT_URL=https://refundbot-818451736887.us-central1.run.app ^
  --set-secrets PHOENIX_API_KEY=phoenix-api-key:latest ^
  --memory 2Gi ^
  --cpu 2 ^
  --timeout 600