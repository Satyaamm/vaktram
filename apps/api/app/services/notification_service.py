"""Notification service."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str | None = None,
        notification_type: str = "info",
        link: str | None = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            link=link,
        )
        self.db.add(notif)
        await self.db.flush()
        await self.db.refresh(notif)
        return notif

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, notification_ids: list[uuid.UUID], user_id: uuid.UUID) -> int:
        """Mark notifications as read. Returns count updated."""
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        return result.rowcount

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        return result.rowcount
