# Vaktram — API Reference

All routes are mounted under `/api/v1` unless noted otherwise. `/internal/*` and `/health*` are unprefixed. **Auth column** values:

- **`JWT`** — `Authorization: Bearer <access_token>` from a logged-in user. Short-lived (15 min); auto-refreshed via the HttpOnly `vaktram_refresh` cookie.
- **`X-Bot-Auth`** — Internal callers (bot service, workers) sending `BOT_SHARED_SECRET` in the `X-Bot-Auth` header. Constant-time HMAC compare.
- **`Upstash-Signature`** — QStash webhooks verify a signed JWT in the `Upstash-Signature` header against the current + next signing keys.
- **`SCIM Bearer`** — Identity-provider tokens for `/scim/v2/Users`. Bearer compared against hashes in `scim_tokens`.
- **`Stripe-Signature`** — Stripe webhook HMAC.
- **`public`** — No auth. Always rate-limited per-IP at the middleware layer.
- **`WebSocket`** — Connection-scoped, per-meeting.

All `4xx` Pydantic validation errors return `422` with FastAPI's default body shape: `{"detail":[{"loc":[...],"msg":"...","type":"..."}]}`. Endpoint-specific errors use the shapes documented inline.

> **Citations** point to `apps/api/app/...` paths.

---

## Health

### `GET /health` (also `HEAD`)
**Auth:** public. **Response 200:** `{"status":"ok"}`. Liveness only — does not touch the DB. Source: `routers/health.py`.

### `GET /healthz` (also `HEAD`)
**Auth:** public. **Response 200:** `{"status":"ok","database":"connected"}` or `{"status":"degraded","database":"error: ..."}`. Runs `SELECT 1` against the DB.

---

## Auth — `/api/v1/auth/*`

### `POST /auth/signup` — Create account
- **Auth:** public
- **Request:** `SignupRequest` (`schemas/team.py`)
  - `full_name` — `min=2 max=100`, regex `^[A-Za-zÀ-ÖØ-öø-ÿ'.\- ]+$`
  - `organization_name` — `min=2 max=120`
  - `email` — `EmailStr`
  - `phone` — optional, `^\+?[0-9 ()\-]{7,20}$`
  - `password` — `min=8 max=128`, must contain ≥1 letter and ≥1 digit
  - `password_confirm` — must equal `password`
- **Response 201:** `SignupResponse` `{user_id, email, organization_id, verification_email_sent, message}`
- **Errors**
  - `409` `{"error":"email_exists","message":"An account with this email already exists. Please log in or reset your password."}` (`routers/auth.py:154`)
- **Side effects:** Org + user created (`is_active=False`, `email_verified_at=NULL`); bcrypt hash; verification token issued; email sent.

### `POST /auth/verify-email` — Redeem verification token
- **Auth:** public
- **Request:** `VerifyEmailRequest` `{ token: str(min=10,max=200) }`
- **Response 200:** `TokenResponse` `{access_token, refresh_token, token_type:"bearer", user: UserProfileRead}`
- **Errors**
  - `400` `{"error":"invalid_or_expired_token","message":"This verification link is invalid or has expired. Request a new one."}` (`auth.py:231`)
  - `404` `"User not found"` (`auth.py:242`)
- **Side effects:** Marks `email_verified_at=now()`, `is_active=True`. Sets `vaktram_refresh` HttpOnly cookie + `vaktram_session` hint cookie. Sends welcome email.

### `POST /auth/resend-verification` — Resend verification email
- **Auth:** public
- **Request:** `{ email: EmailStr }`
- **Response 202:** `{message:str}`. **Always 202**, even on unknown email — prevents enumeration.
- **Errors:** none.
- **Side effects:** Rate-limited to **3/hour/email** in Redis (`services/session_service.py:69`). Invalidates outstanding tokens, issues a fresh one, sends email.

### `POST /auth/login` — Authenticate
- **Auth:** public
- **Request:** `LoginRequest` `{ email: EmailStr, password: str }`
- **Response 200:** `TokenResponse`
- **Errors**
  - `401` `{"error":"invalid_credentials","message":"Invalid email or password."}` (`auth.py:466`)
  - `403` `{"error":"email_not_verified","message":"Please verify your email before signing in. Check your inbox or request a new link.","email":"…"}` (`auth.py:478`)
  - `403` `{"error":"account_deactivated","message":"This account is deactivated. Contact support."}` (`auth.py:488`)
