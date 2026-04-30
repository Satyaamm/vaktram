"""Channels — shared meeting workspaces (organize meetings into rooms)."""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.intel import Channel, ChannelMeeting, ChannelMember
from app.models.team import UserProfile

router = APIRouter(prefix="/channels", tags=["channels"])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")[:120] or "channel"


class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None
    is_private: bool = False


@router.get("")
async def list_channels(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        return []
    rows = (await db.execute(
        select(Channel)
        .where(Channel.organization_id == user.organization_id)
        .order_by(Channel.created_at.desc())
    )).scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "slug": c.slug,
            "is_private": c.is_private,
            "description": c.description,
        }
        for c in rows
    ]


@router.post("")
async def create_channel(
    body: ChannelCreate,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.organization_id:
        raise HTTPException(403, "No organization")
    channel = Channel(
        organization_id=user.organization_id,
        name=body.name,
        slug=_slugify(body.name),
        description=body.description,
        is_private=body.is_private,
    )
    db.add(channel)
    await db.flush()
    db.add(ChannelMember(channel_id=channel.id, user_id=user.id, role="owner"))
    await db.flush()
    return {"id": str(channel.id), "slug": channel.slug}


@router.post("/{channel_id}/meetings/{meeting_id}", status_code=204)
async def add_meeting(
    channel_id: uuid.UUID,
    meeting_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await db.get(Channel, channel_id)
    if not channel or channel.organization_id != user.organization_id:
        raise HTTPException(404, "Channel not found")
    db.add(ChannelMeeting(channel_id=channel_id, meeting_id=meeting_id))
    try:
        await db.flush()
    except Exception:
        # already in channel — idempotent
        await db.rollback()
    return


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: uuid.UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await db.get(Channel, channel_id)
    if not channel or channel.organization_id != user.organization_id:
        raise HTTPException(404, "Channel not found")
    await db.delete(channel)
    await db.flush()
    return
