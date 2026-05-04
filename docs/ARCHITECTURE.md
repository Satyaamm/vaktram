# Vaktram — Architecture

Vaktram is a meeting-notes platform with **bring-your-own-model (BYOM)** for the LLM that writes the summary. This document covers service topology, request lifecycle, data model, auth, the async pipeline, and the security controls that landed in the recent hardening pass.

> **Reading order**: skim §1 for the topology, then §2 for the end-to-end flow. §3 → §9 are reference material.

---

## 1. Service Topology

| Service | Entry point | Port | Deploy target | Talks to |
|---|---|---|---|---|
| **API** | `apps/api/app/main.py:51` | 8000 | Render (Docker) | Postgres, Redis, QStash, bot, workers, Resend, Groq |
| **Dashboard + marketing** | `apps/web/src/app/layout.tsx` | 3000 | Vercel | API |
| **Bot service** | `apps/bot-service/bot/main.py:45` | 8001 | VPS Docker (`212.38.94.234`) | API (callback), Supabase Storage, Playwright/Chromium |
| **Transcription worker** | `apps/workers/transcription/worker.py` | — (poll) | Docker / Render BG / Fly | Supabase Storage, API, Groq Whisper |
| **Summarizer worker** | `apps/workers/summarizer/worker.py` | — (poll) | Docker / Render BG / Fly | Supabase, API, user's BYOM LLM |
| **Diarization** | `apps/workers/diarization/main.py` | 8002 | Docker (optional) | API, pyannote 3.1 (HF) |

**Internal call shapes**

- API → bot service: `POST /bots/start`, header `X-Bot-Auth: $BOT_SHARED_SECRET` (`apps/api/app/services/bot_service.py:30`)
- Bot/workers → API: `POST /internal/...`, same `X-Bot-Auth` header (`apps/api/app/utils/internal_auth.py:28`)
- API → QStash → API: pipeline jobs published in `apps/api/app/services/queue_service.py:40`; webhook arrives back at `/internal/pipeline/*` and is verified in `apps/api/app/utils/qstash_signature.py:74`

---

## 2. End-to-end Request Lifecycle

Trace of a single meeting from invite to searchable summary. File:line citations point at the exact code.

1. **Signup** — `POST /api/v1/auth/signup` (`apps/api/app/routers/auth.py:135`)
   creates `Organization` + `UserProfile` (`is_active=False`), bcrypt-hashes the password (`apps/api/app/utils/security.py:37`), issues a verification token (`apps/api/app/services/verification_service.py:28`), sends the email via Resend.
2. **Verify email** — `POST /api/v1/auth/verify-email` (`auth.py:218`) marks the user verified, mints an access + refresh JWT pair, sets the `vaktram_refresh` HttpOnly cookie + the `vaktram_session` non-credential hint cookie (`auth.py:60`).
3. **Connect calendar** — `POST /api/v1/calendar/authorize` returns the Google OAuth URL; the callback at `/api/v1/calendar/callback` (`apps/api/app/routers/calendar.py:55`) stores Fernet-encrypted access/refresh tokens.
4. **Calendar sync** — APScheduler runs `sync_all_calendars` every 5 min (`apps/api/app/services/meeting_scheduler.py:76`); detected meetings become `Meeting` rows with `status=scheduled`.
5. **Bot dispatch** — `scan_upcoming_meetings` (`meeting_scheduler.py:71`) every 60 s schedules a `DateTrigger` job that calls `apps/api/app/services/bot_service.py:join_meeting` → `POST {BOT_SERVICE_URL}/bots/start` with `X-Bot-Auth`.
6. **Bot joins** — `apps/bot-service/bot/main.py:89` constructs a platform-specific bot (`platforms/google_meet.py`, `zoom.py`, `teams.py`, `zoho.py`), Playwright joins, PulseAudio captures via `bot/audio/capture.py`.
7. **Audio upload** — On meeting end, `bot/audio/uploader.py:31` writes FLAC to Supabase Storage, then calls `POST /internal/meetings/{id}/audio-ready` with `X-Bot-Auth` (`apps/api/app/routers/internal.py:383`).
8. **Pipeline kickoff** — API publishes `/internal/pipeline/transcribe/{id}` to QStash (`queue_service.py:40`) which delivers a signed webhook back.
9. **Transcribe** — `pipeline_transcribe` (`internal.py:90`) runs Groq Whisper, optionally pyannote diarization, writes `TranscriptSegment` rows, then publishes `/internal/pipeline/summarize/{id}` to QStash.
10. **Summarize (BYOM)** — `pipeline_summarize` (`internal.py:218`) loads `UserAIConfig`, decrypts the API key in memory (`apps/api/app/services/encryption_service.py:30`), calls the user's chosen LLM, persists `MeetingSummary` (`apps/api/app/models/summary.py`) and per-segment embeddings.
11. **Realtime push** — every state change emits a WebSocket event on `/ws/meetings/{id}` (`apps/api/app/routers/ws.py`); the dashboard subscribes from the meeting detail page.
12. **Search** — `POST /api/v1/search` (`apps/api/app/routers/search.py`) does FTS on `transcript_segments.content` + cosine similarity on the embedding column, fused via reciprocal rank.

