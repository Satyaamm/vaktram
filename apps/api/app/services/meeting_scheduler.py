"""Meeting Scheduler — uses APScheduler to schedule bot deployments.

Jobs are persisted in the `vaktram.apscheduler_jobs` table so they survive restarts.
Two recurring jobs run:
1. `scan_upcoming_meetings` — every 60s, finds meetings starting soon and schedules bot deploys
2. `sync_all_calendars` — every 5 min, syncs calendar events for all users
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete, select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.meeting import Meeting, MeetingStatus
from app.models.scheduler import ScheduledJob
from app.utils.database import get_async_session

logger = logging.getLogger(__name__)
settings = get_settings()

# APScheduler instance (module-level singleton)
scheduler: AsyncIOScheduler | None = None

LOOKAHEAD_MINUTES = 2


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the APScheduler instance."""
    global scheduler
    if scheduler is None:
        from sqlalchemy import create_engine

        db_url = sync_database_url()
        # Create engine with pool_pre_ping so stale connections are
        # automatically recycled (Supabase drops idle connections).
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        jobstores = {
            "default": SQLAlchemyJobStore(
                engine=engine,
                tablename="apscheduler_jobs",
                tableschema="vaktram",
            ),
        }
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 120},
        )
    return scheduler


def sync_database_url() -> str:
    """Convert async DB URL to sync for APScheduler's SQLAlchemy job store."""
    url = settings.database_url
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def start_scheduler() -> None:
    """Start APScheduler and register recurring jobs."""
    sched = get_scheduler()

    # Recurring: scan for upcoming meetings every 60 seconds
    sched.add_job(
        scan_upcoming_meetings,
        trigger=IntervalTrigger(seconds=60),
        id="scan_upcoming_meetings",
        name="Scan for upcoming meetings and deploy bots",
        replace_existing=True,
    )

    # Recurring: sync calendars every 5 minutes
    sched.add_job(
        sync_all_calendars,
        trigger=IntervalTrigger(minutes=5),
        id="sync_all_calendars",
        name="Sync calendar events for all users",
        replace_existing=True,
    )

    # Recurring: clean up old completed/failed jobs every 24 hours
    sched.add_job(
        cleanup_old_jobs,
        trigger=IntervalTrigger(hours=24),
        id="cleanup_old_jobs",
        name="Delete completed/failed scheduled jobs older than 30 days",
        replace_existing=True,
    )

    # Recurring: process webhook delivery retries every minute
    sched.add_job(
        retry_pending_webhooks,
        trigger=IntervalTrigger(minutes=1),
        id="retry_pending_webhooks",
        name="Reattempt failed webhook deliveries",
        replace_existing=True,
    )

    # Recurring: weekly bot-platform health probe so a Meet/Zoom UI change
    # doesn't silently break joins for hours.
    sched.add_job(
        run_selector_health_check,
        trigger=IntervalTrigger(days=7),
        id="selector_health_check",
        name="Probe bot service for selector health",
        replace_existing=True,
    )

    sched.start()
    logger.info("APScheduler started with %d jobs", len(sched.get_jobs()))


async def retry_pending_webhooks() -> None:
    """Drain failed webhook deliveries whose next_retry_at has passed."""
    from app.services import webhook_service

    async for db in get_async_session():
        try:
            n = await webhook_service.process_retries(db)
            if n:
                logger.info("Retried %d pending webhooks", n)
        except Exception:
            logger.exception("retry_pending_webhooks failed")
        break


async def run_selector_health_check() -> None:
    """Weekly probe — pings the bot service and logs a warning if it's
    unhealthy. Real selector validation needs a permanent test meeting URL
    (set BOT_SELECTOR_TEST_URL); we keep that opt-in to avoid false alarms.
    """
    import os

    bot_url = settings.bot_service_url
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{bot_url}/health")
            if resp.status_code >= 300:
                logger.warning("Bot health probe failed: %s", resp.status_code)
                return
            logger.info("Bot health probe OK: %s", resp.json())
    except Exception:
        logger.exception("Bot health probe raised")
        return

    test_url = os.getenv("BOT_SELECTOR_TEST_URL")
    if not test_url:
        return  # opt-in
    # Future: request a no-op join attempt against test_url and inspect the
    # bot's reported state to confirm selectors still work.


