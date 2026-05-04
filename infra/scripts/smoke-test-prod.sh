#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Smoke-test the live Vaktram deployment end-to-end.
#
# Run this AFTER:
#   1. Setting all env vars on Render (and waiting for a redeploy)
#   2. Setting all env vars on Vercel (and waiting for a redeploy)
#   3. Running infra/scripts/deploy-bot-vps.sh
#
# What it checks:
#   • API reachable + DB connected
#   • Web reachable + correct API baked in
#   • Bot reachable
#   • CORS allows the Vercel origin
#   • Auth flow rejects bad inputs correctly
#   • Internal-auth gate works (bot-shared-secret enforced)
#   • QStash signature gate works
#
# Exits 0 if everything passes; non-zero on first failure.
# ─────────────────────────────────────────────────────────────────────────
set -uo pipefail

API="${API_URL:-https://vaktram-api.onrender.com}"
WEB="${WEB_URL:-https://vaktram-web.vercel.app}"
BOT="${BOT_URL:-http://212.38.94.234:1003}"

GREEN=$'\033[32m'; RED=$'\033[31m'; DIM=$'\033[2m'; RESET=$'\033[0m'
pass() { echo "  ${GREEN}✓${RESET} $1"; }
fail() { echo "  ${RED}✗${RESET} $1"; FAILED=1; }
hdr()  { echo; echo "${DIM}── $1 ──${RESET}"; }

FAILED=0

hdr "API on Render"
code=$(curl -s -o /dev/null -w "%{http_code}" "$API/health")
[ "$code" = "200" ] && pass "/health → 200" || fail "/health → $code"

dbz=$(curl -s "$API/healthz")
echo "$dbz" | grep -q '"database":"connected"' && pass "/healthz DB connected" || fail "/healthz: $dbz"

hdr "Web on Vercel"
code=$(curl -s -A "smoke-test" -o /dev/null -w "%{http_code}" "$WEB/")
[ "$code" = "200" ] && pass "/ → 200" || fail "/ → $code"

# Verify the API URL baked into the login page bundle matches our API
login=$(curl -s -A "smoke-test" "$WEB/login")
chunk=$(echo "$login" | grep -oE 'src="[^"]*\(auth\)/login/page-[^"]+\.js"' | head -1 | sed -E 's/src="//;s/"$//')
if [ -n "$chunk" ]; then
  baked=$(curl -s "${WEB}${chunk}" | grep -oE 'https://[^"]*onrender\.com' | head -1)
  if [ "$baked" = "$API" ]; then
    pass "frontend bundle calls $API"
  else
    fail "frontend bundle expects '$baked', want '$API'"
  fi
fi

hdr "Bot on VPS"
code=$(curl -s -m 5 -o /tmp/.bot-h -w "%{http_code}" "$BOT/health")
if [ "$code" = "200" ]; then
  pass "/health → 200 ($(cat /tmp/.bot-h))"
else
  fail "/health → $code (deploy-bot-vps.sh not run, or :1003 not open in firewall)"
fi

hdr "CORS"
allow=$(curl -s -I -X OPTIONS "$API/api/v1/auth/login" \
  -H "Origin: $WEB" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  | grep -i "^access-control-allow-origin:" | tr -d '\r' | awk '{print $2}')
[ "$allow" = "$WEB" ] && pass "API allows origin $WEB" || fail "API allow-origin: '$allow'"

hdr "Auth surface"
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/api/v1/auth/signup" \
  -H "Content-Type: application/json" -d '{}')
[ "$code" = "422" ] && pass "empty signup → 422" || fail "empty signup → $code"

body=$(curl -s -X POST "$API/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke-nobody@example.com","password":"WrongPwd1!"}')
echo "$body" | grep -q "invalid_credentials" \
  && pass "wrong creds → invalid_credentials" \
  || fail "wrong creds: $body"

code=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/auth/me")
[ "$code" = "401" ] && pass "unauth /me → 401" || fail "unauth /me → $code"

hdr "Internal auth gate"
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$API/internal/meetings/00000000-0000-0000-0000-000000000000/audio-ready" \
  -H "Content-Type: application/json" -d '{}')
if [ "$code" = "401" ]; then
  pass "/internal/* without X-Bot-Auth → 401 (BOT_SHARED_SECRET set on Render)"
elif [ "$code" = "500" ]; then
  fail "/internal/* → 500 (BOT_SHARED_SECRET missing on Render!)"
else
  fail "/internal/* → $code (unexpected)"
fi

hdr "QStash signature gate"
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$API/internal/pipeline/transcribe/00000000-0000-0000-0000-000000000000")
[ "$code" = "401" ] && pass "/pipeline/* without signature → 401" \
  || fail "/pipeline/* → $code"

echo
if [ $FAILED -eq 0 ]; then
  echo "${GREEN}━━━ ALL CHECKS PASSED ━━━${RESET}"
  echo "Ready for an end-to-end test: schedule a Google Meet on a connected calendar"
  echo "and watch the meeting record arrive in the dashboard."
  exit 0
else
  echo "${RED}━━━ SOME CHECKS FAILED ━━━${RESET}"
  exit 1
fi
