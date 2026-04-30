# Vaktram — System Architecture

Vaktram is an AI meeting-intelligence platform. A bot joins your video calls
(Meet, Zoom, Teams), records audio, transcribes with speaker diarization,
generates structured summaries, and makes everything searchable + queryable.
The differentiator is **BYOM (Bring Your Own Model)** — users plug in their
own OpenAI / Anthropic / Gemini / Groq key, so per-user cost scales with the
LLM provider directly, not us.

## Product surface

| Capability | Vaktram surface | Status |
|---|---|---|
| Bot joins Meet / Zoom / Teams | `apps/bot-service/bot/platforms/*` | ✅ all three |
| Audio transcription | Groq Whisper API (chunked) | ✅ post-call; live = roadmap |
| Speaker diarization | pyannote.audio worker | ✅ |
| Auto-generated summary, action items, decisions | LLM via BYOM | ✅ |
| Search across meetings | Postgres FTS + pgvector RRF | ✅ |
| **Ask (Vakta)** — chat with your meetings | `/api/v1/ask` (RAG over embeddings) | ✅ |
| **Topic Tracker** — keyword alerts across all calls | `topic_trackers` table + scanner | ✅ |
| **Soundbites** — clip + share short audio segments | `soundbites` table | ✅ |
| **Channels** — shared meeting workspaces | `channels` table | ✅ |
| CRM / Slack / Notion / Asana sync | webhook + per-integration adapters | partial |
| Talk-time + sentiment analytics | analytics router | partial |
| Mobile / desktop apps | — | future |
| Live in-call assistance | — | future |

## High-level system

```
                            ┌──────────── USER ────────────┐
                            │ Web (Next.js / Vercel)       │
                            │ Mobile (React Native, later) │
                            └──────────────┬───────────────┘
                                           │ HTTPS + WebSocket
                                           ▼
                  ┌─────────────────── API ────────────────────┐
                  │ FastAPI on Fly.io (auto-scale, scale-to-1) │
                  │ Auth · Billing · Quota · Audit · SSO/SCIM  │
                  └────┬─────────────────────────────────┬─────┘
                       │                                 │
                       │ Calendar OAuth, scheduler       │ /ask, /search,
                       │ pulls events every 60s          │ /topics, /soundbites
                       ▼                                 ▼
            ┌────────────────────┐               ┌──────────────────┐
            │ Google / MS / Apple│               │ Hybrid retriever │
            │ Calendar APIs      │               │ FTS + pgvector   │
            └────────────────────┘               │ + RRF fusion     │
                       │                         └──────────────────┘
                       │ at T-2min                     │
                       ▼                               ▼
            ┌────────────────────┐               ┌──────────────────┐
            │ Bot orchestrator   │               │ Vakta (Ask) RAG  │
            │ Fly Machines       │               │ LLM via BYOM key │
            │ 1 pod per meeting  │               │ — answer + cites │
            └─────────┬──────────┘               └──────────────────┘
                      │ Playwright Chromium + PulseAudio
                      ▼
        ┌─────── Meeting platforms ────────┐
        │  Google Meet · Zoom · Teams      │
        └────────────────┬─────────────────┘
                         │ FLAC chunks
                         ▼
            ┌────────────────────────┐
            │  Cloudflare R2 (S3)    │  ◄── 10 GB free, zero egress
            │  region/org/{id}/...   │
            └───────────┬────────────┘
                        │ /audio-ready
                        ▼
        ┌──── Pipeline (QStash or inline) ────┐
        │ 1. transcribe — Groq Whisper        │
        │ 2. diarize — Modal serverless GPU   │
        │ 3. merge speakers + segments        │
        │ 4. summarize — BYOM LLM (LiteLLM)   │
        │ 5. embed — OpenAI text-embed-3-small│
        │ 6. topic-scan — keyword matcher     │
        │ 7. notify — Resend + WS broadcast   │
        └─────────────┬───────────────────────┘
                      ▼
        ┌────────────────────────────┐
        │ Supabase Postgres          │
        │ + pgvector + FTS GIN       │
        │ + RLS for multi-tenant     │
        └────────────────────────────┘

  Cross-cutting:
   • Upstash Redis  — cache, rate-limit, WS pub/sub
   • Upstash QStash — async pipeline jobs with retries + DLQ
   • Stripe         — billing + metered usage
   • Sentry         — error tracking
   • Honeycomb      — distributed tracing (OTel)
   • WorkOS         — enterprise SSO + SCIM (paid)
```

## Pipeline — meeting end-to-end

The most-load-bearing flow. Numbered by stage.

