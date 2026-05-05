#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Integration test for every router in the live Vaktram API.
#
# What this proves:
#   • Each route is registered and reachable (no 404 for a documented path).
#   • Public endpoints return the documented status + shape.
#   • Auth-protected endpoints reject unauthenticated calls with 401.
#   • Error contracts (structured `{error, message}` shapes) match docs.
#
# What this does NOT prove (run a real signup → verify → meeting flow for):
#   • Long-running pipeline (transcribe → summarize) actually completes.
#   • Email delivery (Resend).
#   • Calendar sync (Google OAuth).
#   • Stripe checkout / billing webhooks.
#   • SAML / SCIM identity provisioning (needs a real IDP).
#   • WebSocket /ws/meetings/{id} real-time updates.
#
# Usage:
#   bash infra/scripts/test-endpoints-prod.sh
# Override the host:
#   API_URL=http://localhost:8000 bash infra/scripts/test-endpoints-prod.sh
# ─────────────────────────────────────────────────────────────────────────
set -uo pipefail

API="${API_URL:-https://vaktram-api.onrender.com}"
GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; DIM=$'\033[2m'; RESET=$'\033[0m'

PASS=0; FAIL=0; SKIP=0
FAILED_LINES=()

# ── Test helpers ────────────────────────────────────────────────────────