---

## 3. Data Model

All tables live in the `vaktram` schema. The migrations that create them are in `supabase/migrations/`.

| Model | Table | Notable columns | Purpose |
|---|---|---|---|
| `Organization` (`team.py:23`) | `organizations` | `slug`, `max_seats`, `default_retention_days` | Tenant boundary |
| `UserProfile` (`team.py:34`) | `user_profiles` | `email`, `password_hash`, `email_verified_at`, `is_active`, `organization_id` | One per human |
| `Meeting` (`meeting.py:45`) | `meetings` | `platform` (enum incl. `zoho`), `status`, `meeting_url`, `audio_url`, `bot_id` | The recording record |
| `TranscriptSegment` (`transcript.py:14`) | `transcript_segments` | `speaker_name`, `start_time`, `end_time`, `content` | Ordered turns; FTS index on `content` |
| `MeetingSummary` (`summary.py:14`) | `meeting_summaries` | `summary_text`, `action_items` (JSONB), `key_decisions` (JSONB), `model_used` | One per meeting |
| `MeetingEmbedding` | `meeting_embeddings` | `embedding` (`vector(1536)` via pgvector), `chunk_text` | Hybrid search index |
| `UserAIConfig` (`ai_config.py:14`) | `user_ai_configs` | `provider`, `model_name`, `api_key_encrypted` (Fernet) | BYOM credentials |
| `CalendarConnection` (`team.py:64`) | `calendar_connections` | `access_token_encrypted`, `refresh_token_encrypted` | Google OAuth state |
| `EmailVerificationToken` | `email_verification_tokens` | `token_hash` (sha256), `expires_at`, `used_at` | One-shot verify/reset |
| `RetentionPolicy` | `retention_policies` | `default_days`, `legal_hold` | GDPR retention |

`pgvector` is added by `supabase/migrations/00000000000002_add_pgvector.sql`. Postgres FTS uses a generated tsvector on `transcript_segments.content`.

---

## 4. Auth Model

After the security pass, the auth surface looks like this:

- **Algorithm**: HS256, pinned in `apps/api/app/utils/security.py:82`. `jwt.decode(..., algorithms=["HS256"])` — no `alg=none` confusion attacks.
- **Access token**: 15 min, in JS memory only via the Zustand `auth-store` (`apps/web/src/lib/stores/auth-store.ts`).
- **Refresh token**: 24 h, **HttpOnly + Secure + SameSite=None** cookie `vaktram_refresh`. Set by `apps/api/app/routers/auth.py:60` on signup-verify, login, refresh.
- **Refresh rotation**: Each refresh token carries a `jti` registered in Redis (`apps/api/app/services/session_service.py:38`). On `/refresh`, the old jti is revoked before a new one is issued; replay is detected and 401'd.
- **Logout**: `POST /api/v1/auth/logout` (`auth.py:419`) revokes the refresh jti and clears both cookies. Idempotent.
- **Bcrypt cost**: 12 rounds, pinned (`security.py:32`). Constant-time `dummy_verify` runs against a bogus hash on unknown-email logins (`security.py:45`) so timing doesn't leak account existence.
- **Email verification**: 32-byte URL-safe random token, only the sha256 is stored. Compare via `hmac.compare_digest` (`apps/api/app/services/verification_service.py:60`).
- **Resend rate limit**: 3 per hour per email, Redis-backed (`apps/api/app/services/session_service.py:69`).
- **Internal auth**: Every `/internal/*` and `/webhooks/bot-events` requires `X-Bot-Auth: $BOT_SHARED_SECRET` (`apps/api/app/utils/internal_auth.py:28`). HMAC-compared.
- **QStash auth**: `Upstash-Signature` JWT verified against current + next signing keys in `apps/api/app/utils/qstash_signature.py:74`. Body integrity is checked via the `body` claim (sha256 of request bytes).
- **CORS**: Validated at startup. Refuses to boot if the origin regex is `.*` while `allow_credentials=True` (`apps/api/app/middleware/cors.py:35`).
- **CSP + 5 other security headers** on the dashboard set by `apps/web/next.config.mjs`. Includes `frame-ancestors 'none'` and HSTS preload.

The Next.js middleware (`apps/web/src/middleware.ts`) only redirects already-signed-in users away from auth pages. Dashboard route gating is done client-side by `AuthBootstrap` (`apps/web/src/components/auth-bootstrap.tsx`), which calls `/auth/refresh` on mount and bounces to `/login` on 401.

---

## 5. Async Pipeline