```
0  Calendar event → Meeting row (status=scheduled, platform auto-detected)
1  Scheduler scans every 60s → finds meeting at T−2min
2  POST /bots/start to bot-service → Fly.io spawns a Machine
3  Machine entrypoint:
     a. start PulseAudio (user mode) + verify vaktram_sink
     b. launch Chromium with --use-fake-ui-for-media-stream
     c. navigate to URL with wait_until=domcontentloaded
     d. mute mic+cam, enter "Vaktram Notetaker", click Join
     e. wait up to 60s for the leave button to appear
4  Audio capture: parec → /tmp/vaktram/audio/{meeting_id}/chunk_*.pcm
5  Watcher loop polls is_meeting_active() every 10s:
     • end-of-meeting screen
     • participant_count == 1 (only the bot)
     • denied/removed banner
     • BOT_MAX_DURATION_SEC reached
6  On exit → concat PCM → WAV → FLAC
7  Upload FLAC to R2 → object key: {region}/org/{org_id}/meetings/{mid}/audio.flac
8  POST /internal/meetings/{mid}/audio-ready (signed) with R2 key
9  publish_job("/pipeline/transcribe/{mid}") via QStash
        (or inline asyncio.create_task fallback for self-host)
10 /pipeline/transcribe:
     a. Read FLAC bytes from R2 (presigned GET)
     b. POST /diarize on Modal endpoint
     c. Groq Whisper (chunked, retry on 429)
     d. Merge speaker turns into TranscriptSegment rows
     e. Record usage_event(transcription_minutes)
11 publish_job("/pipeline/summarize/{mid}")
12 /pipeline/summarize:
     a. Load org's BYOM AIConfig (provider, model, encrypted key)
     b. Call LLM → summary, action items, decisions, follow-ups
     c. Embed segments → MeetingEmbedding rows (pgvector)
     d. Topic Tracker scan → TopicHit rows for matching keywords
     e. notification_dispatcher.dispatch (in-app + email + WS)
13 User opens meeting page → sees transcript, summary, sentiment, soundbites
   Ask (Vakta) chat → RAG over their meetings using vector search + LLM
```

## Data model (high level)

```
Tenant tier:
  organizations            (region, plan, retention)
  user_profiles            (email, role, sso_id)
  channels                 (shared meeting workspaces — NEW)
  channel_members

Meetings:
  meetings                 (platform, scheduled, audio_url, status)
  meeting_participants
  transcript_segments      (fts_idx GIN on content)
  meeting_summaries
  meeting_embeddings       (pgvector vector(1536))
  soundbites               (start, end, share_token — NEW)

Knowledge:
  topic_trackers           (org-level keyword alerts — NEW)
  topic_hits               (segment matches for trackers — NEW)
  ask_threads              (Ask/Vakta conversations — NEW)
  ask_messages             (with citations to segments — NEW)

Identity & RBAC:
  sso_connections   scim_tokens   roles   role_assignments

Billing:
  subscriptions   usage_events   usage_period_summaries   invoices

Compliance:
  retention_policies   kms_keys   data_export_requests   audit_logs

Reliability:
  dead_letter_jobs   webhook_endpoints   webhook_deliveries
```

## Security & isolation

- **Multi-tenancy:** every table has `organization_id`; Postgres RLS enforced.
- **Auth:** custom JWT (15 min access + 1 day refresh) with optional SAML/OIDC SSO.
- **AuthZ:** RBAC via `roles` + `role_assignments`, permission strings of the form `resource:action`.
- **Encryption at rest:** Fernet by default; **BYOK** via AWS/GCP/Azure KMS for enterprise — DEK is wrapped with the customer's key, platform never sees plaintext key.
- **Audit log:** hash-chained rows with `verify_chain()` integrity check, hourly export to S3 Object Lock.
- **DLP:** regex (always on) and Presidio (Enterprise) PII redaction before storing transcripts.
- **Recording-consent disclosure:** bot announces itself on join (per-region rules).

## Scale & SLO targets

| Metric | Pro | Business | Enterprise |
|---|---|---|---|
| API uptime | 99.5% | 99.9% | 99.95% |
| Bot join success | 95% | 98% | 99% |
| Transcript ready ≤ 2× duration | 95% | 98% | 99% |
| API p95 | 400 ms | 250 ms | 150 ms |
| RPO / RTO | 1 h / 4 h | 30 m / 2 h | 15 m / 1 h |

Scaling levers:
- API: Fly.io autoscale 1→N on RPS.
- Bot: 1 Machine per concurrent meeting, scale-to-zero.
- Transcribe / Summarize workers: Upstash QStash queue depth → HPA.
- Diarize: GPU pool on Modal (serverless, scales-to-zero).
- DB: Supabase Pro on launch, dedicated cluster for Enterprise.

## Free-tier first, paid when revenue arrives

See `docs/DEPLOYMENT.md` for the concrete service matrix. The MVP runs on
**$0 + $9/year (domain)** until the first ~30 paying customers, then upgrades
incrementally.
