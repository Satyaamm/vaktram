# Vaktram Demo Guide

## What is Vaktram?

Vaktram is an AI-powered meeting intelligence platform. It records meetings, transcribes them with speaker identification, and generates AI summaries, action items, and key decisions -- automatically.

**Core differentiators:**

- **BYOM (Bring Your Own Model)** -- Users plug in their own LLM API key (Gemini, OpenAI, Claude). No vendor lock-in.
- **Self-hosted bot** -- Audio never touches third-party servers. Your data stays on your infrastructure.
- **Speaker diarization** -- Knows who said what, not just what was said.
- **Event-driven pipeline** -- Groq Whisper for transcription, Gemini for summarization, QStash for async processing.

---

## Complete Feature List

### 1. Upload and Transcribe

Upload any audio or video file and get a full transcript with AI-generated summary.

- **Supported formats:** MP3, WAV, FLAC, M4A, WebM, MP4
- **Max file size:** 100 MB
- **Transcription engine:** Groq Whisper (whisper-large-v3-turbo)
- **Processing time:** ~30 seconds for a 1-hour recording

**API endpoint:** `POST /api/v1/meetings/upload-audio`

**What the user gets:**
- Timestamped transcript with speaker labels
- AI-generated summary (3-5 paragraphs)
- Action items with assignees, deadlines, and priority
- Key decisions with context

---

### 2. Bot Joins Live Meeting

A recording bot joins Google Meet calls in real-time, records everything, and processes it automatically.

- **Bot name:** "Vaktram Notetaker" (appears as a participant)
- **Camera:** Off
- **Microphone:** Off
- **Platform:** Google Meet (Zoom and Teams planned)
- **Technology:** Playwright + PulseAudio + FFmpeg in Docker

**How it works:**
1. User clicks "Record" on a meeting
2. API sends request to bot service
3. Bot launches headless Chromium, navigates to the Meet URL
4. Mutes mic/camera, enters display name, clicks "Join"
5. PulseAudio captures browser audio in 30-second PCM chunks
6. When meeting ends: chunks are concatenated, converted to FLAC
7. Audio is sent to API, pipeline processes it automatically

**API endpoints:**
- `POST /api/v1/bot/join` -- Send bot to a meeting
- `POST /api/v1/bot/leave/{meeting_id}` -- Remove bot from meeting
- `GET /api/v1/bot/status/{meeting_id}` -- Check bot status

---

### 3. Calendar Integration and Auto-Record

Connect Google Calendar to automatically detect and record meetings.

- **OAuth2 flow** -- Secure token exchange, encrypted storage
- **Auto-sync** -- Every 5 minutes, calendar events are synced to Vaktram
- **Auto-record** -- When enabled, the bot joins meetings 30 seconds before they start
- **Webhook support** -- Google Calendar push notifications for real-time updates

**How auto-record works:**
1. User connects Google Calendar in Settings
2. Calendar events sync as meetings in Vaktram
3. User enables "Auto-record" on meetings they want captured
4. APScheduler scans every 60 seconds for meetings starting soon
5. Bot is deployed 30 seconds before the meeting starts
6. User walks in -- bot is already there recording

**API endpoints:**
- `POST /api/v1/calendar/authorize` -- Start OAuth flow
- `GET /api/v1/calendar/connections` -- List connected calendars
- `POST /api/v1/calendar/sync` -- Manual sync trigger
- `DELETE /api/v1/calendar/{connection_id}` -- Disconnect calendar

---

### 4. Speaker Diarization

Identifies and labels different speakers in the audio using pyannote.audio.

- **Model:** pyannote.audio 3.1 (state-of-the-art speaker diarization)
- **Output:** Speaker segments with start/end times
- **Integration:** Diarization runs in parallel with transcription, then speakers are assigned to transcript segments based on temporal overlap

**Example output:**
```
[Speaker A] (0.0s - 12.5s): Let's discuss the Q3 budget allocation.
[Speaker B] (12.8s - 24.1s): I think we should increase marketing spend by 15%.
[Speaker A] (24.5s - 35.2s): That makes sense. What about the engineering headcount?
[Speaker C] (35.8s - 48.0s): We need at least two more backend engineers.
```

---

### 5. AI Summary and Action Items

LLM-powered analysis of meeting transcripts using LiteLLM (Gemini 2.0 Flash by default).

**Three parallel AI calls:**