- **Side effects:** Bcrypt verify (constant-time even on unknown email — `dummy_verify` runs against a bogus hash). Issues access + refresh tokens, sets cookies.

### `POST /auth/token` — OAuth2 password flow (Swagger UI)
- **Auth:** public, form-encoded
- **Request:** `OAuth2PasswordRequestForm` (`username`, `password`)
- **Response 200:** `{access_token, refresh_token, token_type:"bearer"}`
- **Errors:** same as `/login`.

### `POST /auth/refresh` — Rotate refresh token
- **Auth:** Refresh token via cookie OR JSON body. Cookie wins.
- **Request:** `RefreshRequest` `{ refresh_token: str | null }` (optional). Cookie `vaktram_refresh` is the modern path.
- **Response 200:** `TokenResponse` (new access + refresh, cookie reset)
- **Errors**
  - `401` `"No refresh token provided"` (`auth.py:349`)
  - `401` `"Refresh token expired, please log in again"` (`auth.py:356`)
  - `401` `"Invalid refresh token"` (`auth.py:361`)
  - `401` `"Invalid token type"` (`auth.py:367`)
  - `401` `"Refresh token has been revoked, please log in again"` (`auth.py:374`)
  - `401` `"User not found or deactivated"` (`auth.py:387`)
- **Side effects:** Old `jti` revoked in Redis; new `jti` registered. Replay of revoked jti is detected and 401'd.

### `GET /auth/me` — Current user
- **Auth:** JWT
- **Response 200:** `UserProfileRead`
- **Errors:** `401` from auth dependency.

### `POST /auth/logout` — Revoke refresh + clear cookies
- **Auth:** public (intentional — lets expired-access clients still log out)
- **Request:** `{ refresh_token: str | null }` (optional). Cookie wins.
- **Response 204:** empty. Idempotent.
- **Side effects:** Clears `vaktram_refresh` + `vaktram_session` cookies. Revokes jti if valid; silent on invalid.

---

## Meetings — `/api/v1/meetings/*`

### `GET /meetings`
- **Auth:** JWT
- **Query:** `page` (`≥1`, default `1`), `page_size` (`1..100`, default `20`), `status` (filter on `MeetingStatus` enum)
- **Response 200:** `MeetingList { items: MeetingRead[], total, page, page_size }`

### `POST /meetings`
- **Auth:** JWT
- **Request:** `MeetingCreate` `{ title(max=500), meeting_url?, platform: MeetingPlatform=google_meet, scheduled_start?, scheduled_end?, auto_record=true, participants[] }`
- **Response 201:** `MeetingRead`

### `GET /meetings/{meeting_id}`
- **Auth:** JWT
- **Response 200:** `MeetingRead`
- **Errors:** `404 "Meeting not found"` (`routers/meetings.py:62`)

### `PATCH /meetings/{meeting_id}`
- **Auth:** JWT
- **Request:** `MeetingUpdate` (all fields optional)
- **Response 200:** `MeetingRead`
- **Errors:** `404 "Meeting not found"` (`meetings.py:79`)

### `DELETE /meetings/{meeting_id}`
- **Auth:** JWT
- **Response 204**
- **Errors:** `404 "Meeting not found"` (`meetings.py:93`)

### `GET /meetings/{meeting_id}/audio`
- **Auth:** JWT via `Authorization` OR `?token=` query (allows `<audio src>` tags)
- **Response 200:** binary audio stream (`audio/mpeg`)
- **Errors**
  - `401 "Not authenticated"` / `"Invalid token"` (`meetings.py:115,120,123`)
  - `404 "Audio not found"` (`meetings.py:132`)
  - `404 "Audio file missing from disk"` (`meetings.py:135`)

### `POST /meetings/upload-audio`
- **Auth:** JWT, `multipart/form-data`
- **Request:** `file: UploadFile`, `title: str=Uploaded Meeting`. Allowed MIME types: mp3, wav, flac, ogg, webm, mp4, m4a (audio + video). Filename extension whitelisted via `_safe_extension` (mp3/wav/flac/ogg/webm/mp4/m4a).
- **Response 201:** `MeetingRead`
- **Errors**
  - `400 "Unsupported file type: {ct}. Accepted: mp3, wav, flac, m4a, webm, mp4"` (`meetings.py:184`)
  - `400 "File too large. Maximum size is 100 MB."` (`meetings.py:192`)
  - `400 "File is empty."` (`meetings.py:194`)
  - `500 "Processing failed: {exc}"` if inline pipeline (dev fallback) errors (`meetings.py:256`)
