# Deploy the bot service to a VPS

The bot service runs Playwright + PulseAudio + FFmpeg to join Meet/Zoom/Teams
calls. It can't run on Render free tier (no audio device, 512MB RAM cap), so
it lives on a VPS you control.

## VPS specs

| Resource | Minimum | Recommended | Why |
|---|---|---|---|
| RAM | 2 GB | 4 GB | Chromium + Playwright + PulseAudio + FFmpeg |
| vCPU | 1 | 2 | Concurrent meetings |
| Disk | 10 GB | 20 GB | Docker layers + temp audio chunks |
| OS | Ubuntu 22.04 LTS | Same | Docker / PulseAudio play nicest here |

Tested cheap providers: Hetzner CX22 ($4/mo), Vultr $6, DigitalOcean basic, Contabo.

## One-shot deploy

SSH into the VPS, then:

```bash
# 1) Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 2) Pull the public repo
git clone https://github.com/Satyaamm/vaktram.git
cd vaktram

# 3) Bot env — fill in your values
cat > apps/bot-service/.env <<'EOF'
# Where the API lives — bot calls the API on /audio-ready when done
API_URL=https://vaktram-api.onrender.com

# Supabase Storage (where bot uploads recorded audio for the API to read)
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_REDACTED__paste_from_supabase_dashboard
STORAGE_BUCKET=vaktram-audio

# Bot settings
HEADLESS=true
PULSE_SERVER=unix:/tmp/pulseaudio.socket
BOT_MAX_DURATION_SEC=10800
BOT_END_CHECK_INTERVAL_SEC=10
REGION=ap-southeast-1
BOT_SERVICE_PORT=8001
EOF

# 4) Build + run
docker build -t vaktram-bot -f infra/docker/Dockerfile.bot .
docker run -d \
  --name vaktram-bot \
  --restart unless-stopped \
  -p 8001:8001 \
  --env-file apps/bot-service/.env \
  vaktram-bot

# 5) Sanity check
sleep 8 && curl http://localhost:8001/health
# Expected: {"status":"healthy","active_bots":0,"version":"0.1.0"}
```

## Make it reachable from Render's API

The Render API needs to POST `https://<bot>/bots/start` when a meeting is due.
Pick one inbound option:

### Option A — Cloudflare Tunnel (recommended; free; no public ports)

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cf.deb
sudo dpkg -i cf.deb && rm cf.deb

# Login (opens a browser link)
cloudflared tunnel login

# Quick path — gets you a free *.trycloudflare.com URL, no domain needed
cloudflared tunnel --url http://localhost:8001 &> /var/log/cloudflared.log &
sleep 3 && grep "trycloudflare.com" /var/log/cloudflared.log
# Copy the https://*.trycloudflare.com URL it prints
```

Then on **Render → vaktram-api → Environment**:

```
BOT_SERVICE_URL = https://<the-trycloudflare-url>.trycloudflare.com
```

Render auto-redeploys.

### Option B — Open port 8001 (simpler; less secure)

```bash
sudo ufw allow 8001/tcp
sudo ufw enable
```

Set Render env:

```
BOT_SERVICE_URL = http://<vps-public-ip>:8001
```

⚠️ Anyone can hit `/bots/start`. Acceptable for testing only — add a shared
secret header before real customers depend on it.

## Tell the API where the bot lives

After either Option A or B, the Render API needs **two more env vars** so it
can decrypt audio that the bot uploaded to Supabase Storage:

```
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_REDACTED__paste_from_supabase_dashboard
BOT_SERVICE_URL=<your-bot-url>
```

Render → Environment → add → save → auto-redeploy.

## Verifying the full chain

After deploy:

```bash
# 1) On the VPS — confirm the bot is listening
curl http://localhost:8001/health

# 2) On the public URL — confirm it's reachable
curl https://<bot-url>/health

# 3) Through the API — schedule a fake bot start
curl -X POST https://<bot-url>/bots/start \
  -H 'Content-Type: application/json' \
  -d '{"meeting_id":"test-1","meeting_url":"https://meet.google.com/abc-defg-hij","platform":"google_meet","bot_name":"Vaktram Test"}'
# Returns { "status": "joining" } — bot is now trying to join the meet
# Stop it:
curl -X POST https://<bot-url>/bots/stop -H 'Content-Type: application/json' -d '{"meeting_id":"test-1"}'
```

## Operational notes

- **Container restart policy** is `unless-stopped` so reboots survive.
- **Logs:** `docker logs -f vaktram-bot`
- **Pull updates:** `cd vaktram && git pull && docker build -t vaktram-bot -f infra/docker/Dockerfile.bot . && docker rm -f vaktram-bot && docker run -d ...` (same `docker run` as above)
- **Resource ceiling:** `docker stats vaktram-bot` — Chromium per call uses ~600 MB. With `BOT_MAX_DURATION_SEC=10800` (3h) the worst case is ~600 MB × concurrent meetings.

## Next: shared-secret auth (when you add the first real customer)

Right now anyone with the bot URL can dispatch a recording. Before exposing
this to non-test customers, add an HMAC signed header on every API → bot call.
30 LOC; happy to ship when you're ready.
