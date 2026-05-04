"""Pydantic schemas for teams, users, notifications."""

from __future__ import annotations

import uuid
from datetime import datetime

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


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


# ---- Auth (custom JWT) ----

_NAME_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'.\- ]+$")
_PHONE_RE = re.compile(r"^\+?[0-9 ()\-]{7,20}$")


class SignupRequest(BaseModel):
    """Validated signup payload.

    Rules:
    * full_name 2–100 chars, letters/spaces/apostrophes/hyphens only
    * organization_name 2–120 chars
    * email RFC-valid, lowercased
    * phone optional, 7–20 digits with optional +, spaces, parens, dashes
    * password 8–128 chars, ≥1 letter and ≥1 digit
    * password_confirm must equal password
    """

    full_name: str = Field(..., min_length=2, max_length=100)
    organization_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @field_validator("full_name", "organization_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("full_name")
    @classmethod
    def _name_charset(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError(
                "Name may only contain letters, spaces, apostrophes, hyphens, and periods."
            )
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not _PHONE_RE.match(v):
            raise ValueError("Phone must be 7–20 digits with optional +, spaces, parens, or dashes.")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        return v

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match.")
        return self


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfileRead"


class SignupResponse(BaseModel):
    """Returned after signup. We do NOT issue tokens until email is verified."""
    user_id: uuid.UUID
    email: str
    organization_id: uuid.UUID
    verification_email_sent: bool
    message: str = "Check your email to verify your account."


class RefreshRequest(BaseModel):
    # Optional: modern clients use the HttpOnly refresh cookie instead. Body
    # is kept for legacy clients (Swagger, the OAuth2 password flow).
    refresh_token: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = None
    role: str | None = None
    onboarding_completed: bool | None = None
    timezone: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=10)


class UserProfileRead(UserProfileBase):
    id: uuid.UUID
    organization_id: uuid.UUID | None = None
    organization_name: str | None = None
    is_active: bool
    onboarding_completed: bool
    timezone: str | None = None
    language: str | None = None
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
