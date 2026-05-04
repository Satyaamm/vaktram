#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deploy the Vaktram bot service to your VPS.
#
# Usage:
#     bash infra/scripts/deploy-bot-vps.sh
#
# Behavior on every run:
#   1. SSH into the VPS (you'll be prompted for the root password)
#   2. Install Docker if missing
#   3. Clone or fast-forward the public repo at /opt/vaktram
#   4. Write apps/bot-service/.env using secrets read from your LOCAL .env
#   5. Stop and remove any existing container named 'vaktram-bot'
#   6. Build the bot image with --no-cache (always a fresh build)
#   7. Run the new container with --restart unless-stopped
#   8. Wait for /health to respond, otherwise tail the logs and exit 1
#
# Re-running the script is idempotent — old container is always destroyed
# before a new one is built, so you can iterate freely.
#
# Override defaults via env vars before invoking:
#     VPS_HOST=root@<ip>
#     CONTAINER_NAME=vaktram-bot
#     LOCAL_ENV=/path/to/.env
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

VPS_HOST="${VPS_HOST:-root@212.38.94.234}"
CONTAINER_NAME="${CONTAINER_NAME:-vaktram-bot}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCAL_ENV="${LOCAL_ENV:-$REPO_ROOT/.env}"

# ── Pull secrets from the local .env (no secrets baked into this script) ─
if [ ! -f "$LOCAL_ENV" ]; then
    echo "ERROR: local .env not found at $LOCAL_ENV" >&2
    exit 1
fi
set -a
# shellcheck source=/dev/null
. "$LOCAL_ENV"
set +a

SUPABASE_URL_VAL="${NEXT_PUBLIC_SUPABASE_URL:-}"
if [ -z "$SUPABASE_URL_VAL" ]; then
    echo "ERROR: NEXT_PUBLIC_SUPABASE_URL missing from $LOCAL_ENV" >&2
    exit 1
