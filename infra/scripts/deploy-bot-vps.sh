#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deploy the Vaktram bot service to your VPS.
#
# Usage:
#     bash infra/scripts/deploy-bot-vps.sh
#
# Behavior on every run (idempotent — safe to re-run as many times as
# you want, every prior bot artefact is destroyed before the new build):
#
#   1. SSH into the VPS (you'll be prompted for the root password)
#   2. Install Docker if missing
#   3. Clone or fast-forward the public repo at /opt/vaktram
#   4. Write apps/bot-service/.env using secrets read from your LOCAL .env
#   5. Stop + remove containers named 'bot' or 'vaktram-bot' (legacy)
#   6. Stop + remove ANY container that holds host port 1003
#      (catch-all for stale orphans under unexpected names)
#   7. Remove images 'bot:latest' AND 'vaktram-bot:latest'
#   8. Prune dangling image layers
#   9. Prune the docker BUILD CACHE (forces fresh layers next build)
#  10. Build the image with --no-cache --pull (truly fresh)
#  11. Run the new container with --restart unless-stopped
#  12. Wait for /health to respond, otherwise tail the logs and exit 1
#
# ─── Safety contract for shared VPS hosts ────────────────────────────
# This script ONLY touches bot artefacts. It DOES NOT use any of:
#   docker system prune        ← would nuke everything
#   docker container prune     ← would remove all stopped containers
#   docker image prune -a      ← would remove unused images host-wide
# The image-prune step uses `-f` only (dangling-only). The builder-prune
# touches only the build cache, which Docker rebuilds on demand and is
# never tied to a running container.
#
# So if your VPS also runs unrelated containers (halovoice, focalboard,
# rulemind, etc.), this script will leave them completely alone.
#
# Override defaults via env vars before invoking:
#     VPS_HOST=root@<ip>
#     CONTAINER_NAME=bot
#     IMAGE_NAME=bot:latest
#     LOCAL_ENV=/path/to/.env
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

VPS_HOST="${VPS_HOST:-root@212.38.94.234}"
CONTAINER_NAME="${CONTAINER_NAME:-bot}"
IMAGE_NAME="${IMAGE_NAME:-bot:latest}"
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
: "${BOT_IMAGE_NAME:?missing}"
: "${BOT_SUPABASE_URL:?missing}"
: "${BOT_SUPABASE_KEY:?missing}"
: "${BOT_AUTH_SECRET:?missing}"

# Names of containers + images we may have created in past deploys. The
# script removes ALL of them so renames don't strand orphan containers.
LEGACY_NAMES=("bot" "vaktram-bot")
LEGACY_IMAGES=("bot:latest" "vaktram-bot:latest")

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
BOT_SERVICE_PORT=1003
BOT_SHARED_SECRET=$BOT_AUTH_SECRET
ZOHO_STORAGE_STATE_PATH=/app/state/zoho_state.json
ENVEOF
echo "[VPS] .env written (mode 0600)."

# 4. Tear down all known previous containers (by name)
for name in "${LEGACY_NAMES[@]}"; do
    if docker ps -aq -f "name=^${name}$" | grep -q .; then
        echo "[VPS] Removing container by name: '$name'..."
        docker stop "$name" >/dev/null 2>&1 || true
        docker rm -f "$name" >/dev/null 2>&1 || true
    fi
done

# 5. Catch-all: kill anything else still bound to port 1003. Without this
#    a stale orphan blocks `docker run -p 1003:1003` with the cryptic
#    "port is already allocated" error users hit before this fix.
HOLDERS=$(docker ps -aq --filter "publish=1003" 2>/dev/null || true)
if [ -n "$HOLDERS" ]; then
    echo "[VPS] Removing leftover container(s) holding port 1003:"
    docker ps -a --filter "publish=1003" --format "         {{.Names}}  ({{.ID}})  {{.Status}}"
    # shellcheck disable=SC2086
    docker rm -f $HOLDERS >/dev/null 2>&1 || true
fi