1. **Summary** -- Concise 3-5 paragraph overview with logical sections
2. **Action Items** -- Extracted tasks with:
   - Task description
   - Assignee (from speaker labels)
   - Deadline (if mentioned)
   - Priority (high/medium/low)
3. **Key Decisions** -- What was decided, context, and who made the decision

**Example action items output:**
```json
[
  {"task": "Prepare Q3 budget proposal", "assignee": "Speaker A", "deadline": "Next Friday", "priority": "high"},
  {"task": "Schedule interviews for backend engineers", "assignee": "Speaker C", "deadline": "This week", "priority": "medium"}
]
```

---

### 6. BYOM (Bring Your Own Model)

Users can configure their own LLM provider and API key.

- **Supported providers:** OpenAI, Google Gemini, Anthropic Claude, and any LiteLLM-compatible provider
- **Per-user config** -- Each user can set their own model
- **Test before save** -- Validate API key and model with a test call
- **Default model:** Gemini 2.0 Flash (free tier)

**API endpoints:**
- `GET /api/v1/ai-config` -- List configured models
- `POST /api/v1/ai-config` -- Add a new model config
- `POST /api/v1/ai-config/test` -- Test a model config
- `PATCH /api/v1/ai-config/{id}` -- Update config
- `DELETE /api/v1/ai-config/{id}` -- Remove config

---

### 7. Semantic Search

Search across all meeting transcripts using natural language queries.

- **Full-text search** across all transcript segments
- **Results include:** Meeting title, speaker name, content snippet, timestamp, relevance score
- **Search scope:** All meetings owned by the user

**Example:**
- Query: "budget discussion"
- Result: Meeting "Q3 Planning" -- Speaker A at 2:15 -- "Let's discuss the Q3 budget allocation..."

**API endpoint:** `POST /api/v1/search` with `{ "query": "...", "top_k": 10 }`

---

### 8. Team and Organization Management

Multi-tenant organization support with role-based access.

- **Auto-org creation** -- Organization is created automatically on signup
- **Roles:** Owner, Admin, Member, Viewer
- **Invite flow** -- Invite by email, placeholder user created, completed on signup
- **Seat limits** -- Configurable max seats per organization
- **Shared library** -- All org members see shared meetings

**API endpoints:**
- `GET /api/v1/teams/members` -- List team members
- `POST /api/v1/teams/invite` -- Invite by email
- `PATCH /api/v1/teams/members/{id}` -- Change role
- `DELETE /api/v1/teams/members/{id}` -- Remove member

---

### 9. Real-Time Notifications

WebSocket-based real-time updates and in-app notifications.

- **Pipeline status** -- Live updates as meeting progresses through stages:
  `recording -> transcribing -> summarizing -> completed`
- **In-app notifications** -- Bell icon with unread count
- **Notification types:** Recording complete, transcription done, summary ready, errors

**WebSocket:** `ws://api:8000/ws/{meeting_id}`

**API endpoints:**
- `GET /api/v1/notifications` -- List notifications
- `PATCH /api/v1/notifications/{id}/read` -- Mark as read
- `POST /api/v1/notifications/read-all` -- Mark all as read

---

### 10. Analytics Dashboard

Meeting intelligence analytics for users and teams.

- **Overview stats:** Total meetings, hours recorded, avg duration, meetings this week
- **Speaker talk-time:** Who talks the most across meetings (with percentages)
- **Meeting frequency:** Chart of meetings per day over 7/30/90 days
- **Topic trends:** Most discussed topics extracted from summaries
- **Usage tracking:** Meetings this month, storage used, plan info

**API endpoints:**
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/talk-time`
- `GET /api/v1/analytics/frequency?period=30d`
- `GET /api/v1/analytics/topics`
- `GET /api/v1/analytics/usage`

---

### 11. Scheduled Bot Deployment

Schedule a bot to join a future meeting at a specific time.

- **APScheduler** with SQLAlchemy job store (survives server restarts)
- **Job tracking** -- Status, execution time, errors, retries
- **Auto-cleanup** -- Completed jobs older than 30 days are purged daily

**API endpoints:**
- `POST /api/v1/bot/schedule` -- Schedule a bot deployment
- `GET /api/v1/bot/scheduled-jobs` -- List scheduled jobs with status filter

---

### 12. Custom JWT Authentication

Fully custom auth system -- no third-party auth provider dependency.

- **Signup/Login** -- Email + password (bcrypt hashed)
- **JWT tokens** -- 15-minute access token, 1-day refresh token
- **Auto-refresh** -- Frontend automatically refreshes expired tokens
- **Route protection** -- Next.js middleware checks cookie for protected routes

---

## Full UI Walkthrough (Step-by-Step)

Everything below is done entirely from the browser -- no terminal, no curl commands.

---

### Step 1: Create Account

1. Open `http://localhost:3000`
2. Click **Sign Up**
3. Enter full name, email, and password
4. Click **Create Account**
5. You are redirected to the **Dashboard**
6. Your organization is auto-created. You are the admin.