- **Side effects:** Writes `/tmp/vaktram/uploads/{meeting_id}.{ext}`. Creates `Meeting` (status=processing). Publishes QStash transcribe job, or runs inline if QStash not configured.

---

## Transcripts — `/api/v1/transcripts/*`

### `GET /transcripts/{meeting_id}`
- **Auth:** JWT
- **Response 200:** `FullTranscript { meeting_id, segments: TranscriptSegmentRead[], total_segments }`. Each segment: `id, meeting_id, speaker_name, speaker_email?, content, start_time, end_time, sequence_number, confidence?, language=en, created_at`.
- **Errors:** `404 "Transcript not found"` (`routers/transcripts.py:32`)

### `POST /transcripts`
- **Auth:** JWT
- **Request:** `TranscriptBulkCreate { meeting_id, segments: TranscriptSegmentBase[] }`
- **Response 201:** `TranscriptSegmentRead[]`

### `DELETE /transcripts/{meeting_id}`
- **Auth:** JWT
- **Response 204** (idempotent)

---

## Summaries — `/api/v1/summaries/*`

### `GET /summaries/{meeting_id}`
- **Auth:** JWT
- **Response 200:** `SummaryRead { id, meeting_id, summary_text, action_items?, key_decisions?, topics?, sentiment?, model_used?, provider_used?, created_at, updated_at }`
- **Errors:** `404 "Summary not found"` (`routers/summaries.py:28`)

### `POST /summaries/generate`
- **Auth:** JWT
- **Request:** `SummaryGenerateRequest { meeting_id, provider?, model?, custom_prompt? }`
- **Response 201:** `SummaryRead`
- **Side effects:** Calls user's BYOM LLM. Records token usage.

### `DELETE /summaries/{meeting_id}`
- **Auth:** JWT
- **Response 204**
- **Errors:** `404 "Summary not found"` (`summaries.py:59`)

---

## Search — `/api/v1/search`

### `POST /search`
- **Auth:** JWT
- **Request:** `SearchRequest { query: str(min=1,max=1000), top_k: int(1..50)=10 }`
- **Response 200:** `SearchResponse { results: SearchResultItem[], query, total }`. Each item: `meeting_id, meeting_title, segment_id, content, speaker_name, score, start_time, end_time`.
- **Side effects:** Hybrid: Postgres FTS + pgvector cosine, RRF-fused.

---

## Bot — `/api/v1/bot/*`

### `POST /bot/join`
- **Auth:** JWT
- **Request:** `BotJoinRequest { meeting_id, meeting_url? }`
- **Response 200:** `BotStatusResponse { meeting_id, bot_id, status, message }`

### `POST /bot/leave/{meeting_id}`
- **Auth:** JWT
- **Response 200:** `BotStatusResponse`

### `GET /bot/status/{meeting_id}`
- **Auth:** JWT
- **Response 200:** `BotStatusResponse`

### `POST /bot/schedule`
- **Auth:** JWT
- **Request:** `ScheduleBotRequest { meeting_id, deploy_at? }` (defaults to 30 s before scheduled_start)
- **Response 201:** `ScheduledJobRead`
- **Errors**
  - `404 "Meeting not found"` (`routers/bot.py:103`)
  - `400 "Meeting has no URL"` (`bot.py:105`)

### `GET /bot/scheduled-jobs`
- **Auth:** JWT
- **Query:** `status?` (filter)
- **Response 200:** `ScheduledJobRead[]`

---

## AI Config (BYOM) — `/api/v1/ai-config/*`

### `GET /ai-config`
- **Auth:** JWT
- **Response 200:** `AIConfigRead[]` — one row per saved provider/model. `has_api_key: bool` indicates whether an encrypted key is stored.

### `GET /ai-config/status`
- **Auth:** JWT
- **Response 200:** `{ configured: bool, provider?, model?, is_default? }`

### `POST /ai-config`
- **Auth:** JWT
- **Request:** `AIConfigCreate { provider(max=50), model_name(max=100), api_key?, base_url?, extra_config?, is_default=false, is_active=true }`. `extra_config` can hold `api_version` (Azure), `aws_region_name`/`aws_access_key_id`/`aws_secret_access_key` (Bedrock), `vertex_project`/`vertex_location`/`vertex_credentials` (Vertex).
- **Response 201:** `AIConfigRead`
- **Side effects:** Encrypts `api_key` with Fernet (`services/encryption_service.py:30`). Demotes other defaults if `is_default=true`.

