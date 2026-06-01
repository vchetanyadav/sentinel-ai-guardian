FROM python:3.11-slim

WORKDIR /app

# Install deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Cloud Run injects PORT; default to 8080 locally
ENV PORT=8080
CMD exec uvicorn app:app --host 0.0.0.0 --port $PORT