---

### Step 2: Explore the Dashboard

1. The dashboard shows:
   - **Stats cards**: Total meetings, hours recorded, average duration, meetings this week
   - **Recent meetings**: Empty for now
2. The **sidebar** has: Dashboard, Meetings, Search, Analytics, Team, Settings

---

### Step 3: Upload an Audio Recording

1. Click **Meetings** in the sidebar
2. Click the **Upload Audio** button (top-right, next to "New Meeting")
3. In the dialog:
   - Enter a title (e.g., "Q3 Planning Discussion")
   - Click the upload area to select an audio file (MP3, WAV, FLAC, M4A, WebM, or MP4, up to 100 MB)
   - Click **Upload & Transcribe**
4. You are redirected to the meeting detail page
5. The pipeline runs automatically:
   - `processing` -> `transcribing` -> `summarizing` -> `completed`
6. Once complete, explore the three tabs:
   - **Transcript** -- Timestamped transcript with speaker labels (Speaker A, Speaker B, etc.)
   - **Summary** -- AI-generated 3-5 paragraph overview
   - **Action Items** -- Extracted tasks with assignee, deadline, and priority

---

### Step 4: Create a Meeting and Record with Bot

1. Go to **Meetings** page
2. Click **New Meeting**
3. Fill in:
   - Title: "Team Standup"
   - Platform: Google Meet
   - Meeting URL: paste your Google Meet link
   - Scheduled date/time: set to a few minutes from now
4. Click **Create Meeting**
5. Click on the newly created meeting to open it
6. Click the red **Record** button (appears when meeting has a URL and is in "scheduled" status)
7. The bot ("Vaktram Notetaker") joins the Google Meet call
8. When done, click **Stop Recording**
9. The pipeline processes automatically -- transcript + summary appear in the tabs

---

### Step 5: Calendar Integration (Auto-Record)

1. Click **Settings** in the sidebar
2. Go to the **Calendar** tab
3. Click **Connect Google Calendar**
4. Complete the Google OAuth flow
5. Your calendar events sync as meetings in Vaktram
6. Enable **Auto-record** on meetings you want captured
7. The bot will join automatically 30 seconds before the meeting starts -- no manual action needed

---

### Step 6: Search Across Meetings

1. Click **Search** in the sidebar
2. Type a query like "budget" or "deadline" or "action items"
3. Results show:
   - Meeting title
   - Speaker name
   - Exact transcript snippet with the matching text highlighted
   - Timestamp link -- click to jump to that moment in the audio
4. Filter results by: Transcripts, Summaries, Action Items (toggle badges)

---

### Step 7: Configure AI Model (BYOM)

1. Click **Settings** in the sidebar
2. Go to the **AI Config** tab
3. Add your own LLM provider:
   - Provider: OpenAI, Gemini, or Claude
   - API Key: paste your key
   - Model name: e.g., "gpt-4o" or "claude-sonnet-4-20250514"
4. Click **Test** to validate the key works
5. Click **Save**
6. All future summaries will use your chosen model

---

### Step 8: Invite Team Members

1. Click **Team** in the sidebar
2. Click **Invite Member**
3. Enter the email address and select a role (Admin, Member, or Viewer)
4. Click **Send Invite**
5. The invited person receives the invite and can sign up
6. All team members see the shared meeting library

---

### Step 9: View Analytics

1. Click **Analytics** in the sidebar (or view stats on the Dashboard)
2. See:
   - **Overview**: Total meetings, hours recorded, avg duration
   - **Speaker Talk-Time**: Who talks the most across meetings (with percentages)
   - **Meeting Frequency**: Chart of meetings per day
   - **Topic Trends**: Most discussed topics extracted from summaries
   - **Usage**: Meetings this month, storage used

---

### Step 10: Notifications

1. The **bell icon** in the top-right header shows real-time notifications
2. Notification types:
   - Recording complete
   - Transcription done
   - Summary ready
   - Errors
3. Click a notification to navigate to the meeting
4. Click **Mark all read** to clear the badge

