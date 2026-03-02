"""Dependency injection functions for FastAPI."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user_from_token
from app.models.team import UserProfile
from app.utils.database import get_async_session


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Return the authenticated UserProfile.

    Decodes the JWT, extracts the ``sub`` claim (Supabase user id),
    and fetches the corresponding UserProfile row.
    """
    payload = await get_current_user_from_token(request)
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id in token",
        )

    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    if user is None:
        # Auto-create user profile on first API call
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found and no email in token",
            )
        user_meta = payload.get("user_metadata", {})
        user = UserProfile(
            id=user_uuid,
            email=email,
            full_name=user_meta.get("full_name") or user_meta.get("name"),
            role="member",
            is_active=True,
            onboarding_completed=False,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user
