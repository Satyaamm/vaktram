"""Team management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.team import Organization, UserProfile
from app.schemas.team import (
    OrganizationCreate,
    OrganizationRead,
    UserProfileRead,
    UserProfileUpdate,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/organization", response_model=OrganizationRead)
async def get_organization(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Get the user's organization."""
    if user.organization_id is None:
        raise HTTPException(status_code=404, detail="User has no organization")
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/organization", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Create a new organization and assign the user as admin."""
    org = Organization(
        name=payload.name,
        slug=payload.slug,
        logo_url=payload.logo_url,
        max_seats=payload.max_seats,
    )
    db.add(org)
    await db.flush()

    user.organization_id = org.id
    user.role = "admin"
    await db.flush()
    await db.refresh(org)
    return org


@router.get("/members", response_model=list[UserProfileRead])
async def list_members(
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """List all members of the user's organization."""
    if user.organization_id is None:
        raise HTTPException(status_code=404, detail="User has no organization")
    result = await db.execute(
        select(UserProfile).where(UserProfile.organization_id == user.organization_id)
    )
    return result.scalars().all()


@router.get("/profile", response_model=UserProfileRead)
async def get_profile(
    user: UserProfile = Depends(get_current_user),
):
    """Get the authenticated user's profile."""
    return user


@router.patch("/profile", response_model=UserProfileRead)
async def update_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Update the authenticated user's profile."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user