### `PATCH /ai-config/{config_id}`
- **Auth:** JWT
- **Request:** `AIConfigUpdate` (all optional)
- **Response 200:** `AIConfigRead`
- **Errors:** `404 "AI config not found"` (`routers/ai_config.py:125`)

### `DELETE /ai-config/{config_id}`
- **Auth:** JWT
- **Response 204**
- **Errors:** `404 "AI config not found"` (`ai_config.py:161`)

### `POST /ai-config/test`
- **Auth:** JWT
- **Request:** `AIConfigTestRequest` (provider/model/key/base_url/extra)
- **Response 200:** `AIConfigTestResponse { success: bool, message: str, response_time_ms? }`. **Returns 200 even on failure** with `success=false`.

---

## Analytics — `/api/v1/analytics/*`

### `GET /analytics/overview`
- **Auth:** JWT
- **Response 200:** `{ total_meetings, completed_meetings, total_duration_hours, avg_duration_minutes, meetings_this_week }`

### `GET /analytics/usage`
- **Auth:** JWT
- **Response 200:** `{ meetings_this_month, storage_used_mb, plan }`

### `GET /analytics/talk-time`
- **Auth:** JWT
- **Response 200:** top-20 `[{ speaker_name, total_seconds, meeting_count, percentage }]`

### `GET /analytics/frequency`
- **Auth:** JWT
- **Query:** `period: ^(7d|30d|90d)$ = 30d`
- **Response 200:** `[{ date: "YYYY-MM-DD", count }]`

### `GET /analytics/topics`
- **Auth:** JWT
- **Response 200:** top-20 `[{ topic, count }]`

---

## Notifications — `/api/v1/notifications/*`

### `GET /notifications`
- **Auth:** JWT
- **Response 200:** last-50 `[{ id, title, body?, notification_type, is_read, link?, created_at }]`

### `PATCH /notifications/{notification_id}/read`
- **Auth:** JWT
- **Response 200:** `NotificationRead`
- **Errors:** `404 "Notification not found"` (`routers/notifications.py:48`)

### `POST /notifications/read-all`
- **Auth:** JWT
- **Response 200:** `{ status:"ok", message }`

---

## Teams — `/api/v1/teams/*`

### `GET /teams/organization`
- **Auth:** JWT
- **Response 200:** `OrganizationRead { id, name, slug, logo_url?, max_seats, created_at, updated_at }`
- **Errors:** `404 "User has no organization"` / `"Organization not found"` (`routers/teams.py:40,46`)

### `POST /teams/organization`
- **Auth:** JWT
- **Request:** `OrganizationCreate { name(max=255), slug(max=255), logo_url?, max_seats=5 }`
- **Response 201:** `OrganizationRead`

### `GET /teams/members`
- **Auth:** JWT
- **Response 200:** `UserProfileRead[]`
- **Errors:** `404 "User has no organization"` (`teams.py:80`)

### `GET /teams/profile`
- **Auth:** JWT — **Response 200:** `UserProfileRead`

### `PATCH /teams/profile`
- **Auth:** JWT
- **Request:** `UserProfileUpdate { full_name?, avatar_url?, role?, onboarding_completed?, timezone?(max=100), language?(max=10) }`
- **Response 200:** `UserProfileRead`

### `POST /teams/invite`
- **Auth:** JWT (admin/owner)
- **Request:** `InviteMemberRequest { email(max=255), role(max=50)=member }`
- **Response 201:** `{ status:"ok", message }`
- **Errors**
  - `400 "You must belong to an organization first"` (`teams.py:118`)
  - `403 "Only admins can invite members"` (`teams.py:120`)
  - `404 "Organization not found"` (`teams.py:128`)
  - `400 "Organization has reached its seat limit ({n})"` (`teams.py:135`)
  - `409 "User is already a member"` (`teams.py:146`)

### `PATCH /teams/members/{member_id}`
- **Auth:** JWT (admin/owner)
- **Request:** `UpdateMemberRoleRequest { role(max=50) }`
- **Errors**
  - `403 "Only admins can update roles"` (`teams.py:177`)
  - `404 "Member not found"` (`teams.py:187`)

