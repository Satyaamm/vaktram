# Vaktram API Documentation

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.vaktram.com/api/v1
```

## Authentication

All API requests require a Bearer token from Supabase Auth:

```
Authorization: Bearer <supabase-jwt-token>
```

## Endpoints

### Meetings

#### List Meetings
```
GET /meetings
```
Query parameters:
- `status` (optional): Filter by status (scheduled, in_progress, completed)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset

Response:
```json
{
  "meetings": [
    {
      "id": "uuid",
      "title": "Weekly Standup",
      "platform": "google_meet",
      "status": "completed",
      "scheduled_at": "2024-01-15T10:00:00Z",
      "duration_seconds": 1800,
      "participant_count": 4
    }
  ],
  "total": 42
}
```

#### Create Meeting
```
POST /meetings
```
Body:
```json
{
  "title": "Sprint Planning",
  "meeting_url": "https://meet.google.com/abc-defg-hij",
  "scheduled_at": "2024-01-20T14:00:00Z",
  "bot_name": "Vaktram Notetaker"
}
```

#### Get Meeting Details
```
GET /meetings/:id
```

#### Join Meeting (Deploy Bot)
```
POST /meetings/:id/join
```
Dispatches a bot to join the meeting immediately.

#### Leave Meeting (Stop Bot)
```
POST /meetings/:id/leave
```

### Transcripts

#### Get Transcript
```
GET /meetings/:id/transcript
```
Response:
```json
{
  "meeting_id": "uuid",
  "segments": [
    {
      "speaker_label": "SPEAKER_00",
      "start_time": 0.0,
      "end_time": 5.2,
      "text": "Good morning everyone.",
      "confidence": 0.95
    }
  ],
  "language": "en"
}
```

### Summaries

#### Get Summary
```
GET /meetings/:id/summary
```
Response:
```json
{
  "meeting_id": "uuid",
  "summary": "The team discussed...",
  "action_items": [...],
  "decisions": [...],
  "follow_ups": [...]
}
```

### Search

#### Semantic Search
```
POST /search
```
Body:
```json
{
  "query": "What did we decide about the database migration?",
  "limit": 10
}
```
Response:
```json
{
  "results": [
    {
      "meeting_id": "uuid",
      "meeting_title": "Sprint Planning",
      "chunk_text": "We decided to use...",
      "similarity": 0.89
    }
  ]
}
```

### BYOM (Bring Your Own Model)

#### List Configurations
```
GET /byom/configs
```

#### Add Configuration
```
POST /byom/configs
```
Body:
```json
{
  "provider": "anthropic",
  "model_name": "claude-3-sonnet",
  "api_key": "sk-ant-..."
}
```

### Webhooks

#### List Webhooks
```
GET /webhooks
```

#### Create Webhook
```
POST /webhooks
```
Body:
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["meeting.completed", "transcription.completed"]
}
```

## Webhook Events

| Event | Description |
|-------|-------------|
| `meeting.joined` | Bot joined the meeting |
| `meeting.completed` | Meeting ended and bot left |
| `transcription.completed` | Transcript is ready |
| `summary.completed` | Summary generation finished |

## Rate Limits

| Plan | Requests/minute |
|------|----------------|
| Free | 60 |
| Pro | 300 |
| Enterprise | 1000 |

## Error Responses

```json
{
  "error": {
    "code": "MEETING_NOT_FOUND",
    "message": "No meeting found with the given ID",
    "status": 404
  }
}
```
