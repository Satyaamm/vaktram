"""Fan-out a domain event to in-app + email + (optionally) Slack.

Other code calls `dispatch()` instead of writing to one channel directly. This
makes it trivial to add Slack / Teams later without touching every callsite.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Notification, UserProfile
from app.services import email_service, realtime

logger = logging.getLogger(__name__)


async def dispatch(
    db: AsyncSession,
    *,
    user: UserProfile,
    title: str,
    body: str,
    notification_type: str,
    link: str | None = None,
    email: bool = True,
) -> None:
    """Persist an in-app notification, push it over WS, and optionally email."""
    notif = Notification(
        user_id=user.id,
        title=title,
        body=body,
        notification_type=notification_type,
        link=link,
    )
    db.add(notif)
    await db.flush()

    await realtime.publish(
        realtime.channel_for_user(str(user.id)),
        {
            "type": "notification",
            "id": str(notif.id),
            "title": title,
            "body": body,
            "link": link,
            "notification_type": notification_type,
        },
    )

    if email and user.email:
        html = (
            f"<h2>{title}</h2>"
            f"<p>{body}</p>"
            + (f'<p><a href="{link}">Open in Vaktram</a></p>' if link else "")
        )
        await email_service.send_email(to=user.email, subject=title, html=html)