### `DELETE /teams/members/{member_id}`
- **Auth:** JWT (admin/owner)
- **Errors**
  - `403 "Only admins can remove members"` (`teams.py:202`)
  - `400 "Cannot remove yourself"` (`teams.py:204`)
  - `404 "Member not found"` (`teams.py:214`)

---

## Calendar — `/api/v1/calendar/*`

### `GET /calendar/connections`
- **Auth:** JWT — `[{ id, provider, calendar_id?, is_active, created_at }]`

### `POST /calendar/authorize`
- **Auth:** JWT
- **Response 200:** `{ authorization_url: str }`
- **Errors:** `503 "Google Calendar integration is not configured"` (`routers/calendar.py:45`)

### `GET /calendar/callback`
- **Auth:** public (state contains user_id)
- **Query:** `code`, `state`
- **Response 302:** redirect to `${frontend_base_url}/settings?status=connected&provider=google` or `?status=error&message=...`

### `POST /calendar/sync`
- **Auth:** JWT — manually trigger sync. Response: `{ synced_count, new_meetings }`

### `DELETE /calendar/{connection_id}`
- **Auth:** JWT — `204`
- **Errors:** `404 "Calendar connection not found"` (`calendar.py:107`)

---

## Webhooks (Inbound) — `/api/v1/webhooks/*`

### `POST /webhooks/google-calendar`
- **Auth:** public (Google verifies via channel token)
- **Headers:** `x-goog-channel-id`, `x-goog-resource-id`, `x-goog-resource-state`
- **Response 200:** `{ status }`
- **Errors:** `400 "Missing channel ID header"` (`routers/webhooks.py:39`)

### `POST /webhooks/bot-events`
- **Auth:** **X-Bot-Auth**
- **Request:** `{ event: str, meeting_id: str, error?: str }`
- **Response 200:** `{ status:"ok" }`
- **Errors**
  - `400 "Invalid webhook payload"` (`webhooks.py:64`)
  - `404 "Meeting not found"` (`webhooks.py:74`)

---

## Internal pipeline — `/internal/*` (no `/api/v1` prefix)

### `POST /internal/pipeline/transcribe/{meeting_id}`
- **Auth:** **Upstash-Signature**
- **Response 200:** `{ status:"ok", segments:int, next_stage:"summarizing" }`
- **Errors**
  - `404 "Meeting not found"` (`routers/internal.py:100`)
  - `400 "Meeting has no audio file"` (`internal.py:103`)
  - `500` on transcription/embedding failure (`internal.py:215`)
- **Side effects:** Groq Whisper + optional pyannote diarization. Writes `TranscriptSegment[]`. Indexes embeddings if BYOM key set. Publishes `summarize` job. Broadcasts WS status.

### `POST /internal/pipeline/summarize/{meeting_id}`
- **Auth:** **Upstash-Signature**
- **Response 200:** `{ status:"ok", next_stage:"done" }`
- **Errors**
  - `404 "Meeting not found"` (`internal.py:232`)
  - `500` on LLM failure (`internal.py:378`)
- **Side effects:** Loads `UserAIConfig`, Fernet-decrypts key in memory. Calls user's LLM. Persists `MeetingSummary` + topic-tracker scan + Slack post + outbound webhook + email + notification. Updates meeting status to `completed`.

### `POST /internal/meetings/{meeting_id}/audio-ready`
- **Auth:** **X-Bot-Auth**
- **Request:** `AudioReadyRequest { audio_storage_path: str, user_id: UUID }`
- **Response 200:** `{ status:"ok", next_stage:"transcribing" }`

### `POST /internal/meetings/{meeting_id}/transcription-complete`
- **Auth:** **X-Bot-Auth**
- **Request:** `{ segment_count: int>=0 }`
- **Response 200:** `{ status:"ok", next_stage:"summarizing" }`

### `POST /internal/meetings/{meeting_id}/summarization-complete`
- **Auth:** **X-Bot-Auth**
- **Request:** empty
- **Response 200:** `{ status:"ok", next_stage:"done" }`

### `POST /internal/meetings/{meeting_id}/pipeline-error`
- **Auth:** **X-Bot-Auth**
- **Request:** `{ stage: str, error: str }`
- **Response 200:** `{ status:"ok", stage, result:"failed" }`

---

## Billing — `/api/v1/billing/*`

### `GET /billing/plans`
- **Auth:** public
- **Response 200:** map of `PlanTier → { name, monthly_price_cents, seat_limit, features, limits: {UsageKind:int} }`

