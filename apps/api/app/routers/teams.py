"""Team management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
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


class InviteMemberRequest(BaseModel):
    email: str = Field(..., max_length=255)
    role: str = Field(default="member", max_length=50)


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., max_length=50)

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


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    payload: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Invite a member to the organization by email."""
    if user.organization_id is None:
        raise HTTPException(status_code=400, detail="You must belong to an organization first")
    if user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admins can invite members")

    # Check if user already exists
    result = await db.execute(
        select(UserProfile).where(UserProfile.email == payload.email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.organization_id == user.organization_id:
            raise HTTPException(status_code=409, detail="User is already a member")
        existing.organization_id = user.organization_id
        existing.role = payload.role
        await db.flush()
        return {"status": "ok", "message": f"Added {payload.email} to the organization"}

    # Create a placeholder profile for invited user
    new_user = UserProfile(
        id=uuid.uuid4(),
        email=payload.email,
        organization_id=user.organization_id,
        role=payload.role,
        is_active=True,
        onboarding_completed=False,
    )
    db.add(new_user)
    await db.flush()
    return {"status": "ok", "message": f"Invited {payload.email}"}


@router.patch("/members/{member_id}", response_model=UserProfileRead)
async def update_member_role(
    member_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Update a team member's role."""
    if user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admins can update roles")

    result = await db.execute(
        select(UserProfile).where(
            UserProfile.id == member_id,
            UserProfile.organization_id == user.organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = payload.role
    await db.flush()
    await db.refresh(member)
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(get_current_user),
):
    """Remove a member from the organization."""
    if user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    if member_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    result = await db.execute(
        select(UserProfile).where(
            UserProfile.id == member_id,
            UserProfile.organization_id == user.organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.organization_id = None
    member.role = "member"
    await db.flush()