# Check status code only.
#   expect <description> <expected_codes_csv> <method> <path> [body]
expect() {
  local desc="$1" want="$2" method="$3" path="$4" body="${5:-}"
  local code body_data
  if [ -n "$body" ]; then
    code=$(curl -s -o /tmp/.body -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" -d "$body" "$API$path" 2>/dev/null)
  else
    code=$(curl -s -o /tmp/.body -w "%{http_code}" -X "$method" "$API$path" 2>/dev/null)
  fi
  if echo ",$want," | grep -q ",$code,"; then
    PASS=$((PASS+1))
    echo "  ${GREEN}✓${RESET} ${desc} ${DIM}[$method $path → $code]${RESET}"
  else
    FAIL=$((FAIL+1))
    FAILED_LINES+=("$desc — wanted $want got $code at $method $path")
    body_data=$(head -c 200 /tmp/.body 2>/dev/null)
    echo "  ${RED}✗${RESET} ${desc} ${DIM}[$method $path → $code, want $want]${RESET}"
    [ -n "$body_data" ] && echo "    ${DIM}body:${RESET} ${body_data}"
  fi
}

# Check status AND that the JSON body contains a substring (or a `detail.error` key).
#   expect_json <description> <expected_code> <method> <path> <body> <substring>
expect_json() {
  local desc="$1" want="$2" method="$3" path="$4" body="$5" needle="$6"
  local code response
  response=$(curl -s -o /tmp/.body -w "%{http_code}" -X "$method" \
    -H "Content-Type: application/json" -d "$body" "$API$path" 2>/dev/null)
  code=$response
  if [ "$code" = "$want" ] && grep -q "$needle" /tmp/.body; then
    PASS=$((PASS+1))
    echo "  ${GREEN}✓${RESET} ${desc} ${DIM}[→ $code, found '${needle}']${RESET}"
  else
    FAIL=$((FAIL+1))
    body_data=$(head -c 200 /tmp/.body 2>/dev/null)
    FAILED_LINES+=("$desc — wanted $want+'$needle' got $code at $method $path")
    echo "  ${RED}✗${RESET} ${desc} ${DIM}[→ $code, want $want+'$needle']${RESET}"
    [ -n "$body_data" ] && echo "    ${DIM}body:${RESET} ${body_data}"
  fi
}

skip() {
  SKIP=$((SKIP+1))
  echo "  ${YELLOW}~${RESET} $1"
}

hdr() { echo; echo "${DIM}── $1 ──${RESET}"; }


# ── Tier 0 · liveness ──────────────────────────────────────────────────
hdr "Health"
expect "GET /health"               200      GET  /health
expect "HEAD /health"              200      HEAD /health
expect "GET /healthz (DB probe)"   200      GET  /healthz


# ── Tier 1 · auth surface ──────────────────────────────────────────────
hdr "Auth"
# Signup — empty body must Pydantic-422
expect      "signup empty body → 422"        422  POST /api/v1/auth/signup '{}'
# Signup — weak password
expect_json "signup weak password → 422"     422  POST /api/v1/auth/signup \
  '{"full_name":"Test","organization_name":"Org","email":"t@example.com","password":"abc","password_confirm":"abc"}' \
  "password"
# Login — wrong creds → 401 invalid_credentials
expect_json "login wrong creds → invalid_credentials" 401 POST /api/v1/auth/login \
  '{"email":"nobody-prod-test@example.com","password":"WrongPwd1!"}' \
  "invalid_credentials"
# Login — empty body → 422
expect      "login empty body → 422"         422  POST /api/v1/auth/login '{}'
# /me unauth → 401
expect      "GET /me unauth → 401"           401  GET  /api/v1/auth/me
# /verify-email bad token → 400 invalid_or_expired_token
expect_json "verify-email bad token → 400"   400  POST /api/v1/auth/verify-email \
  '{"token":"this-is-not-a-real-token-xx"}' \
  "invalid_or_expired_token"
# /resend-verification — always 202
expect      "resend-verification → 202"      202  POST /api/v1/auth/resend-verification \
  '{"email":"nobody-prod-test@example.com"}'
# /forgot-password — always 202
expect      "forgot-password → 202"          202  POST /api/v1/auth/forgot-password \
  '{"email":"nobody-prod-test@example.com"}'
# /reset-password — bad token → 400
expect_json "reset-password bad token → 400" 400  POST /api/v1/auth/reset-password \
  '{"token":"fake","new_password":"NotReal123"}' \
  "invalid_or_expired_token"
# /reset-password — weak password → 400
expect_json "reset-password weak pwd → 400"  400  POST /api/v1/auth/reset-password \
  '{"token":"x","new_password":"abc"}' \
  "weak_password"
# /refresh — no token → 401
expect      "refresh no token → 401"         401  POST /api/v1/auth/refresh '{}'
# /refresh — junk token → 401
expect      "refresh junk token → 401"       401  POST /api/v1/auth/refresh \
  '{"refresh_token":"clearly-not-a-jwt"}'
# /logout — idempotent 204
expect      "logout → 204"                   204  POST /api/v1/auth/logout '{}'


# ── Tier 2 · meetings (auth required → expect 401) ─────────────────────
hdr "Meetings (require auth → 401)"
expect "GET    /meetings"                401 GET    /api/v1/meetings
expect "POST   /meetings"                401 POST   /api/v1/meetings  '{"title":"x"}'
expect "GET    /meetings/{id}"           401 GET    /api/v1/meetings/00000000-0000-0000-0000-000000000000
expect "PATCH  /meetings/{id}"           401 PATCH  /api/v1/meetings/00000000-0000-0000-0000-000000000000 '{}'
expect "DELETE /meetings/{id}"           401 DELETE /api/v1/meetings/00000000-0000-0000-0000-000000000000
expect "POST   /meetings/upload-audio"   401 POST   /api/v1/meetings/upload-audio
expect "GET    /meetings/{id}/audio"     401 GET    /api/v1/meetings/00000000-0000-0000-0000-000000000000/audio


# ── Tier 2 · transcripts / summaries / search ──────────────────────────
hdr "Transcripts / Summaries / Search"
expect "GET  /transcripts/{id}"          401 GET  /api/v1/transcripts/00000000-0000-0000-0000-000000000000
expect "POST /transcripts"               401 POST /api/v1/transcripts '{}'
expect "GET  /summaries/{id}"            401 GET  /api/v1/summaries/00000000-0000-0000-0000-000000000000
expect "POST /summaries/generate"        401 POST /api/v1/summaries/generate '{}'
expect "POST /search"                    401 POST /api/v1/search '{}'


# ── Tier 2 · bot dispatch / ai-config / analytics ──────────────────────
hdr "Bot / AI-Config / Analytics"
expect "POST /bot/join"                  401 POST /api/v1/bot/join '{}'
expect "GET  /bot/status/{id}"           401 GET  /api/v1/bot/status/00000000-0000-0000-0000-000000000000
expect "POST /bot/schedule"              401 POST /api/v1/bot/schedule '{}'
expect "GET  /bot/scheduled-jobs"        401 GET  /api/v1/bot/scheduled-jobs
expect "GET  /ai-config"                 401 GET  /api/v1/ai-config
expect "GET  /ai-config/status"          401 GET  /api/v1/ai-config/status
expect "POST /ai-config"                 401 POST /api/v1/ai-config '{}'
expect "POST /ai-config/test"            401 POST /api/v1/ai-config/test '{}'
expect "GET  /analytics/overview"        401 GET  /api/v1/analytics/overview
expect "GET  /analytics/usage"           401 GET  /api/v1/analytics/usage
expect "GET  /analytics/talk-time"       401 GET  /api/v1/analytics/talk-time
expect "GET  /analytics/frequency"       401 GET  /api/v1/analytics/frequency?period=30d
expect "GET  /analytics/topics"          401 GET  /api/v1/analytics/topics


# ── Tier 2 · notifications / teams / calendar ──────────────────────────
hdr "Notifications / Teams / Calendar"
expect "GET  /notifications"             401 GET  /api/v1/notifications
expect "POST /notifications/read-all"    401 POST /api/v1/notifications/read-all
expect "GET  /teams/organization"        401 GET  /api/v1/teams/organization
expect "GET  /teams/members"             401 GET  /api/v1/teams/members
expect "GET  /teams/profile"             401 GET  /api/v1/teams/profile
expect "POST /teams/invite"              401 POST /api/v1/teams/invite '{"email":"x@x.com"}'
expect "GET  /calendar/connections"      401 GET  /api/v1/calendar/connections
expect "POST /calendar/authorize"        401 POST /api/v1/calendar/authorize
expect "POST /calendar/sync"             401 POST /api/v1/calendar/sync


# ── Tier 1 · public webhooks / billing / SSO ────────────────────────────
hdr "Public webhooks / billing / SSO"
# Google calendar webhook — without channel ID → 400
expect "google-calendar webhook no headers → 400"  400 POST /api/v1/webhooks/google-calendar '{}'
# Bot-events webhook — no auth → 401
expect "bot-events no auth → 401"         401 POST /api/v1/webhooks/bot-events '{}'
# Billing plans — public
expect "GET /billing/plans → 200"         200 GET  /api/v1/billing/plans
# Stripe webhook — missing signature → 400
expect "stripe webhook no sig → 400"      400 POST /api/v1/billing/webhook '{}'
# SSO lookup for unknown email — 200 with sso=false
expect_json "sso/lookup unknown → sso:false"  200 GET  '/api/v1/sso/lookup?email=nobody@example.com' '' "sso"
expect "sso/init unknown → 404"           404 GET  '/api/v1/sso/init?email=nobody@example.com'


# ── Tier 2 · compliance / ask / topics / channels / soundbites ──────────
hdr "Compliance / Ask / Topics / Channels / Soundbites / Integrations"
expect "GET  /compliance/retention"      401 GET  /api/v1/compliance/retention
expect "GET  /compliance/audit"          401 GET  /api/v1/compliance/audit
expect "POST /compliance/export"         401 POST /api/v1/compliance/export
expect "DELETE /compliance/me"           401 DELETE /api/v1/compliance/me
expect "POST /ask/threads"               401 POST /api/v1/ask/threads '{}'
expect "GET  /ask/threads"               401 GET  /api/v1/ask/threads
expect "GET  /topics"                    401 GET  /api/v1/topics
expect "POST /topics"                    401 POST /api/v1/topics '{}'
expect "GET  /channels"                  401 GET  /api/v1/channels
expect "POST /channels"                  401 POST /api/v1/channels '{}'
expect "POST /soundbites"                401 POST /api/v1/soundbites '{}'
expect "GET  /soundbites/shared/junk"    404 GET  /api/v1/soundbites/shared/junk
expect "GET  /integrations"              401 GET  /api/v1/integrations
expect "PUT  /integrations/slack"        401 PUT  /api/v1/integrations/slack '{}'


# ── Tier 1 · public outbound webhook events list ───────────────────────
hdr "Outbound webhooks"
expect "GET /webhooks-out/events → 200"  200 GET  /api/v1/webhooks-out/events
expect "GET  /webhooks-out"              401 GET  /api/v1/webhooks-out
expect "POST /webhooks-out"              401 POST /api/v1/webhooks-out '{}'


# ── SCIM (separate Bearer scheme) ──────────────────────────────────────
hdr "SCIM"
# No auth → 401 "Missing SCIM bearer token"
expect "GET    /scim/v2/Users no auth → 401"        401 GET    /api/v1/scim/v2/Users
expect "POST   /scim/v2/Users no auth → 401"        401 POST   /api/v1/scim/v2/Users '{}'
expect "DELETE /scim/v2/Users/{id} no auth → 401"   401 DELETE /api/v1/scim/v2/Users/00000000-0000-0000-0000-000000000000


# ── Internal / pipeline endpoints ───────────────────────────────────────
hdr "Internal & QStash gates"
# Without the secret → 401
expect "internal/audio-ready no auth → 401"          401 POST /internal/meetings/00000000-0000-0000-0000-000000000000/audio-ready '{}'
expect "internal/transcription-complete no auth → 401" 401 POST /internal/meetings/00000000-0000-0000-0000-000000000000/transcription-complete '{}'
expect "internal/summarization-complete no auth → 401" 401 POST /internal/meetings/00000000-0000-0000-0000-000000000000/summarization-complete '{}'
expect "internal/pipeline-error no auth → 401"        401 POST /internal/meetings/00000000-0000-0000-0000-000000000000/pipeline-error '{}'
# QStash-driven endpoints reject without signature
expect "pipeline/transcribe no sig → 401"            401 POST /internal/pipeline/transcribe/00000000-0000-0000-0000-000000000000
expect "pipeline/summarize no sig → 401"             401 POST /internal/pipeline/summarize/00000000-0000-0000-0000-000000000000


# ── Tier 1 · with valid X-Bot-Auth (proves secret matches) ─────────────
hdr "X-Bot-Auth chain (valid secret from local .env)"
SECRET=$(grep "^BOT_SHARED_SECRET=" "$(dirname "$0")/../../.env" 2>/dev/null | cut -d= -f2-)
if [ -n "$SECRET" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "$API/internal/meetings/00000000-0000-0000-0000-000000000000/audio-ready" \
    -H "Content-Type: application/json" \
    -H "X-Bot-Auth: $SECRET" \
    -d '{"audio_storage_path":"supabase://test/x.flac","user_id":"00000000-0000-0000-0000-000000000000"}')
  if [ "$code" = "200" ] || [ "$code" = "404" ] || [ "$code" = "422" ]; then
    PASS=$((PASS+1))
    echo "  ${GREEN}✓${RESET} internal/audio-ready with valid secret → $code (Render's BOT_SHARED_SECRET matches local)"
  else
    FAIL=$((FAIL+1))
    FAILED_LINES+=("X-Bot-Auth mismatch — got $code (expected 200/404/422). Render's BOT_SHARED_SECRET differs from local .env.")
    echo "  ${RED}✗${RESET} internal/audio-ready with valid secret → $code (Render's BOT_SHARED_SECRET differs from local!)"
  fi
else
  skip "BOT_SHARED_SECRET not in local .env — skipping cross-service auth check"
fi


# ── Skipped (need state or external IDP) ───────────────────────────────
hdr "Skipped"
skip "WS /ws/meetings/{id} — websocket; needs JWT in query"
skip "GET /calendar/callback — needs Google OAuth code"
skip "POST /sso/saml/acs — needs IdP-signed assertion"
skip "GET /scim/v2/Users with Bearer — needs provisioned SCIM token"
skip "POST /billing/checkout — needs JWT + Stripe keys + admin role"
skip "POST /billing/portal — needs JWT + Stripe + admin"
skip "POST /billing/webhook (valid sig) — needs Stripe webhook signature"
skip "Full pipeline (transcribe → summarize) — needs real audio + QStash signature"
skip "POST /meetings + create + run — needs JWT (signup→verify→login flow)"


# ── Summary ────────────────────────────────────────────────────────────
TOTAL=$((PASS+FAIL))
echo
echo "${DIM}━━━ Results ━━━${RESET}"
echo "  ${GREEN}Passed:${RESET}  $PASS / $TOTAL"
[ $FAIL -gt 0 ] && echo "  ${RED}Failed:${RESET}  $FAIL"
[ $SKIP -gt 0 ] && echo "  ${YELLOW}Skipped:${RESET} $SKIP (require state or external services)"
echo

if [ $FAIL -gt 0 ]; then
  echo "${RED}Failures:${RESET}"
  for line in "${FAILED_LINES[@]}"; do
    echo "  • $line"
  done
  exit 1
fi
echo "${GREEN}━━━ All ${PASS} routes wired correctly ━━━${RESET}"
exit 0
