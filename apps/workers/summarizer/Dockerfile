FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Environment defaults
ENV LLM_MODEL=gpt-4o-mini
ENV LLM_TEMPERATURE=0.3
ENV POLL_INTERVAL_SECONDS=10
ENV LOG_LEVEL=INFO

CMD ["python", "worker.py"]