fi
if [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
    echo "ERROR: SUPABASE_SERVICE_ROLE_KEY missing from $LOCAL_ENV" >&2
    exit 1
fi
if [ -z "${BOT_SHARED_SECRET:-}" ]; then
    # Without this the bot service refuses to boot — and without the same
    # value on the API side, every dispatch returns 401. Generate it once
    # and put the same value in BOTH .env files.
    echo "ERROR: BOT_SHARED_SECRET missing from $LOCAL_ENV" >&2
    echo "       Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'" >&2
    exit 1
fi

# ── The remote script (single-quoted heredoc — no local expansion) ──────
REMOTE=$(cat <<'REMOTE_EOF'
set -euo pipefail

: "${BOT_CONTAINER_NAME:?missing}"
: "${BOT_SUPABASE_URL:?missing}"
: "${BOT_SUPABASE_KEY:?missing}"
: "${BOT_AUTH_SECRET:?missing}"

# 1. Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "[VPS] Installing Docker..."
    curl -fsSL https://get.docker.com | sh >/dev/null
else
    echo "[VPS] Docker already installed."
fi

# 2. Repo
if [ -d /opt/vaktram/.git ]; then
    echo "[VPS] Updating repo /opt/vaktram..."
    cd /opt/vaktram
    git fetch --all --quiet
    git reset --hard origin/main --quiet
else
    echo "[VPS] Cloning repo to /opt/vaktram..."
    git clone --quiet https://github.com/Satyaamm/vaktram.git /opt/vaktram
    cd /opt/vaktram
fi

# 3. Write the bot env file (root-owned, 0600)
install -m 0600 /dev/null apps/bot-service/.env
cat > apps/bot-service/.env <<ENVEOF
API_URL=https://vaktram-api.onrender.com
SUPABASE_URL=$BOT_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=$BOT_SUPABASE_KEY
STORAGE_BUCKET=vaktram-audio
HEADLESS=true
PULSE_SERVER=unix:/tmp/pulseaudio.socket
BOT_MAX_DURATION_SEC=10800
BOT_END_CHECK_INTERVAL_SEC=10
REGION=ap-southeast-1
BOT_SERVICE_PORT=8001
BOT_SHARED_SECRET=$BOT_AUTH_SECRET
ENVEOF
echo "[VPS] .env written (mode 0600)."

# 4. Tear down any existing container with the same name
if docker ps -aq -f "name=^${BOT_CONTAINER_NAME}$" | grep -q .; then
    echo "[VPS] Stopping and removing existing container '$BOT_CONTAINER_NAME'..."
    docker stop "$BOT_CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm -f "$BOT_CONTAINER_NAME" >/dev/null
fi

# 5. Remove the previous image so the next build is truly fresh
if docker images -q vaktram-bot:latest | grep -q .; then
    echo "[VPS] Removing previous vaktram-bot:latest image..."
    docker rmi -f vaktram-bot:latest >/dev/null 2>&1 || true
fi

# 6. Prune dangling layers (keeps the host tidy across re-deploys)
docker image prune -f >/dev/null 2>&1 || true

# 7. Build with --no-cache (always fresh)
echo "[VPS] Building image vaktram-bot:latest (--no-cache, ~3-5 min)..."
docker build --no-cache --pull \
    -t vaktram-bot:latest \
    -f infra/docker/Dockerfile.bot \
    .

# 8. Run
echo "[VPS] Starting container '$BOT_CONTAINER_NAME'..."
docker run -d \
    --name "$BOT_CONTAINER_NAME" \
    --restart unless-stopped \
    -p 8001:8001 \
    --env-file apps/bot-service/.env \
    vaktram-bot:latest >/dev/null

# 9. Wait for /health
echo -n "[VPS] Waiting for /health"
for i in $(seq 1 15); do
    echo -n "."
    if curl -fsS http://localhost:8001/health >/dev/null 2>&1; then
        echo
        echo "[VPS] ✓ Bot healthy:"
        curl -s http://localhost:8001/health | sed 's/^/         /'
        echo
        echo "[VPS] Container status:"
        docker ps --filter "name=^${BOT_CONTAINER_NAME}$" --format "         {{.Names}}  {{.Status}}  {{.Ports}}"
        exit 0
    fi
    sleep 3
done
echo
echo "[VPS] ✗ /health didn't respond in 45s. Last 50 log lines:"
docker logs --tail 50 "$BOT_CONTAINER_NAME"
exit 1
REMOTE_EOF
)

# ── Prepend the locally-resolved values, then ship to remote ─────────────
PAYLOAD="$(printf 'export BOT_CONTAINER_NAME=%q\nexport BOT_SUPABASE_URL=%q\nexport BOT_SUPABASE_KEY=%q\nexport BOT_AUTH_SECRET=%q\n%s\n' \
    "$CONTAINER_NAME" \
    "$SUPABASE_URL_VAL" \
    "$SUPABASE_SERVICE_ROLE_KEY" \
    "$BOT_SHARED_SECRET" \
    "$REMOTE")"

echo "→ Deploying '$CONTAINER_NAME' to $VPS_HOST"
echo "→ You'll be prompted for the SSH password..."
echo

ssh -o StrictHostKeyChecking=accept-new -t "$VPS_HOST" "bash -s" <<< "$PAYLOAD"

echo
echo "✓ Deploy complete."
echo
echo "Next steps:"
echo "  • Confirm reachable:  curl http://${VPS_HOST#root@}:8001/health"
echo "  • Tail logs:          ssh $VPS_HOST 'docker logs -f $CONTAINER_NAME'"
echo "  • Restart container:  ssh $VPS_HOST 'docker restart $CONTAINER_NAME'"
echo "  • Update Render env:  BOT_SERVICE_URL=http://${VPS_HOST#root@}:8001"
echo "    (then it will use the new bot URL on the next API redeploy)"
