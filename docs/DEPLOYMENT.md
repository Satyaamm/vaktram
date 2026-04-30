# Vaktram Deployment — Free Tier First

The whole stack runs on **$0/month + $9/year (domain)** until ~30 paying
customers, then upgrades incrementally. No localhost-only dependencies; every
service is hosted, reliable, and has a paid tier you slide into without
rewriting code.

## Recommended stack (all free tier ⇒ paid)

| Component | Service | Free tier | Why this | Upgrade trigger |
|---|---|---|---|---|
| Frontend | **Vercel Hobby** | 100 GB bw, unlim builds | Next.js native | Pro $20/mo at 100k visitors |
| API | **Fly.io** | $5 monthly allowance | Docker-native, scales-to-zero, global | $25–50/mo at ~50 active users |
| Bot service | **Fly.io Machines** | same allowance | 1 Machine per meeting, idle = $0 | per-machine billing kicks in only during a call |
| Diarization | **Modal** | $30 free credits/mo | Serverless GPU, cold-start ~5s | pay-per-second after credits |
| DB | **Supabase Free** | 500 MB, 50k MAU, 1 GB storage | Postgres + pgvector + RLS in one box | Pro $25/mo (no auto-pause) |
| Object storage | **Cloudflare R2** | **10 GB + zero egress** | Audio files, no surprise bandwidth bill | $0.015/GB/mo above 10 GB |
| Cache + WS | **Upstash Redis Free** | 10k cmd/day, 256 MB | Pub/sub for cross-instance WS | pay-as-you-go, ~$0.20/100k cmd |
| Job queue | **Upstash QStash Free** | 500 msgs/day | Inline fallback when over quota | $1 / 100k msgs |
| Transcription | **Groq Whisper API** | ~10 hr/day free | 10× faster than OpenAI Whisper | swap to Modal-hosted Whisper at scale |
| LLM (default) | **Gemini 2.0 Flash** | 15 RPM, 1M tok/min free | Default for users w/o their own key | BYOM — users plug in their own |
| Embeddings | **OpenAI text-embed-3-small** | $0.02 / 1M tokens | Cheapest reliable embed model | — |
| Email | **Resend Free** | 100/day, 3k/mo | Transactional email | $20/mo at 50k/mo |
| Errors | **Sentry Free** | 5k errors/mo | — | $26/mo |
| Tracing | **Honeycomb Free** | 20M events/mo | OTel native | — |
| Auth | **Custom JWT** | Free | Already built | WorkOS for enterprise SSO ($125/mo flat) |
| Domain + DNS + WAF | **Cloudflare** | Free DNS + WAF, $9/yr domain | DDoS, SSL, edge caching | — |
| Status page | **Better Stack Free** | 1 monitor | — | $24/mo |
| CI | **GitHub Actions** | 2,000 min/mo free | already wired | — |

**At MVP: $0 + $9/year domain.**
**At $1k MRR (~30 customers): $50–80/mo (mostly Supabase Pro + Sentry).**
**At $10k MRR: $300–500/mo.**

## Why these picks specifically

- **Fly.io over Render/Railway** — Render free tier spins down after 15 min idle (30–60s cold start, unacceptable for a bot dispatcher). Railway killed its free tier. Fly's $5 allowance covers a small always-on API + on-demand bot Machines.
- **Cloudflare R2 over Supabase Storage** — R2 has **zero egress fees** which is huge for audio files that get fetched by transcribers and re-served to users. 10 GB free vs 1 GB on Supabase Storage.
- **Modal over self-hosting GPU** — pyannote needs GPU; running 24/7 on a managed GPU costs ~$700/mo. Modal scales to zero and bills per second of execution. Free $30/mo credits cover ~3,000 hours of audio diarization.
- **Groq Whisper over self-hosted** — Groq is free up to ~10 h/day and 10× faster. We only self-host on Modal once we exceed that.
- **Supabase over RDS/Neon** — only managed Postgres with built-in pgvector, FTS, RLS, and S3-compatible storage. The 7-day auto-pause on free tier is fine for an MVP staging env, not for prod.

## What you (the human) need to do once

These are the only manual setup steps. After this, deploys are `git push`.

| Step | Service | Time |
|---|---|---|
| 1. Buy domain on Cloudflare | Cloudflare | 5 min |
| 2. Create Supabase project, copy `DATABASE_URL` | supabase.com | 3 min |
| 3. Create Cloudflare R2 bucket `vaktram-audio`, generate API token | dash.cloudflare.com → R2 | 5 min |
| 4. Create Upstash Redis + QStash projects | console.upstash.com | 3 min |
| 5. Get Groq API key (free) | console.groq.com | 1 min |
| 6. Get Google AI Studio key for Gemini | aistudio.google.com | 1 min |
| 7. Get HuggingFace token (for pyannote on Modal) | huggingface.co/settings/tokens | 1 min |
| 8. Create Resend account, verify domain | resend.com | 5 min |
| 9. Create Sentry project (Python + Next.js) | sentry.io | 3 min |
| 10. Create Stripe account (test mode is fine for now) | dashboard.stripe.com | 5 min |
| 11. Install Fly CLI, run `fly launch` for api + bot | fly.io | 10 min |
| 12. Connect Vercel to GitHub, set root to `apps/web` | vercel.com | 5 min |
| 13. Create Modal account, deploy diarization fn | modal.com | 10 min |