---

### Step 11: Profile and Settings

1. Click **Settings** in the sidebar
2. Tabs available:
   - **Profile**: Update name, email, avatar
   - **AI Config**: BYOM model configuration
   - **Calendar**: Connect/disconnect Google Calendar
   - **Notifications**: Notification preferences
   - **Billing**: View plan and usage

---

## Demo Script (7 Minutes)

### Setup Before Demo

1. API server running (`uvicorn app.main:app --port 8000`)
2. Frontend running (`npm run dev` in apps/web, port 3000)
3. Groq API key and Gemini API key configured in `.env`
4. Prepare a 3-5 minute sample audio file with 2-3 speakers
5. (Optional) Docker running with bot service for live meeting demo

---

### Scene 1: The Problem (30 seconds)

> "You just finished a 45-minute product meeting. Someone was supposed to take notes -- they didn't. Important decisions are already being forgotten. Action items are vague. By Friday, half the team won't remember what was agreed on."
>
> "Vaktram fixes this."

---

### Scene 2: Sign Up and Dashboard (30 seconds)

1. Open the app at `http://localhost:3000`, click **Sign Up**
2. Create an account -- show the clean dashboard with stats cards
3. "Your organization was created automatically. You're the admin."

---

### Scene 3: Upload a Recording (2 minutes)

1. Go to **Meetings** page, click **Upload Audio**
2. Select a pre-prepared audio file, give it a title, click **Upload & Transcribe**
3. You land on the meeting detail page -- show the status changing in real-time
4. Once completed, show the three tabs:
   - **Transcript** -- "Notice the speaker labels. Speaker A, Speaker B -- the AI identified who said what."
   - **Summary** -- "Three concise paragraphs covering everything discussed."
   - **Action Items** -- "Tasks extracted automatically with assignees and priorities. No one took notes."

> "This took about 30 seconds. For a one-hour meeting."

---

### Scene 4: Bot Joins a Live Meeting (2 minutes)

*Skip this if Docker is not running. Show a pre-completed meeting instead.*

1. Create a new meeting with a Google Meet URL
2. Open the meeting and click the red **Record** button
3. Switch to Google Meet -- show "Vaktram Notetaker" appearing as a participant
4. Talk for 1-2 minutes with someone
5. Click **Stop Recording** in Vaktram
6. Wait -- show the notification bell light up: "Your summary is ready!"
7. Open the meeting -- full transcript + summary

> "The bot sat in your meeting quietly. Camera off, mic off. Just listening and recording. And now you have perfect notes."

---

### Scene 5: Calendar Integration (1 minute)

1. Go to **Settings** -> **Calendar** tab
2. Click **Connect Google Calendar** -> complete OAuth flow
3. Show meetings syncing from calendar
4. Enable auto-record on a meeting

> "From now on, every meeting with auto-record turned on -- the bot joins automatically 30 seconds before it starts. You never have to think about it again."

---

### Scene 6: Search Across Meetings (30 seconds)

1. Go to **Search** in the sidebar
2. Type "budget" or "deadline"
3. Show results: exact transcript moment, speaker, timestamp, highlighted match

> "Three months from now, when you have 200 meetings recorded, you can find anything. 'What did we decide about pricing in that meeting with the client?' -- found in 2 seconds."

---

### Scene 7: BYOM and Team (30 seconds)

1. **Settings** -> **AI Config** -> Show model configuration
2. "You can use your own OpenAI or Claude API key. Your data, your model."
3. **Team** page -> Show invite flow
4. "Invite your team. Everyone gets access to the shared meeting library."

---

### Closing (30 seconds)

> "Vaktram captures every meeting, identifies every speaker, extracts every action item, and makes every conversation searchable -- automatically."
>
> "No more lost context. No more 'can you send me the notes?' No more forgotten action items."

---

## Architecture Overview (For Technical Audiences)

```
Frontend (Next.js 14)
    |
    v
API (FastAPI + SQLAlchemy)
    |
    +-- Auth: Custom JWT (bcrypt + PyJWT)
    +-- Database: Supabase PostgreSQL (DB only)
    +-- Cache: Upstash Redis
    +-- Queue: Upstash QStash
    +-- Scheduler: APScheduler (SQLAlchemy job store)
    |
    +-- Transcription: Groq Whisper API (whisper-large-v3-turbo)
    +-- Diarization: pyannote.audio 3.1 (Docker service)
    +-- Summarization: LiteLLM -> Gemini 2.0 Flash
    |
    +-- Bot Service (Docker):
        +-- Playwright + Chromium (joins meetings)
        +-- PulseAudio (captures audio)
        +-- FFmpeg (audio conversion)
```