### `GET /billing/subscription`
- **Auth:** JWT
- **Response 200:** `SubscriptionRead { plan, status, seats, trial_ends_at?, current_period_start?, current_period_end?, cancel_at_period_end }`
- **Errors:** `403 "User has no organization"` (`routers/billing.py:51`)

### `GET /billing/usage`
- **Auth:** JWT
- **Response 200:** `UsageSummary { plan, period_start, entries: [{ kind, used, limit, remaining }] }` where `kind` ∈ {`transcription_minutes`, `llm_input_tokens`, `llm_output_tokens`, `bot_minutes`, `storage_gb_hours`, `seats`}
- **Errors:** `403 "User has no organization"` (`billing.py:69`)

### `POST /billing/checkout`
- **Auth:** JWT (admin/owner)
- **Request:** `CheckoutRequest { plan: PlanTier, seats(1..10000)=1, success_url, cancel_url }`
- **Response 201:** `{ url }`
- **Errors**
  - `403 "User has no organization"` (`billing.py:102`)
  - `403 "Only admins can manage billing"` (`billing.py:104`)
  - `503` Stripe failure (`billing.py:116`)

### `POST /billing/portal`
- **Auth:** JWT (admin/owner)
- **Request:** `PortalRequest { return_url }`
- **Response 201:** `{ url }`
- **Errors:** `403 "Only admins can manage billing"` (`billing.py:126`); `503` Stripe failure (`billing.py:133`)

### `POST /billing/webhook`
- **Auth:** **Stripe-Signature**
- **Response 200:** `{ received: true }`
- **Errors:** `400 "Missing Stripe-Signature header"` (`billing.py:145`); `400 "Invalid signature"` (`billing.py:151`)
- **Side effects:** Dispatches `customer.subscription.*` to `apply_subscription_event` and `invoice.paid|payment_failed|finalized` to `record_invoice`.

---

## SSO — `/api/v1/sso/*`

### `GET /sso/lookup`
- **Auth:** public
- **Query:** `email`
- **Response 200:** `{ sso: bool, type?: "saml"|"oidc", init_url? }`

### `GET /sso/init`
- **Auth:** public
- **Query:** `email`
- **Response 302:** redirect to IdP
- **Errors**
  - `404 "No SSO connection for this email domain"` (`routers/sso.py:42`)
  - `503 "SAML provider library not installed on this deployment"` (`sso.py:61`)
  - `501 "OIDC start not yet implemented in self-hosted mode"` (`sso.py:75`)
  - `400 "Unsupported SSO type: {type}"` (`sso.py:77`)

### `POST /sso/saml/acs`
- **Auth:** public; assertion signature validated by `onelogin`
- **Request:** form-encoded SAML response
- **Response 302:** `${frontend_base_url}/auth/sso-callback#access=...&refresh=...`
- **Errors**
  - `503 "SAML provider library not installed"` (`sso.py:86`)
  - `400 "Missing email in assertion"` (`sso.py:91`)
  - `403 "No SSO connection for this domain"` (`sso.py:94`)

---

## SCIM 2.0 — `/api/v1/scim/v2/*`

All routes require `Authorization: Bearer <scim_token>`. Tokens are hashed in `scim_tokens`; constant-time compare.

### `GET /scim/v2/Users`
- **Query:** `startIndex=1`, `count=100`, `filter` (supports `userName eq "<email>"`)
- **Response 200:** SCIM `ListResponse` with `Resources: User[]`
- **Errors:** `401 "Missing SCIM bearer token"` / `"Invalid SCIM token"` (`routers/scim.py:30,36`)

### `POST /scim/v2/Users`
- **Request:** SCIM `User` `{ userName: email, name?:{formatted}, active?=true }`
- **Response 201:** SCIM `User`
- **Errors:** `400 "userName required"` (`scim.py:87`)

### `PATCH /scim/v2/Users/{user_id}`
- **Request:** SCIM PatchOp `{ Operations: [{op:"replace", path: "active"|"userName"|"name.formatted", value }] }`
- **Errors:** `404 "User not found"` (`scim.py:118`)

### `DELETE /scim/v2/Users/{user_id}`
- **Response 204** (soft delete: `is_active=false`)
- **Errors:** `404 "User not found"` (`scim.py:139`)

---

## Compliance — `/api/v1/compliance/*`