**Total ~1 hour. After this, every deploy is `git push origin main`.**

## Step-by-step: deploy from scratch

### A. Database (Supabase)

```bash
# Create project at supabase.com → copy connection string
# Run migrations:
psql $DATABASE_URL -f supabase/migrations/20260302155003_initial_schema.sql
psql $DATABASE_URL -f supabase/migrations/20260307120000_add_billing.sql
psql $DATABASE_URL -f supabase/migrations/20260307130000_add_search_indexes.sql
psql $DATABASE_URL -f supabase/migrations/20260307140000_add_dlq.sql
psql $DATABASE_URL -f supabase/migrations/20260307150000_add_identity.sql
psql $DATABASE_URL -f supabase/migrations/20260307160000_add_compliance.sql
psql $DATABASE_URL -f supabase/migrations/20260307170000_add_region.sql
psql $DATABASE_URL -f supabase/migrations/20260307180000_add_intel_features.sql
```

(Or use the Supabase CLI: `supabase db push`.)

### B. Object storage (Cloudflare R2)

```
1. cloudflare.com → R2 → Create bucket "vaktram-audio"
2. Manage R2 API tokens → Create token (read+write to vaktram-audio)
3. Save: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
4. Optional: enable public bucket for read-only signed URLs
```

### C. API + Bot service (Fly.io)

```bash
# Install: brew install flyctl
fly auth signup
fly launch --config infra/fly/fly.api.toml --no-deploy
fly secrets set \
  DATABASE_URL=...        \
  JWT_SECRET=...          \
  ENCRYPTION_KEY=...      \
  GROQ_API_KEY=...        \
  GOOGLE_AI_API_KEY=...   \
  UPSTASH_REDIS_URL=...   \
  UPSTASH_REDIS_TOKEN=... \
  QSTASH_TOKEN=...        \
  STRIPE_API_KEY=...      \
  R2_ACCOUNT_ID=...       \
  R2_ACCESS_KEY_ID=...    \
  R2_SECRET_ACCESS_KEY=...\
  STORAGE_BUCKET=vaktram-audio \
  -a vaktram-api
fly deploy -c infra/fly/fly.api.toml

# Repeat for bot:
fly launch --config infra/fly/fly.bot.toml --no-deploy
fly deploy -c infra/fly/fly.bot.toml
```

### D. Frontend (Vercel)

```
1. vercel.com → Import GitHub repo
2. Root directory: apps/web
3. Framework: Next.js (auto-detected)
4. Env vars: NEXT_PUBLIC_API_URL=https://api.vaktram.com
5. Deploy
6. Add custom domain in Cloudflare DNS:
   www → CNAME → cname.vercel-dns.com
   api → CNAME → vaktram-api.fly.dev
```

### E. Diarization (Modal)

```bash
pip install modal
modal token new
modal deploy infra/modal/diarize.py
# Note the URL it prints, set as DIARIZATION_SERVICE_URL on Fly
```

### F. Verify happy path

```bash
# 1. Sign up via the web app
# 2. Connect Google Calendar
# 3. Schedule a Google Meet for 2 minutes from now
# 4. Watch logs:  fly logs -a vaktram-api -a vaktram-bot
# 5. After meeting ends, transcript + summary appear in dashboard
```

## When to upgrade what

| Signal | Upgrade | Cost |
|---|---|---|
| Supabase project pauses on you | Supabase Pro | $25/mo |
| Fly.io bill creeps past $5 | Buy a $25 reservation | $25/mo |
| Groq 10 h/day exhausted regularly | Self-host Whisper on Modal | $0.03/audio-hour |
| 50k Resend emails/mo | Resend Pro | $20/mo |
| Sentry 5k errors/mo blown | Team plan | $26/mo |
| First enterprise lead asking for SAML | WorkOS | $125/mo flat |
| Multi-region (EU customer) | Add Fly EU region + EU bucket | $0 marginal |

## Upgrade math (back-of-envelope)

```
Customers   Plan-mix       MRR        Hosting cost   Margin
   30      mostly Pro      $360       $50            86%
  300      Pro+Team        $5k        $300           94%
3000       +Business+SSO   $80k       $3k            96%
```

## What we deliberately did NOT pick

- **AWS / GCP / Azure** for hosting — too much setup time for an MVP. Move there for Enterprise on-prem only.
- **Heroku** — no free tier since 2022.
- **DigitalOcean App Platform** — fine, but Fly's per-meeting Machines map better to our bot model.
- **Pinecone** — pgvector inside Supabase is enough until ~10M vectors.
- **Twilio** — overkill; Resend covers email, no SMS needed yet.