**Pipeline flow:**
```
Calendar Sync -> Scheduler (every 60s) -> Bot joins meeting
    -> Records audio -> API callback -> QStash
    -> Transcribe (Groq) + Diarize (pyannote)
    -> QStash -> Summarize (Gemini)
    -> WebSocket notification -> Dashboard updated
```

---

## API Quick Reference

| Category | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| Auth | POST | `/api/v1/auth/signup` | Create account |
| Auth | POST | `/api/v1/auth/login` | Login |
| Auth | POST | `/api/v1/auth/refresh` | Refresh tokens |
| Auth | GET | `/api/v1/auth/me` | Current user |
| Meetings | GET | `/api/v1/meetings` | List meetings |
| Meetings | POST | `/api/v1/meetings` | Create meeting |
| Meetings | GET | `/api/v1/meetings/{id}` | Get meeting |
| Meetings | PATCH | `/api/v1/meetings/{id}` | Update meeting |
| Meetings | DELETE | `/api/v1/meetings/{id}` | Delete meeting |
| Meetings | POST | `/api/v1/meetings/upload-audio` | Upload audio file |
| Transcripts | GET | `/api/v1/transcripts/{meeting_id}` | Get transcript |
| Summaries | GET | `/api/v1/summaries/{meeting_id}` | Get summary |
| Bot | POST | `/api/v1/bot/join` | Send bot to meeting |
| Bot | POST | `/api/v1/bot/leave/{id}` | Remove bot |
| Bot | GET | `/api/v1/bot/status/{id}` | Bot status |
| Bot | POST | `/api/v1/bot/schedule` | Schedule bot |
| Bot | GET | `/api/v1/bot/scheduled-jobs` | List scheduled jobs |
| Search | POST | `/api/v1/search` | Search transcripts |
| AI Config | GET | `/api/v1/ai-config` | List AI configs |
| AI Config | POST | `/api/v1/ai-config` | Add AI config |
| AI Config | POST | `/api/v1/ai-config/test` | Test AI config |
| Calendar | POST | `/api/v1/calendar/authorize` | Start OAuth |
| Calendar | GET | `/api/v1/calendar/connections` | List connections |
| Calendar | POST | `/api/v1/calendar/sync` | Sync calendar |
| Calendar | DELETE | `/api/v1/calendar/{id}` | Disconnect |
| Analytics | GET | `/api/v1/analytics/overview` | Stats overview |
| Analytics | GET | `/api/v1/analytics/talk-time` | Speaker stats |
| Analytics | GET | `/api/v1/analytics/frequency` | Meeting frequency |
| Analytics | GET | `/api/v1/analytics/topics` | Topic trends |
| Analytics | GET | `/api/v1/analytics/usage` | Usage data |
| Teams | GET | `/api/v1/teams/members` | List members |
| Teams | POST | `/api/v1/teams/invite` | Invite member |
| Teams | GET | `/api/v1/teams/profile` | Get profile |
| Teams | PATCH | `/api/v1/teams/profile` | Update profile |
| Notifications | GET | `/api/v1/notifications` | List notifications |
| Notifications | PATCH | `/api/v1/notifications/{id}/read` | Mark read |
| Notifications | POST | `/api/v1/notifications/read-all` | Mark all read |
| Webhooks | POST | `/api/v1/webhooks/google-calendar` | Calendar webhook |
| Webhooks | POST | `/api/v1/webhooks/bot-events` | Bot event webhook |
| Health | GET | `/health` | API health check |

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://...

# Auth
JWT_SECRET=your-jwt-secret

# Transcription
GROQ_API_KEY=gsk_...

# Summarization
GOOGLE_AI_API_KEY=your-gemini-key

# Queue (optional -- inline fallback for local dev)
QSTASH_TOKEN=...
QSTASH_CURRENT_SIGNING_KEY=...
QSTASH_NEXT_SIGNING_KEY=...

# Redis (optional -- for rate limiting)
UPSTASH_REDIS_URL=...
UPSTASH_REDIS_TOKEN=...

# Bot Service
BOT_SERVICE_URL=http://localhost:8001

# Diarization Service
DIARIZATION_SERVICE_URL=http://localhost:8002

# Calendar OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# URLs
API_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:3000
```