### `GET /compliance/retention`
- **Auth:** JWT
- **Response 200:** `{ default_days, legal_hold, audio_days?, transcript_days?, summary_days? }` (defaults `{365, false}`)
- **Errors:** `403 "No org"` (`routers/compliance.py:40`)

### `PUT /compliance/retention`
- **Auth:** JWT + `require_permission(P_TEAM_MANAGE)`
- **Request:** any of `default_days`, `audio_days`, `transcript_days`, `summary_days`, `legal_hold`
- **Response 200:** `RetentionPolicy`
- **Errors:** `403 "No org"` (`compliance.py:56`); `403` if missing permission

### `GET /compliance/audit`
- **Auth:** JWT + `require_permission(P_AUDIT_READ)`
- **Query:** `limit=100`, `after?` (cursor; not yet implemented)
- **Response 200:** `[{ id, user_id?, action, resource_type, resource_id, ip, ts, details }]` (omits `row_hash`/`prev_hash`)

### `GET /compliance/audit/verify`
- **Auth:** JWT + `require_permission(P_AUDIT_READ)`
- **Response 200:** result of `audit_service.verify_chain(db)` (hash-chain integrity check)

### `PUT /compliance/byok`
- **Auth:** JWT + `require_permission(P_TEAM_MANAGE)`
- **Request:** `{ provider:"aws"|"gcp"|"azure", key_arn }`
- **Response 200:** `{ provider, key_arn, enabled }`
- **Errors:** `403 "No org"` (`compliance.py:114`); `400 "provider and key_arn required"` (`compliance.py:118`)

### `POST /compliance/export`
- **Auth:** JWT
- **Response 200:** `{ id, status:"pending"|"in_progress"|"ready"|"failed" }`
- **Errors:** `403 "No org"` (`compliance.py:143`)

### `DELETE /compliance/me`
- **Auth:** JWT
- **Response 204**
- **Side effects:** GDPR right-to-erasure: deactivates user, scrubs PII (email→`deleted-{id}@example.invalid`, name/avatar/password cleared). Audit rows retained with `user_id=null`.

---

## Ask (RAG) — `/api/v1/ask/*`

### `POST /ask/threads`
- **Auth:** JWT
- **Request:** `CreateThreadRequest { title?, scope: "meeting"|"channel"|"organization"=organization, scope_id? }`
- **Response 201:** `{ id, title?, scope }`

### `GET /ask/threads`
- **Auth:** JWT
- **Query:** `limit=30`
- **Response 200:** `[{ id, title?, scope, created_at }]`

### `GET /ask/threads/{thread_id}`
- **Auth:** JWT
- **Response 200:** `{ id, title?, scope, scope_id?, messages: [{ id, role, content, citations[], created_at }] }`
- **Errors:** `404 "Thread not found"` (`routers/ask.py:75`)

### `POST /ask/threads/{thread_id}/messages`
- **Auth:** JWT
- **Request:** `AskRequest { message: str(min=1,max=4000) }`
- **Response 200:** assistant message `{ id, role, content, citations[] }`
- **Errors**
  - `404 "Thread not found"` (`ask.py:108`)
  - `412 {"error":"no_ai_config","message":"…"}` (`ask.py:120`)

---

## Topics — `/api/v1/topics/*`

### `GET /topics`
- **Auth:** JWT — `[{ id, name, keywords[], is_active, notify_emails[] }]`

### `POST /topics`
- **Auth:** JWT
- **Request:** `TrackerCreate { name(min=1,max=120), keywords: str[](min=1), notify_emails=[] }`
- **Errors:** `403 "No organization"` (`routers/topics.py:63`)

### `PATCH /topics/{tracker_id}`
- **Request:** `TrackerUpdate` (all optional)
- **Errors:** `404 "Tracker not found"` (`topics.py:84`)

### `DELETE /topics/{tracker_id}`
- **Errors:** `404 "Tracker not found"` (`topics.py:105`)

### `GET /topics/{tracker_id}/hits`
- **Query:** `limit=100`
- **Response 200:** `[{ id, meeting_id, matched_keyword, snippet, timestamp, created_at }]`
- **Errors:** `404 "Tracker not found"` (`topics.py:120`)

---

## Channels — `/api/v1/channels/*`

### `GET /channels` — `JWT` — `[{ id, name, slug, is_private, description? }]`