async def stop_scheduler() -> None:
    """Gracefully shut down APScheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
    scheduler = None


# ── Recurring Jobs ──────────────────────────────────────────────────────

async def scan_upcoming_meetings() -> None:
    """Find meetings starting in the next 2 minutes and schedule bot deployments."""
    async for session in get_async_session():
        now = datetime.now(timezone.utc)
        lookahead = now + timedelta(minutes=LOOKAHEAD_MINUTES)

        result = await session.execute(
            select(Meeting).where(
                and_(
                    Meeting.status == MeetingStatus.scheduled,
                    Meeting.scheduled_start.isnot(None),
                    Meeting.scheduled_start <= lookahead,
                    Meeting.scheduled_start >= now - timedelta(minutes=5),
                    Meeting.meeting_url.isnot(None),
                    Meeting.meeting_url != "",
                    Meeting.auto_record.is_(True),
                )
            )
        )
        meetings = result.scalars().all()

        for meeting in meetings:
            # Check if we already scheduled a job for this meeting
            existing = await session.execute(
                select(ScheduledJob).where(
                    and_(
                        ScheduledJob.meeting_id == meeting.id,
                        ScheduledJob.job_type == "bot_deploy",
                        ScheduledJob.status.in_(["pending", "running", "completed"]),
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Create a scheduled job record
            job = ScheduledJob(
                job_type="bot_deploy",
                meeting_id=meeting.id,
                user_id=meeting.user_id,
                scheduled_at=meeting.scheduled_start or now,
                status="pending",
                payload={
                    "meeting_url": meeting.meeting_url,
                    "platform": meeting.platform.value if meeting.platform else "google_meet",
                    "organization_id": str(meeting.organization_id) if meeting.organization_id else None,
                },
            )
            session.add(job)

            # Schedule the bot deployment via APScheduler
            deploy_time = (meeting.scheduled_start or now) - timedelta(seconds=30)
            if deploy_time < now:
                deploy_time = now

            sched = get_scheduler()
            sched.add_job(
                deploy_bot_for_meeting,
                trigger=DateTrigger(run_date=deploy_time),
                id=f"bot_deploy_{meeting.id}",
                name=f"Deploy bot for {meeting.title}",
                replace_existing=True,
                kwargs={
                    "meeting_id": str(meeting.id),
                    "job_id": str(job.id),
                },
            )

            logger.info(
                "Scheduled bot deploy for meeting %s (%s) at %s",
                meeting.id, meeting.title, deploy_time,
            )

        if meetings:
            await session.commit()


async def sync_all_calendars() -> None:
    """Sync calendar events for all users with active calendar connections."""
    from app.models.team import CalendarConnection
    from app.services.calendar_service import CalendarService

    async for session in get_async_session():
        result = await session.execute(
            select(CalendarConnection).where(CalendarConnection.is_active.is_(True))
        )
        connections = result.scalars().all()

        for conn in connections:
            try:
                svc = CalendarService(session)
                await svc.sync_events(conn.user_id)
                await session.commit()
            except Exception:
                logger.exception("Calendar sync failed for user %s", conn.user_id)
                await session.rollback()

        if connections:
            logger.info("Calendar sync completed for %d users", len(connections))


async def cleanup_old_jobs() -> None:
    """Delete completed/failed scheduled jobs older than 30 days."""
    async for session in get_async_session():
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        result = await session.execute(
            delete(ScheduledJob).where(
                and_(
                    ScheduledJob.status.in_(["completed", "failed", "cancelled"]),
                    ScheduledJob.created_at < cutoff,
                )
            )
        )
        deleted = result.rowcount
        await session.commit()
        if deleted:
            logger.info("Cleaned up %d old scheduled jobs", deleted)


# ── One-time Jobs ───────────────────────────────────────────────────────

async def deploy_bot_for_meeting(meeting_id: str, job_id: str) -> None:
    """Deploy a bot to join a meeting. Called by APScheduler at the scheduled time."""
    async for session in get_async_session():
        # Update job status
        await session.execute(
            update(ScheduledJob)
            .where(ScheduledJob.id == uuid.UUID(job_id))
            .values(status="running", executed_at=datetime.now(timezone.utc))
        )
        await session.commit()

        # Get meeting
        result = await session.execute(
            select(Meeting).where(Meeting.id == uuid.UUID(meeting_id))
        )
        meeting = result.scalar_one_or_none()

        if not meeting:
            logger.warning("Meeting %s not found for bot deploy", meeting_id)
            await _update_job_status(session, job_id, "failed", error="Meeting not found")
            return

        if meeting.status != MeetingStatus.scheduled:
            logger.info("Meeting %s is no longer scheduled (status: %s), skipping", meeting_id, meeting.status)
            await _update_job_status(session, job_id, "cancelled", result="Meeting not in scheduled state")
            return

        # Call bot service
        bot_url = settings.bot_service_url
        if not bot_url:
            await _update_job_status(session, job_id, "failed", error="BOT_SERVICE_URL not configured")
            return

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{bot_url}/bots/start",
                    json={
                        "meeting_id": str(meeting.id),
                        "meeting_url": meeting.meeting_url,
                        "platform": meeting.platform.value if meeting.platform else "google_meet",
                        "bot_name": "Vaktram Notetaker",
                        "user_id": str(meeting.user_id),
                        "organization_id": str(meeting.organization_id) if meeting.organization_id else None,
                    },
                )

                if resp.status_code in (200, 201):
                    meeting.status = MeetingStatus.in_progress
                    meeting.bot_id = "active"
                    await session.commit()
                    await _update_job_status(session, job_id, "completed", result="Bot deployed")
                    logger.info("Bot deployed for meeting %s", meeting_id)
                elif resp.status_code == 409:
                    await _update_job_status(session, job_id, "completed", result="Bot already active")
                else:
                    error_msg = f"Bot service returned {resp.status_code}: {resp.text}"
                    await _update_job_status(session, job_id, "failed", error=error_msg)
                    logger.error("Bot deploy failed: %s", error_msg)

        except httpx.ConnectError:
            await _update_job_status(session, job_id, "failed", error="Bot service not reachable")
            logger.warning("Bot service not reachable at %s", bot_url)
        except Exception as exc:
            await _update_job_status(session, job_id, "failed", error=str(exc))
            logger.exception("Bot deploy error for meeting %s", meeting_id)


async def _update_job_status(
    session: AsyncSession, job_id: str, status: str,
    result: str | None = None, error: str | None = None,
) -> None:
    """Update a ScheduledJob's status."""
    values: dict = {"status": status}
    if result:
        values["result"] = result
    if error:
        values["error"] = error
    if status in ("completed", "failed"):
        values["executed_at"] = datetime.now(timezone.utc)

    await session.execute(
        update(ScheduledJob)
        .where(ScheduledJob.id == uuid.UUID(job_id))
        .values(**values)
    )
    await session.commit()


# ── Manual scheduling helpers ───────────────────────────────────────────

async def schedule_bot_deploy(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    deploy_at: datetime,
    meeting_url: str,
    platform: str = "google_meet",
    organization_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> ScheduledJob:
    """Manually schedule a bot deployment for a specific meeting.

    Can be called from API endpoints when user clicks "Record this meeting".
    """
    job = ScheduledJob(
        job_type="bot_deploy",
        meeting_id=meeting_id,
        user_id=user_id,
        scheduled_at=deploy_at,
        status="pending",
        payload={
            "meeting_url": meeting_url,
            "platform": platform,
            "organization_id": str(organization_id) if organization_id else None,
        },
    )

    if db:
        db.add(job)
        await db.flush()
        await db.refresh(job)

    sched = get_scheduler()
    sched.add_job(
        deploy_bot_for_meeting,
        trigger=DateTrigger(run_date=deploy_at),
        id=f"bot_deploy_{meeting_id}",
        name=f"Deploy bot for meeting {meeting_id}",
        replace_existing=True,
        kwargs={
            "meeting_id": str(meeting_id),
            "job_id": str(job.id),
        },
    )

    logger.info("Manually scheduled bot deploy for meeting %s at %s", meeting_id, deploy_at)
    return job
