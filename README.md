# Vaktram

> **AI meeting notes on the model you choose.** Vaktram joins your Google Meet, Zoom, Teams, and Zoho calls, transcribes them, and summarises with **your** LLM provider — Gemini, OpenAI, Claude, Mistral, anything LiteLLM-compatible. Your keys, your data, your spend.

[![Deploy: Vercel](https://img.shields.io/badge/web-vaktram--web.vercel.app-black?logo=vercel)](https://vaktram-web.vercel.app)
[![Deploy: Render](https://img.shields.io/badge/api-render-46e3b7?logo=render)](https://render.com)
[![Built in](https://img.shields.io/badge/built%20in-India-fb923c)](#)

---

## Why Vaktram

Every other meeting notetaker ships with a bundled LLM — you live with the vendor's choice, paying their margin, on their region. Vaktram is the opposite: **the platform stays platform-managed, the model stays yours**. Bring an API key for any LiteLLM-compatible provider; we route around it.

**At a glance**

- 🧠 **Bring your own model** — OpenAI, Anthropic, Gemini, Mistral, Cohere, Azure, Vertex, Groq, Bedrock, Ollama
- 🤖 **Self-hosted bot** — Playwright captures Meet/Zoom/Teams/Zoho on your VPS; audio never touches a third-party recorder
- 🔍 **Hybrid search** — Postgres FTS + pgvector cosine, RRF-fused
- 🔐 **Hardened** — JWT-rotation, HttpOnly refresh cookies, X-Bot-Auth on every internal call, QStash signature verification, CSP + HSTS preload
- 🌏 **Region-pinned** — Singapore today, EU + US ready
- 🧾 **GDPR retention** scheduled daily

---

## Repo layout

```
vaktram/
├── apps/
│   ├── api/                 # FastAPI backend (Render)
│   │   ├── app/
│   │   │   ├── routers/     # 25 routers, ~135 endpoints
│   │   │   ├── services/    # Business logic (auth, billing, queue, BYOM, …)
│   │   │   ├── models/      # SQLAlchemy 2.0 async models
│   │   │   ├── schemas/     # Pydantic request/response shapes
│   │   │   ├── utils/       # security, qstash_signature, internal_auth
│   │   │   └── middleware/  # cors, rate_limit, request_context
│   │   └── requirements.txt
│   ├── web/                 # Next.js 14 dashboard + marketing (Vercel)
│   │   └── src/app/
│   │       ├── (marketing)/ # Public pages (/, /pricing, /security, …)
│   │       ├── (auth)/      # /login, /signup, /verify-email, …
│   │       └── (dashboard)/ # /dashboard, /meetings, /settings, …
│   ├── bot-service/         # Playwright bot (VPS Docker)
│   │   └── bot/
│   │       └── platforms/   # google_meet, zoom, teams, zoho
│   └── workers/
│       ├── transcription/   # Groq Whisper (or faster-whisper)
│       ├── summarizer/      # User's BYOM LLM
│       └── diarization/     # pyannote 3.1 (FastAPI sidecar)
├── docs/
│   ├── ARCHITECTURE.md      # service map, data model, security controls
│   ├── API.md               # every endpoint, every error
│   └── DEPLOYMENT.md        # Render + Vercel + VPS, env vars, secrets
├── infra/
│   ├── docker/              # Dockerfile.api, Dockerfile.bot
│   └── scripts/
│       └── deploy-bot-vps.sh
└── supabase/
    └── migrations/          # Idempotent .sql files
```

---

## Quick start (local dev)

```bash
# 1. Clone + install
git clone https://github.com/Satyaamm/vaktram.git
cd vaktram

# 2. Bootstrap env
cp .env.example .env
# generate secrets and paste into .env (see docs/DEPLOYMENT.md §1)

# 3. Apply DB migrations (assumes Supabase project + DATABASE_URL)
psql "$DATABASE_URL" -f supabase/migrations/00000000000001_init.sql
# repeat for 0002, 0003, 0004 — all idempotent

# 4. Run the API (terminal 1)
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. Run the dashboard (terminal 2)
cd apps/web
npm install
npm run dev   # http://localhost:3000

# 6. (optional) Run the bot locally — needs Playwright + PulseAudio
cd apps/bot-service
pip install -r requirements.txt
python -m bot.main  # http://localhost:1003
```

The dev pipeline falls back to inline async tasks when QStash isn't configured — fine for solo dev. **Production refuses to boot without QStash signing keys**.

---

## Production deploy

The complete operator's guide is at [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Short version:

| Surface | Where | Trigger |
|---|---|---|
| API | Render (Docker) | push to `main` |
| Dashboard + marketing | Vercel | push to `main` |
| Bot | VPS at `212.38.94.234` | `bash infra/scripts/deploy-bot-vps.sh` |
| DB | Supabase (Singapore) | `psql -f migrations/*.sql` |
| Workers (optional) | Render BG / Docker / Fly | per-target |

---

## How it works (60 seconds)

```
   Calendar invite
        │
   APScheduler ── dispatches ──► Bot service (VPS, Playwright)
                                       │
                            joins Meet/Zoom/Teams/Zoho
                                       │
                            captures audio → Supabase Storage
                                       │
                                  POST /audio-ready (X-Bot-Auth)
                                       │
                            QStash ── /pipeline/transcribe ──► Groq Whisper + pyannote
                                                                       │
                                                            TranscriptSegment[]
                                                                       │
                                                  QStash ── /pipeline/summarize ──► User's LLM (BYOM)
                                                                                                │
                                                                                  MeetingSummary + embeddings
                                                                                                │
                                                                                ───► WebSocket push to dashboard
```

Full lifecycle with file:line citations is in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## API at a glance

~135 endpoints across 25 routers. Auth tiers:

- `JWT (user)` — most dashboard-facing endpoints
- `X-Bot-Auth` — internal callers (bot, workers) → API
- `Upstash-Signature` — QStash → API pipeline webhooks
- `SCIM Bearer` — IDP-driven user provisioning
- `Stripe-Signature` — billing webhooks
- `public` — auth flows, health checks, OAuth callbacks, soundbite shares
- `WebSocket` — `/ws/meetings/{id}` for real-time pipeline status

Complete reference: [`docs/API.md`](docs/API.md).

---

## Security posture

15 controls from the May 2026 hardening pass, every one with a citation. The full list lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#7-security-controls-summary). Highlights:

- **JWT** HS256 pinned, 15 min access + 24 h refresh with rotation
- **Refresh tokens** in `HttpOnly + Secure + SameSite=None` cookie; **access tokens** in JS memory only
- **Bcrypt** rounds=12 with constant-time `dummy_verify` on unknown email (no timing-based account enumeration)
- **Bot service** behind `X-Bot-Auth` shared secret; constant-time HMAC compare
- **QStash webhooks** verified against current + next signing keys
- **Per-email rate limit** of 3/hour on resend-verification
- **CSP** with `frame-ancestors 'none'`, HSTS preload, `Permissions-Policy` denying camera/mic/geolocation
- **Daily retention purge** scheduled (GDPR Art. 5(1)(e))

---

## Tech stack

**Backend** — FastAPI 0.115, SQLAlchemy 2.0 async, Pydantic v2, Postgres 16 (+ pgvector + FTS), Upstash Redis + QStash, Resend, Groq Whisper, pyannote 3.1, APScheduler.

**Frontend** — Next.js 14 App Router, React 18, Tailwind, Zustand, TanStack Query, shadcn/ui.

**Bot** — Python 3.11, Playwright/Chromium, PulseAudio, FFmpeg, Docker.

**Infra** — Render (API), Vercel (web), Supabase (DB + Storage), VPS (bot), Docker (workers, optional).

---

## Honest gaps

- **No SOC 2 yet.** Targeting Q3 2026.
- **No CI/CD for the bot** — `deploy-bot-vps.sh` requires manual SSH password entry.
- **Zoho join** has a CAPTCHA wall; the headless bot stalls there without a solver service.
- **Worker concurrency** doesn't lease jobs distributedly — run one instance per kind.
- **Stripe billing** is wired but not end-to-end production-tested.
- **Single region** today; multi-region is roadmap.

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — service topology, request lifecycle, data model, auth, async pipeline, BYOM, security controls
- [`docs/API.md`](docs/API.md) — every endpoint with auth, request, response, error contract, and side effects
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Render + Vercel + VPS + Supabase + Upstash deploy guide, env vars, secrets, verification checklist

---

## License

Private repo. Source code is closed; documentation patterns may be reused with attribution.

---

## Maintainers

Built and maintained by **Satyam Pathak** ([@Satyaamm](https://github.com/Satyaamm)).
