"""
Shared type definitions used across Vaktram services.
Uses Python dataclasses and TypedDict for cross-service compatibility.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Platform(str, Enum):
    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    TEAMS = "teams"


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    JOINING = "joining"
    IN_PROGRESS = "in_progress"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BotState(str, Enum):
    IDLE = "idle"
    JOINING = "joining"
    IN_MEETING = "in_meeting"
    RECORDING = "recording"
    LEAVING = "leaving"
    LEFT = "left"
    ERROR = "error"


# ---------------------------------------------------------------------------
# TypedDicts for API payloads
# ---------------------------------------------------------------------------

class StartBotPayload(TypedDict):
    meeting_id: str
    meeting_url: str
    platform: str
    bot_name: str
    callback_url: Optional[str]


class BotStatusPayload(TypedDict):
    meeting_id: str
    status: str
    platform: str
    uptime_seconds: float
    error: Optional[str]


class TranscriptSegmentPayload(TypedDict):
    speaker_label: str
    start_time: float
    end_time: float
    text: str
    confidence: float


class MeetingSummaryPayload(TypedDict):
    summary: str
    action_items: str
    decisions: str
    follow_ups: str


class ActionItem(TypedDict):
    task: str
    assignee: str
    deadline: str
    priority: str


class Decision(TypedDict):
    decision: str
    context: str
    made_by: str
    timestamp: str


class FollowUp(TypedDict):
    item: str
    owner: str
    due: str
    type: str


# ---------------------------------------------------------------------------
# Dataclasses for internal use
# ---------------------------------------------------------------------------

@dataclass
class Meeting:
    id: str
    organization_id: str
    title: str
    platform: Platform
    meeting_url: str
    status: MeetingStatus = MeetingStatus.SCHEDULED
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    participant_count: int = 0
    created_by: Optional[str] = None
    audio_storage_path: Optional[str] = None


@dataclass
class Organization:
    id: str
    name: str
    plan: PlanTier = PlanTier.FREE
    owner_id: Optional[str] = None
    member_count: int = 0
    meetings_this_month: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionJob:
    id: str
    meeting_id: str
    status: JobStatus = JobStatus.PENDING
    audio_storage_path: Optional[str] = None
    segment_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SummarizationJob:
    id: str
    meeting_id: str
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
