"""Auth-adjacent endpoints: SSO profile provisioning."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.middleware.auth import get_current_user_from_token
from app.models.team import UserProfile
from app.schemas.team import UserProfileRead, UserProfileSSOCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/profile",
    response_model=UserProfileRead,
    status_code=status.HTTP_200_OK,
)
async def ensure_profile(
    body: UserProfileSSOCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ensure a user profile exists after SSO login.

    Called by the frontend callback after OAuth succeeds.
    Returns the existing profile or creates a new one.
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

    # Check if profile already exists
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        # Update avatar/name from provider if missing locally
        changed = False
        if not user.full_name and body.full_name:
            user.full_name = body.full_name
            changed = True
        if not user.avatar_url and body.avatar_url:
            user.avatar_url = body.avatar_url
            changed = True
        if changed:
            await db.flush()
            await db.refresh(user)
        return user

    # Create new profile from SSO data
    user = UserProfile(
        id=user_uuid,
        email=body.email,
        full_name=body.full_name,
        avatar_url=body.avatar_url,
        role="member",
        is_active=True,
        onboarding_completed=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
