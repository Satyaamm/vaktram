FROM python:3.11-slim-bookworm

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies: Chrome, PulseAudio, FFmpeg, and audio tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    ca-certificates \
    pulseaudio \
    ffmpeg \
    libasound2 \
    libnss3 \
    libxss1 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    fonts-liberation \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN playwright install chromium && playwright install-deps chromium

# Copy PulseAudio config
COPY pulseaudio.conf /etc/pulse/default.pa

# Copy application code
COPY bot/ bot/

# Create directories for audio chunks
RUN mkdir -p /tmp/vaktram/audio

# PulseAudio environment
ENV PULSE_SERVER=unix:/tmp/pulseaudio.socket
ENV HEADLESS=true
ENV BOT_SERVICE_PORT=8100

EXPOSE 8100

# Start PulseAudio daemon, then the bot service
CMD ["sh", "-c", "pulseaudio --daemonize --system --disallow-exit --disallow-module-loading=false && uvicorn bot.main:app --host 0.0.0.0 --port ${BOT_SERVICE_PORT}"]