# 6. Remove old images (both new + legacy names) so build is truly fresh
for img in "${LEGACY_IMAGES[@]}"; do
    if docker images -q "$img" | grep -q .; then
        echo "[VPS] Removing previous image: '$img'..."
        docker rmi -f "$img" >/dev/null 2>&1 || true
    fi
done

# 7. Prune dangling layers (keeps host disk tidy across re-deploys).
#    -f only → dangling images, NEVER images of running containers.
docker image prune -f >/dev/null 2>&1 || true

# 8. Prune the build cache so the next --no-cache build is truly fresh.
#    Touches only buildx layer cache, never any running container.
docker builder prune -f >/dev/null 2>&1 || true

# 9. Build with --no-cache --pull (always fresh)
echo "[VPS] Building image $BOT_IMAGE_NAME (--no-cache, ~3-5 min)..."
docker build --no-cache --pull \
    -t "$BOT_IMAGE_NAME" \
    -f infra/docker/Dockerfile.bot \
    .

# 10. Run
# Optional Zoho storage_state mount: if /root/zoho_state.json exists on
# the host (operator pre-authenticated and SCP'd it), bind it read-only
# into the container so the Zoho bot reuses a logged-in session and skips
# the guest-page CAPTCHA. Missing file → no mount → guest fallback.
ZOHO_STATE_HOST=/root/zoho_state.json
ZOHO_MOUNT=()
if [ -f "$ZOHO_STATE_HOST" ]; then
    echo "[VPS] Mounting Zoho storage_state from $ZOHO_STATE_HOST"
    ZOHO_MOUNT=(-v "$ZOHO_STATE_HOST:/app/state/zoho_state.json:ro")
else
    echo "[VPS] No Zoho storage_state at $ZOHO_STATE_HOST — Zoho joins will use guest flow (CAPTCHA expected)"
fi

echo "[VPS] Starting container '$BOT_CONTAINER_NAME'..."
docker run -d \
    --name "$BOT_CONTAINER_NAME" \
    --restart unless-stopped \
    -p 1003:1003 \
    --env-file apps/bot-service/.env \
    "${ZOHO_MOUNT[@]}" \
    "$BOT_IMAGE_NAME" >/dev/null

# 11. Wait for /health
echo -n "[VPS] Waiting for /health"
for i in $(seq 1 15); do
    echo -n "."
    if curl -fsS http://localhost:1003/health >/dev/null 2>&1; then
        echo
        echo "[VPS] ✓ Bot healthy:"
        curl -s http://localhost:1003/health | sed 's/^/         /'
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
PAYLOAD="$(printf 'export BOT_CONTAINER_NAME=%q\nexport BOT_IMAGE_NAME=%q\nexport BOT_SUPABASE_URL=%q\nexport BOT_SUPABASE_KEY=%q\nexport BOT_AUTH_SECRET=%q\n%s\n' \
    "$CONTAINER_NAME" \
    "$IMAGE_NAME" \
    "$SUPABASE_URL_VAL" \
    "$SUPABASE_SERVICE_ROLE_KEY" \
    "$BOT_SHARED_SECRET" \
    "$REMOTE")"

echo "→ Deploying container='$CONTAINER_NAME' image='$IMAGE_NAME' to $VPS_HOST"
echo "→ You'll be prompted for the SSH password..."
echo

ssh -o StrictHostKeyChecking=accept-new -t "$VPS_HOST" "bash -s" <<< "$PAYLOAD"

echo
echo "✓ Deploy complete."
echo
echo "Next steps:"
echo "  • Confirm reachable:  curl http://${VPS_HOST#root@}:1003/health"
echo "  • Tail logs:          ssh $VPS_HOST 'docker logs -f $CONTAINER_NAME'"
echo "  • Restart container:  ssh $VPS_HOST 'docker restart $CONTAINER_NAME'"
echo "  • Update Render env:  BOT_SERVICE_URL=http://${VPS_HOST#root@}:1003"
echo "    (then it will use the new bot URL on the next API redeploy)"
