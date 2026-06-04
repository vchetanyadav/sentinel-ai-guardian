@echo off
gcloud run deploy sentinel-ui ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --clear-base-image ^
  --set-build-env-vars NEXT_PUBLIC_API_BASE=https://sentinel-api-818451736887.us-central1.run.app ^
  --memory 512Mi