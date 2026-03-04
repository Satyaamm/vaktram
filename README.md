# Vaktram (वक्त्रम्) — The Voice

AI-powered meeting notes platform with BYOM (Bring Your Own Model) support. Record, transcribe, and summarize your meetings automatically.

## Features

- AI bot joins Google Meet / Zoom / Teams meetings
- Real-time transcription with speaker diarization
- AI-generated summaries, action items, decisions, follow-ups
- BYOM: Connect your own LLM (OpenAI, Claude, Gemini, Groq, Azure, Bedrock, etc.)
- Semantic search across all meetings
- Audio playback synced with transcript
- Calendar integration for auto-join
- Meeting analytics dashboard
- Team collaboration with shared workspaces
- Enterprise: SSO, RBAC, audit logs, API access

## Tech Stack

| Layer         | Technology                                      |
| ------------- | ----------------------------------------------- |
| Frontend      | Next.js 14, TypeScript, shadcn/ui, Tailwind CSS |
| Backend       | FastAPI, SQLAlchemy 2.0, Pydantic v2            |
| Database      | Supabase PostgreSQL + pgvector                  |
| Auth          | Supabase Auth (OAuth, magic link)               |
| LLM Router    | LiteLLM (100+ providers)                        |
| Transcription | Faster-Whisper + pyannote.audio                 |
| Bot           | Playwright + PulseAudio + FFmpeg                |
| Cache/Queue   | Upstash Redis + QStash                          |
| Monorepo      | Turborepo                                       |

## Quick Start

### Prerequisites

- Node.js >= 18
- Python >= 3.11
- Docker & Docker Compose
- A Supabase project (free tier)
- An Upstash account (free tier)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-org/vaktram.git
cd vaktram

# 2. Copy environment file and fill in your values
cp .env.example .env

# 3. Install frontend dependencies
npm install

# 4. Run with Docker Compose (all services)
docker-compose up

# OR run individual services for development:

# Frontend (http://localhost:3000)
cd apps/web && npm run dev

# Backend (http://localhost:8000)
cd apps/api && uvicorn app.main:app --reload --port 8000

# 5. Open http://localhost:3000
```

### Project Structure

```
vaktram/
├── apps/
│   ├── web/              # Next.js frontend
│   ├── api/              # FastAPI backend
│   ├── bot-service/      # Meeting bot (Playwright)
│   └── workers/
│       ├── transcription/ # Whisper + pyannote
│       └── summarizer/    # LLM summarization
├── packages/
│   ├── shared/           # Shared utilities
│   ├── db/               # Database schemas
│   └── config/           # Shared config
├── infra/                # Docker, scripts
└── docs/                 # Documentation
```

## SaaS Tiers

| Feature        | Free         | Pro       | Team      | Enterprise |
| -------------- | ------------ | --------- | --------- | ---------- |
| Meetings/month | 5            | Unlimited | Unlimited | Unlimited  |
| LLM            | Gemini Flash | BYOM      | BYOM      | BYOM       |
| Users          | 1            | 1         | 10        | Unlimited  |
| SSO/SAML       | -            | -         | -         | Yes        |
| API Access     | -            | -         | -         | Yes        |
| Audit Logs     | -            | -         | -         | Yes        |

## License

Proprietary. All rights reserved.

---

  <!-- Running the Frontend (Next.js)
cd apps/web                                               
  npm install        # first time only
  npm run dev

  Runs on http://localhost:3000

  Make sure apps/web/.env.local has your Supabase credentials (it already does).

  ---
  Running the Backend (FastAPI)

  cd apps/api
  python -m venv venv          # first time only
  source venv/bin/activate     # on macOS/Linux
  pip install -r requirements.txt  # first time only

  uvicorn app.main:app --reload --port 8000

  Runs on http://localhost:8000

  You'll need a .env file in apps/api/ with:
  SUPABASE_DB_URL=postgresql://postgres:password@db.epdymcjwgnuoojoniqwp.supabase.co:5432/postgres
  SUPABASE_JWT_SECRET=<your-jwt-secret-from-supabase-dashboard>
  GOOGLE_AI_API_KEY=<your-gemini-key>
  ENCRYPTION_KEY=<32-byte-key>

  Get the JWT secret from: Supabase Dashboard → Settings → API → JWT Secret

  ---
  Both at once (Turborepo)

  From the repo root:
  npm install       # installs all workspace deps
  npx turbo dev     # runs dev for all packages

  This starts the frontend on :3000. The backend still needs to be started separately with uvicorn since it's Python.
 -->
