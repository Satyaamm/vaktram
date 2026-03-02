# Vaktram Architecture

## Overview

Vaktram is an AI-powered meeting notetaker that joins video calls, records audio, transcribes speech with speaker diarization, and generates structured summaries with action items.

## System Architecture

```
                    +-----------------+
                    |   Next.js Web   |
                    |   (Frontend)    |
                    +--------+--------+
                             |
                    +--------v--------+
                    | FastAPI Backend  |
                    |   (REST API)    |
                    +--------+--------+
                             |
              +--------------+--------------+
              |              |              |
    +---------v---+  +-------v-------+  +--v-----------+
    | Bot Service |  | Transcription |  | Summarization|
    | (Playwright)|  |    Worker     |  |    Worker    |
    +------+------+  +-------+-------+  +------+-------+
           |                 |                  |
    +------v------+  +-------v-------+  +------v-------+
    | PulseAudio  |  | Faster-Whisper|  |   LiteLLM    |
    | + FFmpeg    |  | + pyannote    |  | + Embeddings |
    +-------------+  +---------------+  +--------------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v--------+
                    |    Supabase     |
                    | (DB + Storage)  |
                    +-----------------+
```

## Services

### 1. Web Frontend (`apps/web/`)
- **Tech**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Purpose**: User-facing dashboard for managing meetings, viewing transcripts, and searching
- **Auth**: Supabase Auth with social providers

### 2. API Backend (`apps/api/`)
- **Tech**: FastAPI (Python)
- **Purpose**: REST API for the frontend and webhook integrations
- **Key endpoints**: Meeting CRUD, transcript retrieval, semantic search, bot control

### 3. Bot Service (`apps/bot-service/`)
- **Tech**: FastAPI + Playwright + PulseAudio
- **Purpose**: Manages browser-based bots that join meetings and capture audio
- **Flow**: Receives join command -> launches Chromium -> joins meeting -> captures audio via PulseAudio virtual sink -> uploads to Supabase Storage

### 4. Transcription Worker (`apps/workers/transcription/`)
- **Tech**: Faster-Whisper (CTranslate2) + pyannote.audio
- **Purpose**: Processes audio files into speaker-attributed transcripts
- **Flow**: Polls for jobs -> downloads audio -> runs Whisper ASR -> runs pyannote diarization -> merges results -> writes to DB

### 5. Summarization Worker (`apps/workers/summarizer/`)
- **Tech**: LiteLLM + sentence-transformers
- **Purpose**: Generates meeting summaries, action items, decisions, follow-ups, and embeddings
- **Flow**: Polls for completed transcriptions -> calls LLM for summaries -> generates embeddings -> writes to DB

## Data Flow

1. User schedules a meeting or provides a join link
2. API dispatches a bot via the Bot Service
3. Bot joins the meeting, captures audio, and uploads chunks to Supabase Storage
4. When the meeting ends, a transcription job is created
5. Transcription Worker processes the audio into speaker-attributed segments
6. Summarization Worker generates structured summaries and embeddings
7. Results are available in the dashboard and via API

## Database

- **Engine**: PostgreSQL (Supabase)
- **Key tables**: organizations, meetings, transcript_segments, meeting_summaries, transcript_embeddings
- **Search**: pgvector extension for semantic similarity search
- **Security**: Row Level Security (RLS) policies for multi-tenant isolation

## Infrastructure

- **Container runtime**: Docker
- **Frontend hosting**: Vercel
- **Backend hosting**: Render / Railway / Fly.io
- **Database**: Supabase (hosted PostgreSQL)
- **Storage**: Supabase Storage (S3-compatible)
- **CI/CD**: GitHub Actions
