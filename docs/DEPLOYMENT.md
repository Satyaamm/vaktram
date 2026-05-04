# Vaktram — Deployment

This is the operator's guide for getting Vaktram from "fresh repo" to "running in production". Every command, env var, and surface is enumerated.

> **Topology**: Vercel (web) ↔ Render (API) ↔ Supabase (DB + Storage) ↔ Upstash (Redis + QStash) ↔ VPS (bot) ↔ Workers (optional).

## TL;DR — order of deploys

1. **Generate secrets** (locally, once)
2. **Apply DB migrations** (Supabase)
3. **Set Render env** + deploy API
4. **Set Vercel env** + deploy web (auto on push)
5. **Run the VPS bot deploy script**
6. **(Optional) deploy workers** — only if you bypass QStash

---

## 1. Generate secrets

Three secrets are required in production. Generate them once locally, store in your local `.env` AND in Render + on the VPS.

```bash
# JWT signing secret — at least 32 chars; production refuses to boot below that
echo "JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" >> .env

# Fernet key — encrypts user LLM API keys at rest
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Bot/worker shared secret — same value on API + VPS + workers
echo "BOT_SHARED_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

**Rotation** — `JWT_SECRET` rotation invalidates all in-flight tokens (forces re-login). `ENCRYPTION_KEY` rotation requires re-encrypting `user_ai_configs.api_key_encrypted`. `BOT_SHARED_SECRET` rotation requires bot redeploy + Render env update simultaneously.

---

## 2. Database (Supabase)

Project: `epdymcjwgnuoojoniqwp` in `ap-southeast-1` (Singapore). Storage bucket: `vaktram-audio`.

**Apply migrations** — every file is idempotent (safe to re-run).

```bash
psql "$DATABASE_URL" \
  -f supabase/migrations/00000000000001_init.sql \
  -f supabase/migrations/00000000000002_add_pgvector.sql \
  -f supabase/migrations/00000000000003_email_verification.sql \
  -f supabase/migrations/00000000000004_zoho_platform.sql
```

If `psql` isn't on your machine, the API venv has `asyncpg`:

```bash
apps/api/.venv/bin/python -c "
import asyncio, asyncpg, pathlib
async def main():
    conn = await asyncpg.connect('$DATABASE_URL', statement_cache_size=0)
    for f in sorted(pathlib.Path('supabase/migrations').glob('*.sql')):
        await conn.execute(f.read_text())
        print(f'applied {f.name}')
    await conn.close()
asyncio.run(main())
"
```

**Storage bucket** — create `vaktram-audio` once via the Supabase dashboard, **public=false**. The bot uses the service-role key to upload via `apps/bot-service/bot/audio/supabase_uploader.py:50`.

**Extensions** — `pgvector` is added by migration 0002. `pgcrypto` for `gen_random_uuid()` is enabled by Supabase by default.

---

## 3. API on Render

Render picks the build target automatically from `apps/api/`. The Dockerfile is `infra/docker/Dockerfile.api` (referenced in `apps/api/render.yaml` if you use Render's Blueprint).

### Required env vars

These are all read by `apps/api/app/config.py` (Pydantic Settings):

| Var | Required in prod? | Notes |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://…` (auto-rewritten if you paste plain `postgresql://`) |
| `JWT_SECRET` | ✅ — boot fails if `<32` chars | aliased as `SUPABASE_JWT_SECRET` |
| `ENCRYPTION_KEY` | ✅ — boot fails if invalid Fernet | validated in `lifespan` |
| `BOT_SHARED_SECRET` | ✅ if bot is in use | same value as VPS + workers |
| `SUPABASE_URL` | ✅ | bot/workers also need it; API uses for storage URLs |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | service role; bypasses RLS for audio bucket |
| `GROQ_API_KEY` | ✅ | Whisper transcription |
| `RESEND_API_KEY` + `RESEND_FROM_EMAIL` | ✅ | verification + invite email |
| `UPSTASH_REDIS_URL` + `UPSTASH_REDIS_TOKEN` | ✅ | rate-limit + refresh-jti revocation |
| `QSTASH_TOKEN` | ✅ | publish pipeline jobs |
| `QSTASH_CURRENT_SIGNING_KEY` + `QSTASH_NEXT_SIGNING_KEY` | ✅ | webhook signature verify; both supported for rotation |
| `BOT_SERVICE_URL` | ✅ | e.g. `http://212.38.94.234:1003` |
| `DIARIZATION_SERVICE_URL` | optional | omit and the pipeline skips diarization |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | optional | only if calendar sync is enabled |
| `STRIPE_API_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PRICE_*` | optional | billing flows |
| `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` | optional | enterprise SSO |
| `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `OTEL_EXPORTER_ENDPOINT` | optional | observability |
| `CORS_ORIGINS` | optional | comma-separated allowlist; defaults to localhost |
| `CORS_ORIGIN_REGEX` | optional | defaults to `*.vercel.app`. **Refuses to boot if set to `.*` while `allow_credentials=true`** (`middleware/cors.py:35`) |
| `RATE_LIMIT_PER_MINUTE` | optional, default `60` | per-user |
| `ENVIRONMENT` | always | set to `production` to enable strict boot guards |
| `API_BASE_URL` | always | self URL for OAuth callbacks |
| `FRONTEND_BASE_URL` | always | dashboard URL — verification email links go here |
| `REGION` + `STORAGE_BUCKET` | optional | defaults `us-east-1` + `vaktram-audio` |
| `DEFAULT_RETENTION_DAYS` | optional | default `365`, overridable per-org |

### Build + run

The default Render service type is **Docker** with a build trigger from GitHub:

- **Build command** (Render uses Dockerfile, no override needed)
- **Start command** — set in Dockerfile: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2`
- **Health check path** — `/health` (200 OK = healthy; 30 s interval, 5 s timeout)

