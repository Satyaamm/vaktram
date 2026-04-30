"""Dependency injection functions for FastAPI."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    """Return the authenticated UserProfile from the JWT."""
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
        select(UserProfile)
        .options(selectinload(UserProfile.organization))
        .where(UserProfile.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user