### `POST /channels`
- **Request:** `ChannelCreate { name(min=1,max=120), description?, is_private=false }`
- **Errors:** `403 "No organization"` (`routers/channels.py:61`)

### `POST /channels/{channel_id}/meetings/{meeting_id}` — add meeting
- **Response 204** (idempotent)
- **Errors:** `404 "Channel not found"` (`channels.py:85`)

### `DELETE /channels/{channel_id}`
- **Errors:** `404 "Channel not found"` (`channels.py:103`)

---

## Soundbites — `/api/v1/soundbites/*`

### `POST /soundbites`
- **Auth:** JWT
- **Request:** `SoundbiteCreate { meeting_id, start_seconds(>=0), end_seconds(>0), title?, transcript? }`
- **Response 201:** `{ id, share_token, share_url:"/s/{token}" }`
- **Errors**
  - `400 "end_seconds must be > start_seconds"` (`routers/soundbites.py:36`)
  - `404 "Meeting not found"` (`soundbites.py:39`)
  - `403 "No access to this meeting"` (`soundbites.py:41`)

### `GET /soundbites/by-meeting/{meeting_id}` — `JWT` — `[{ id, title?, start, end, transcript?, share_url? }]`

### `GET /soundbites/shared/{share_token}` — **public**
- **Response 200:** `{ title?, start, end, transcript? }`
- **Errors:** `404 "Not found"` (`soundbites.py:93`)

---

## Integrations — `/api/v1/integrations/*`

### `GET /integrations` — `JWT` — `[{ provider, is_active, channel?, configured_at }]` (webhook URL never exposed)

### `PUT /integrations/slack`
- **Request:** `SlackConfigRequest { webhook_url: HttpUrl, channel? }`
- **Response 200:** `{ provider:"slack", is_active:true, channel? }`
- **Errors:** `403 "No organization"` (`routers/integrations.py:51`)

### `DELETE /integrations/slack` — `204` (idempotent)

---

## Outbound webhooks — `/api/v1/webhooks-out/*`

### `GET /webhooks-out/events` — public — `WebhookEvent[]` (`meeting.scheduled`, `meeting.started`, `meeting.completed`, `summary.ready`, `transcript.ready`, `topic.hit`)

### `GET /webhooks-out` — `JWT` — `EndpointRead[]` (secret never returned after create)

### `POST /webhooks-out`
- **Request:** `EndpointCreate { url: HttpUrl, events: str[]=[]  // "*" = all, description? }`
- **Response 201:** `EndpointRead` including the **one-time** `secret`.
- **Errors**
  - `403 "No organization"` (`routers/webhooks_outbound.py:80`)
  - `400 "Unknown event types: [...]"` (`webhooks_outbound.py:84`)

### `DELETE /webhooks-out/{endpoint_id}`
- **Errors:** `404 "Endpoint not found"` (`webhooks_outbound.py:114`)

### `GET /webhooks-out/{endpoint_id}/deliveries`
- **Query:** `limit=50`
- **Response 200:** `[{ id, event, status:"pending"|"success"|"failed", attempts, last_status_code?, last_error?, next_retry_at?, created_at }]`
- **Errors:** `404 "Endpoint not found"` (`webhooks_outbound.py:129`)

---

## WebSocket — `/ws/meetings/{meeting_id}`

- **Auth:** WebSocket (no explicit auth dependency; per-meeting subscription).
- **Handshake:** Client opens WS to `/ws/meetings/{meeting_id}`. Server adds it to `ConnectionManager.active_connections[meeting_id]`.
- **Server → client:** JSON status frames as the pipeline progresses (`scheduled`, `transcribing`, `summarizing`, `completed`, `failed`).
- **Client → server:** Anything (used as keepalive). `WebSocketDisconnect` removes the client.

---

## Error code reference (auth-related, structured)

These are the structured error shapes the frontend keys on. Other 4xx/5xx return plain string `detail`.

| Code | Where | Trigger |
|---|---|---|
| `email_exists` | `/auth/signup` | 409 — email already verified |
| `invalid_credentials` | `/auth/login` | 401 — wrong password OR unknown email (constant-time) |
| `email_not_verified` | `/auth/login` | 403 — verified flag still null |
| `account_deactivated` | `/auth/login` | 403 — `is_active=false` |
| `invalid_or_expired_token` | `/auth/verify-email` | 400 — verification token consumed/expired |
| `no_ai_config` | `/ask/threads/{id}/messages` | 412 — user hasn't set up BYOM |
