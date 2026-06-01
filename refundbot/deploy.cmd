@echo off
gcloud run deploy refundbot ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars GCP_PROJECT=sentinel-hackathon-496705,PHOENIX_ENDPOINT=https://app.phoenix.arize.com/s/chetany009 ^
  --set-secrets PHOENIX_API_KEY=phoenix-api-key:latest ^
  --memory 1Gi ^
  --timeout 300