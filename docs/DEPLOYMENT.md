# Vaktram Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+
- Supabase account (or local Supabase CLI)
- OpenAI API key (or other LLM provider)
- Hugging Face token (for pyannote diarization model)

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/vaktram.git
cd vaktram
bash infra/scripts/setup.sh
```

### 2. Configure Environment

Edit `.env` with your credentials:

```bash
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=your-key
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
```

### 3. Start Supabase

```bash
npx supabase start
bash infra/scripts/seed-db.sh
```

### 4. Start Services

Terminal 1 - API:
```bash
cd apps/api
uvicorn main:app --reload --port 8000
```

Terminal 2 - Bot Service:
```bash
cd apps/bot-service
uvicorn bot.main:app --reload --port 8100
```

Terminal 3 - Transcription Worker:
```bash
cd apps/workers/transcription
python worker.py
```

Terminal 4 - Summarization Worker:
```bash
cd apps/workers/summarizer
python worker.py
```

Terminal 5 - Frontend:
```bash
cd apps/web
npm run dev
```

### 5. Download ML Models

```bash
bash infra/scripts/download-models.sh
```

## Docker Deployment

### Build All Images

```bash
docker build -f infra/docker/Dockerfile.api -t vaktram-api .
docker build -f infra/docker/Dockerfile.bot -t vaktram-bot .
docker build -f infra/docker/Dockerfile.transcription -t vaktram-transcription .
docker build -f infra/docker/Dockerfile.summarizer -t vaktram-summarizer .
docker build -f infra/docker/Dockerfile.web -t vaktram-web .
```

### Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    image: vaktram-api
    ports:
      - "8000:8000"
    env_file: .env

  bot-service:
    image: vaktram-bot
    ports:
      - "8100:8100"
    env_file: .env
    privileged: true  # required for PulseAudio

  transcription-worker:
    image: vaktram-transcription
    env_file: .env
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]  # optional: GPU acceleration

  summarizer-worker:
    image: vaktram-summarizer
    env_file: .env

  web:
    image: vaktram-web
    ports:
      - "3000:3000"
    env_file: .env
```

## Production Deployment

### Frontend (Vercel)

1. Connect your GitHub repo to Vercel
2. Set root directory to `apps/web`
3. Configure environment variables in Vercel dashboard
4. Deploy triggers automatically on push to `main`

### Backend API (Render)

1. Create a new Web Service on Render
2. Use `infra/docker/Dockerfile.api` as the Dockerfile
3. Set environment variables
4. Configure health check: `GET /health`

### Bot Service (Dedicated Server)

The bot service requires PulseAudio and a display server. Deploy on:
- A dedicated VM (e.g., AWS EC2, GCP Compute Engine)
- A container service that supports privileged containers

### Workers (Background Services)

Deploy as background workers on Render, Railway, or as Kubernetes jobs:
- Transcription worker benefits from GPU (NVIDIA T4 or better)
- Summarization worker is CPU-only (API calls to LLM)

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `OPENAI_API_KEY` | Yes | OpenAI API key for summarization |
| `HF_TOKEN` | Yes | Hugging Face token for pyannote |
| `LLM_MODEL` | No | LLM model name (default: gpt-4o-mini) |
| `WHISPER_MODEL` | No | Whisper model size (default: large-v3) |
| `COMPUTE_DEVICE` | No | auto, cpu, or cuda |
| `BOT_SERVICE_PORT` | No | Bot service port (default: 8100) |
| `MAX_CONCURRENT_BOTS` | No | Max simultaneous bots (default: 10) |