```
audio-ready ───┐
               ▼
 [QStash] ── /internal/pipeline/transcribe ──► Groq Whisper + (opt.) pyannote
                                                       │
                                                  TranscriptSegment rows
                                                       │
                                                       ▼
                                       [QStash] ── /internal/pipeline/summarize
                                                       │
                                              UserAIConfig.decrypt() → LLM
                                                       │
                                                  MeetingSummary + embeddings
                                                       │
                                                       ▼
                                              status=completed + WS event
```

When QStash isn't configured (local dev), `queue_service.publish_job` falls through to an `asyncio.create_task` inline runner (`queue_service.py:57`). This keeps the dev flow runnable without infra. **Production refuses to boot without QStash signing keys** (`apps/api/app/utils/qstash_signature.py:84`).

---

## 6. BYOM (Bring Your Own Model)

User stores their own LLM credential per-org. Only the platform stays platform-managed.

- **Storage**: `UserAIConfig.api_key_encrypted` is Fernet-encrypted at rest (`apps/api/app/services/encryption_service.py:30`). Encryption key is `ENCRYPTION_KEY` env, validated at startup (`apps/api/app/main.py:34`).
- **Retrieval**: `_get_user_ai_config` (`apps/api/app/services/summarization_service.py:87`) fetches the active default config and decrypts in memory.
- **Routing**: `apps/api/app/services/llm_service.py` dispatches to LiteLLM-compatible providers (OpenAI, Anthropic, Gemini, Mistral, Cohere, Azure, Vertex, Groq, Bedrock, Ollama).
- **No platform LLM markup**: the request hits the user's provider directly; tokens are billed to the user's account.

The signup → verify-email → AI-config flow is wired so brand-new users land on `/settings/ai-config?from=verify` (`apps/web/src/app/(auth)/verify-email/page.tsx`) — they cannot use the platform until they configure a key.

---

## 7. Security Controls Summary

15 controls landed in the May 2026 hardening pass, every one with a citation:

| # | Control | Where |
|---|---|---|
| 1 | JWT_SECRET enforced + length-validated at startup | `config.py:51-72` |
| 2 | ENCRYPTION_KEY validated in `lifespan` | `main.py:32-37` |
| 3 | Bcrypt rounds pinned at 12 | `security.py:32` |
| 4 | Constant-time email-verification compare | `verification_service.py:58-63` |
| 5 | Constant-time login (dummy bcrypt on unknown email) | `security.py:45`, `auth.py:386` |
| 6 | File-upload extension whitelist | `routers/meetings.py:147-167` |
| 7 | CORS regex startup validation | `middleware/cors.py:35` |
| 8 | Bot service requires `X-Bot-Auth` | `bot-service/bot/main.py:39`, `internal_auth.py:28` |
| 9 | QStash signature verification | `utils/qstash_signature.py:74` |
| 10 | Refresh-token rotation + Redis revocation | `services/session_service.py`, `auth.py:333` |
| 11 | `/auth/logout` endpoint | `auth.py:419` |
| 12 | Per-email rate limit on resend-verification | `services/session_service.py:69`, `auth.py:280` |
| 13 | HttpOnly cookie auth (refresh in cookie, access in memory) | `auth.py:48-67`, `lib/stores/auth-store.ts`, `lib/api/client.ts` |
| 14 | CSP + HSTS + 4 other security headers | `apps/web/next.config.mjs` |
| 15 | Daily retention purge scheduled | `meeting_scheduler.py:121` |

---

## 8. Frontend Architecture

Next.js 14 App Router. Three route groups under `apps/web/src/app/`:

- **`(marketing)`** — public, no auth. Pages: `/`, `/product`, `/pricing`, `/customers`, `/security`, `/about`, `/contact`, `/privacy`, `/terms`. Wrapped by `(marketing)/layout.tsx` with `<SiteNav>` + `<SiteFooter>`.
- **`(auth)`** — light split-screen. `/login`, `/signup`, `/verify-email`, `/forgot-password`, `/reset-password`. The layout (`(auth)/layout.tsx`) renders the brand panel on the left and the form on the right; mobile collapses to form-only.
- **`(dashboard)`** — auth-gated. Wrapped by `<AuthBootstrap>` (`components/auth-bootstrap.tsx`), which calls `/auth/refresh` on mount and redirects to `/login` on 401.

Single Vercel deployment serves all three. The marketing site shares the dashboard's domain; CTAs link to relative `/login` and `/signup` paths.

---

## 9. Known Gaps

- **No SOC 2 attestation.** Controls are in place; the audit is targeted for Q3 2026.
- **No CI/CD for the bot.** `infra/scripts/deploy-bot-vps.sh` requires manual SSH password entry.
- **Bot CAPTCHA.** Zoho's guest-join page shows a CAPTCHA; the headless bot stalls there without a solver service hook.
- **Worker concurrency.** Polling workers don't lease jobs distributedly; running >1 instance per kind risks duplicate processing.
- **No native mobile / PWA.**
- **No data-residency enforcement** beyond the single Singapore region today; multi-region is roadmap.
- **Stripe billing wired but not end-to-end tested** in production.
