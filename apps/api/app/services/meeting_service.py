"""Meeting CRUD service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meeting import Meeting, MeetingParticipant, MeetingStatus
from app.schemas.meeting import MeetingCreate, MeetingList, MeetingUpdate


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_meetings(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> MeetingList:
        query = (
            select(Meeting)
            .where(Meeting.user_id == user_id)
            .options(selectinload(Meeting.participants))
            .order_by(Meeting.created_at.desc())
        )
        if status_filter:
            query = query.where(Meeting.status == MeetingStatus(status_filter))

        # Total count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        meetings = result.scalars().unique().all()

        return MeetingList(
            items=meetings,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_meeting(self, user_id: uuid.UUID, data: MeetingCreate) -> Meeting:
        meeting = Meeting(
            user_id=user_id,
            title=data.title,
            meeting_url=data.meeting_url,
            platform=data.platform,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            auto_record=data.auto_record,
        )
        self.db.add(meeting)
        await self.db.flush()

        for p in data.participants:
            participant = MeetingParticipant(
                meeting_id=meeting.id,
                name=p.name,
                email=p.email,
                role=p.role,
            )
            self.db.add(participant)

        await self.db.flush()
        await self.db.refresh(meeting, attribute_names=["participants"])
        return meeting

    async def get_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> Meeting | None:
        result = await self.db.execute(
            select(Meeting)
            .where(Meeting.id == meeting_id, Meeting.user_id == user_id)
            .options(selectinload(Meeting.participants))
        )
        return result.scalar_one_or_none()

    async def update_meeting(
        self, meeting_id: uuid.UUID, user_id: uuid.UUID, data: MeetingUpdate
    ) -> Meeting | None:
        meeting = await self.get_meeting(meeting_id, user_id)
        if meeting is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(meeting, field, value)
        await self.db.flush()
        await self.db.refresh(meeting)
        return meeting

    async def delete_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
        )
        return result.rowcount > 0
