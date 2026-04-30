"""Import all models so Alembic can discover them."""

from app.models.base import Base
from app.models.meeting import Meeting, MeetingParticipant, MeetingStatus, MeetingPlatform
from app.models.transcript import TranscriptSegment
from app.models.summary import MeetingSummary
from app.models.ai_config import UserAIConfig
from app.models.team import (
    Organization,
    UserProfile,
    CalendarConnection,
    MeetingEmbedding,
    ApiKey,
    AuditLog,
    Notification,
)
from app.models.scheduler import ScheduledJob
from app.models.verification import EmailVerificationToken
from app.models.billing import (
    Invoice,
    PlanTier,
    Subscription,
    SubscriptionStatus,
    UsageEvent,
    UsageKind,
    UsagePeriodSummary,
)
from app.models.jobs import DeadLetterJob, JobStatus
from app.models.identity import (
    Role,
    RoleAssignment,
    RoleScope,
    ScimToken,
    SsoConnection,
    SsoType,
)
from app.models.compliance import (
    DataExportKind,
    DataExportRequest,
    DataExportStatus,
    KmsKey,
    RetentionPolicy,
)
from app.models.intel import (
    AskMessage,
    AskScope,
    AskThread,
    Channel,
    ChannelMeeting,
    ChannelMember,
    Soundbite,
    TopicHit,
    TopicTracker,
)
from app.models.webhooks import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
)
from app.models.integrations import OrgIntegration

__all__ = [
    "Base",
    "Meeting",
    "MeetingParticipant",
    "MeetingStatus",
    "MeetingPlatform",
    "TranscriptSegment",
    "MeetingSummary",
    "UserAIConfig",
    "Organization",
    "UserProfile",
    "CalendarConnection",
    "MeetingEmbedding",
    "ApiKey",
    "AuditLog",
    "Notification",
    "ScheduledJob",
    "Subscription",
    "SubscriptionStatus",
    "PlanTier",
    "UsageEvent",
    "UsageKind",
    "UsagePeriodSummary",
    "Invoice",
]