### Startup behaviour

`apps/api/app/main.py:21` runs the lifespan context, which:

1. Validates `ENCRYPTION_KEY` (creates a `Fernet(key)` — fails fast if malformed)
2. Starts APScheduler + registers recurring jobs (`apps/api/app/services/meeting_scheduler.py:71-133`):
   - `scan_upcoming_meetings` every 60 s — dispatches bots
   - `sync_all_calendars` every 5 min
   - `cleanup_old_jobs` every 24 h
   - `retry_pending_webhooks` every 1 min
   - `selector_health_check` every 7 days
   - `run_retention_purge` every 24 h — GDPR retention enforcement

### Redeploy

Push to `main` → GitHub webhook → Render rebuilds + deploys. Verify with `curl https://vaktram-api.onrender.com/health`.

---

## 4. Web (Vercel)

Single Vercel project at the root directory `apps/web`. Hosts marketing routes (`/`, `/pricing`, …), auth (`/login`, `/signup`, …), and dashboard (`/dashboard`, `/meetings`, …) on the same origin.

### Env vars

| Var | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://vaktram-api.onrender.com` (or local) |
| `NEXT_PUBLIC_APP_URL` | `https://vaktram-web.vercel.app` (the dashboard's own URL) |
| `NEXT_PUBLIC_WEBSITE_URL` | same as APP_URL while marketing + dashboard share a deploy |
| `NEXT_PUBLIC_CONTACT_ENDPOINT` | optional — POST target for the contact form. Falls back to `mailto:hello@vaktram.com` |
| `NEXT_PUBLIC_SITE_URL` | optional — used in OG metadata, defaults to `VERCEL_URL` |

Set scope to **Production, Preview, Development** unless preview deploys should target a staging API.

### Security headers

Configured in `apps/web/next.config.mjs:29-58`:

- `Content-Security-Policy` with `frame-ancestors 'none'`, `object-src 'none'`, no third-party script hosts
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=(), interest-cohort=()`

### Build + deploy

Auto on push. The Vercel CLI works too:

```bash
cd apps/web
npx vercel deploy --prod
```

### Verify

- `https://vaktram-web.vercel.app/` → marketing home
- Sign in/Start free CTAs → `/login`, `/signup`
- After login → `/dashboard`
- Sign-out clears cookies + revokes refresh

---

## 5. Bot service (VPS)

Target: VPS at `212.38.94.234`. Deploy via the one-shot script.

### Required local env (in your repo's `.env`)

```bash
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co     # forwarded as SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=sb_secret_…
BOT_SHARED_SECRET=<same value as on Render API>
```

### Deploy

```bash
bash infra/scripts/deploy-bot-vps.sh
```

What it does (`infra/scripts/deploy-bot-vps.sh`):

1. SSH to `root@212.38.94.234` (prompts for password)
2. Installs Docker if missing
3. Clones (or hard-resets) the repo at `/opt/vaktram`
4. Writes `apps/bot-service/.env` (root-owned, 0600) with: `API_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `BOT_SHARED_SECRET`, `STORAGE_BUCKET=vaktram-audio`, `HEADLESS=true`, `BOT_MAX_DURATION_SEC=10800`, `BOT_END_CHECK_INTERVAL_SEC=10`, `REGION=ap-southeast-1`, `BOT_SERVICE_PORT=1003`
5. Stops + removes the existing `vaktram-bot` container
6. Removes the previous `vaktram-bot:latest` image
7. Prunes dangling Docker layers
8. Builds `--no-cache --pull` (3-5 min)
9. Runs the new container (`--restart unless-stopped`, port 1003)
10. Polls `http://localhost:1003/health` for up to 45 s; on success, prints status; on failure, dumps the last 50 log lines

### Verify externally

```bash
curl http://212.38.94.234:1003/health
# Expected: {"status":"healthy","active_bots":0,"version":"0.1.0"}
```

If you get connection-refused, open the firewall:

```bash
ssh root@212.38.94.234 'ufw allow 1003/tcp'
```

### After bot is up

- Render API → confirm `BOT_SERVICE_URL=http://212.38.94.234:1003` and `BOT_SHARED_SECRET=<value>` are set, redeploy if changed.
- Schedule a Google Meet to validate end-to-end.

---

## 6. Workers (optional)

Workers are an alternative to the inline + QStash pipeline. With QStash configured, you don't need standalone workers — the API runs each pipeline stage on QStash-delivered webhooks. Workers exist for:

- **Higher throughput**: parallelise transcription across multiple machines
- **GPU-bound diarization**: pyannote runs faster on a CUDA host
- **Self-hosted Whisper**: replace Groq with local `faster-whisper`

### Transcription worker (`apps/workers/transcription/worker.py`)

- Polls `meetings` table for `status='transcribing'` every `POLL_INTERVAL_SECONDS` (default 5)
- Env: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `API_URL`, `BOT_SHARED_SECRET`, `AUDIO_STORAGE_BUCKET`, `WHISPER_MODEL` (default `large-v3`), `COMPUTE_DEVICE`
- Posts back to `POST /internal/meetings/{id}/transcription-complete` with `X-Bot-Auth`

### Summarizer worker (`apps/workers/summarizer/worker.py`)

- Polls for `status='summarizing'` every 10 s
- Env: same as transcription + `ENCRYPTION_KEY` (decrypt user keys), `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL`, `DEFAULT_LLM_API_KEY`

### Diarization service (`apps/workers/diarization/main.py`)

- FastAPI on port 8002 with `POST /diarize`
- Env: `HF_TOKEN`, `DIARIZATION_MODEL` (default `pyannote/speaker-diarization-3.1`)
- Heavy: requires GPU or 16 GB RAM

> ⚠️ **Concurrency caveat**: workers don't lease jobs distributedly. Running >1 instance per kind risks duplicate processing.

---

## 7. Upstash (Redis + QStash)

Both services share an Upstash account.

### Redis

Used for: rate limiting, refresh-token jti revocation list (`session_service`), per-email rate limit on resend-verification.

- `UPSTASH_REDIS_URL` = `https://<id>.upstash.io`
- `UPSTASH_REDIS_TOKEN` = REST token

If absent, rate-limit middleware silently noop's (`apps/api/app/main.py:57-60`) — fine for local dev, **never deploy prod without it**.

### QStash

Used for: pipeline jobs (`/internal/pipeline/transcribe/{id}` and `/internal/pipeline/summarize/{id}`).

- `QSTASH_TOKEN` — publish jobs
- `QSTASH_CURRENT_SIGNING_KEY` + `QSTASH_NEXT_SIGNING_KEY` — verify webhook signatures

When QStash signing keys are missing in `production`, **the API refuses to boot** (`apps/api/app/utils/qstash_signature.py:84`).

---

## 8. Email (Resend) + Transcription (Groq)

| Service | Env | Free tier |
|---|---|---|
| Resend | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | 100 emails/day |
| Groq | `GROQ_API_KEY` | 10 hr/day Whisper |

Resend `from` defaults to `no-reply@vaktram.com` (`apps/api/app/config.py:126`).

---

## 9. Verification checklist

After every fresh deploy:

- [ ] `curl https://vaktram-api.onrender.com/health` → `{"status":"ok"}`
- [ ] `curl https://vaktram-api.onrender.com/healthz` → `{"status":"ok","database":"connected"}`
- [ ] `curl http://212.38.94.234:1003/health` → bot healthy
- [ ] Browse to `https://vaktram-web.vercel.app/` → marketing renders
- [ ] Sign up → verification email received → click link → land on `/settings/ai-config?from=verify`
- [ ] Add a BYOM key → save → AI config status flips to `configured: true`
- [ ] Schedule a Google Meet → bot dispatches → audio captured → transcript + summary land

If any step fails, the relevant sub-system is the suspect: `/health` for the API, `/healthz` for the DB, `:1003/health` for the bot, the dashboard for the frontend.

---

## 10. Roll-back

- **API/web**: redeploy a prior commit on Render/Vercel via their UI
- **DB migrations**: forward-only by design; the migrations are idempotent but not reversible. Restore from Supabase's automatic daily backup if you need to undo.
- **Bot**: re-run `infra/scripts/deploy-bot-vps.sh` after `git checkout` of a prior tag

---

## 11. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| API 500 on startup with `ENCRYPTION_KEY` error | Key not set or malformed Fernet | Generate via `Fernet.generate_key()` |
| API boots but `/login` returns 401 even with right credentials | `JWT_SECRET` differs across replicas / restarts | Ensure same value across all instances |
| Bot returns 401 on every dispatch | `BOT_SHARED_SECRET` mismatch | Set same value on Render API + VPS `.env`, redeploy both |
| QStash webhooks return 401 | Signing keys missing or wrong | Set `QSTASH_CURRENT_SIGNING_KEY` + `_NEXT_SIGNING_KEY` |
| `verify-email` link 404s | `FRONTEND_BASE_URL` points at the wrong host | Set on Render to your real Vercel URL |
| Build fails on Vercel with `unused-vars` | A removed import wasn't cleaned up | Run `npm run build` locally before pushing |
| `Failed to compile.` on bot deploy script | Stale `.next` from a previous run | Script runs `--no-cache`; if Docker disk is full, `docker system prune -af` on the VPS |
