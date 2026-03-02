FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Environment defaults
ENV WHISPER_MODEL=large-v3
ENV COMPUTE_DEVICE=auto
ENV POLL_INTERVAL_SECONDS=5
ENV LOG_LEVEL=INFO

CMD ["python", "worker.py"]
