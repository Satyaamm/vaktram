"""Pydantic schemas for teams, users, notifications."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- Organization ----

class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    logo_url: str | None = None
    max_seats: int = 5


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationRead(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- UserProfile ----

class UserProfileBase(BaseModel):
    email: str = Field(..., max_length=255)
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = None
    role: str = "member"


class UserProfileCreate(UserProfileBase):
    organization_id: uuid.UUID | None = None


class UserProfileSSOCreate(BaseModel):
    """Created from SSO provider data (Google, Microsoft, etc.)."""

    provider: str = Field(..., description="SSO provider: google, azure, github")
    provider_user_id: str | None = Field(None, description="Provider-specific user ID")
    email: str = Field(..., max_length=255)
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = None
    role: str | None = None
    onboarding_completed: bool | None = None


class UserProfileRead(UserProfileBase):
    id: uuid.UUID
    organization_id: uuid.UUID | None = None
    is_active: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- Notification ----

class NotificationRead(BaseModel):
    id: uuid.UUID
    title: str
    body: str | None = None
    notification_type: str
    is_read: bool
    link: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkRead(BaseModel):
    notification_ids: list[uuid.UUID]


# ---- AuditLog ----

class AuditLogRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
