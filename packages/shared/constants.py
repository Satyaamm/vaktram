"""
Shared constants used across all Vaktram services.
"""

# ---------------------------------------------------------------------------
# Plan Limits
# ---------------------------------------------------------------------------

PLAN_LIMITS = {
    "free": {
        "meetings_per_month": 5,
        "max_meeting_duration_minutes": 60,
        "storage_gb": 1,
        "max_participants": 10,
        "features": ["transcription", "basic_summary"],
    },
    "pro": {
        "meetings_per_month": 50,
        "max_meeting_duration_minutes": 180,
        "storage_gb": 25,
        "max_participants": 50,
        "features": [
            "transcription",
            "summary",
            "action_items",
            "decisions",
            "follow_ups",
            "semantic_search",
            "export",
        ],
    },
    "enterprise": {
        "meetings_per_month": -1,  # unlimited
        "max_meeting_duration_minutes": 480,
        "storage_gb": 500,
        "max_participants": -1,  # unlimited
        "features": [
            "transcription",
            "summary",
            "action_items",
            "decisions",
            "follow_ups",
            "semantic_search",
            "export",
            "byom",
            "custom_prompts",
            "api_access",
            "sso",
            "audit_log",
        ],
    },
}

# ---------------------------------------------------------------------------
# Supported Platforms
# ---------------------------------------------------------------------------

SUPPORTED_PLATFORMS = {
    "google_meet": {
        "name": "Google Meet",
        "status": "active",
        "url_pattern": r"https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}",
    },
    "zoom": {
        "name": "Zoom",
        "status": "coming_soon",
        "url_pattern": r"https://[\w.-]*zoom\.us/j/\d+",
    },
    "teams": {
        "name": "Microsoft Teams",
        "status": "coming_soon",
        "url_pattern": r"https://teams\.microsoft\.com/l/meetup-join/.*",
    },
}

# ---------------------------------------------------------------------------
# LLM Providers (for BYOM)
# ---------------------------------------------------------------------------

SUPPORTED_LLM_PROVIDERS = [
    "openai",
    "anthropic",
    "google",
    "azure",
    "groq",
    "together",
    "ollama",
]

# ---------------------------------------------------------------------------
# Audio Settings
# ---------------------------------------------------------------------------

AUDIO_SAMPLE_RATE = 16_000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "s16le"
AUDIO_CHUNK_DURATION_SECONDS = 30

# ---------------------------------------------------------------------------
# Job Statuses
# ---------------------------------------------------------------------------

JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

# ---------------------------------------------------------------------------
# Bot States
# ---------------------------------------------------------------------------

BOT_STATE_IDLE = "idle"
BOT_STATE_JOINING = "joining"
BOT_STATE_IN_MEETING = "in_meeting"
BOT_STATE_RECORDING = "recording"
BOT_STATE_LEAVING = "leaving"
BOT_STATE_LEFT = "left"
BOT_STATE_ERROR = "error"

# ---------------------------------------------------------------------------
# Storage Buckets
# ---------------------------------------------------------------------------

STORAGE_BUCKET_RECORDINGS = "meeting-recordings"
STORAGE_BUCKET_EXPORTS = "meeting-exports"

# ---------------------------------------------------------------------------
# Embedding Config
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ---------------------------------------------------------------------------
# API Versioning
# ---------------------------------------------------------------------------

API_VERSION = "v1"
