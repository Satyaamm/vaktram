"""Auth endpoints: signup, login, token refresh, current user."""

from __future__ import annotations

import logging
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.dependencies import get_db, get_current_user
from app.models.team import Organization, UserProfile
from app.schemas.team import (
    LoginRequest,
    RefreshRequest,
    ResendVerificationRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserProfileRead,
    VerifyEmailRequest,
)
from app.services import email_service, email_templates, verification_service
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

_settings = get_settings()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _user_read(user: UserProfile) -> UserProfileRead:
    """Build UserProfileRead with organization_name from the relationship."""
    data = UserProfileRead.model_validate(user)
    if user.organization:
        data.organization_name = user.organization.name
    return data


def _slugify(name: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")[:80]
    return slug or "org"


async def _send_verification(db: AsyncSession, user: UserProfile) -> bool:
    """Issue a fresh token (invalidating any prior) and email the verify link.
    Returns True if the email was dispatched (or logged in dev), False on failure.
    """
    await verification_service.invalidate_existing(
        db, user_id=user.id, purpose="verify_email"
    )
    token = await verification_service.issue(
        db, user_id=user.id, purpose="verify_email"
    )
    verify_url = f"{_settings.frontend_base_url.rstrip('/')}/verify-email?token={token}"
    try:
        subject, html, text = email_templates.email_verification(
            full_name=user.full_name, verify_url=verify_url
        )
        return await email_service.send_email(
            to=user.email, subject=subject, html=html, text=text
        )
    except Exception:
        logger.exception("verification email failed for user %s", user.id)
        return False


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Create a new account in `is_active=False, email_verified_at=NULL` state
    and email a verification link. The user CANNOT log in until they verify.

    Three paths:
      1. Brand-new email → create org + user, issue token, send email (201)
      2. Existing user with password but unverified → re-send verification (200)
      3. Existing user with password AND verified → 409 Conflict
      4. Existing placeholder (invite) → complete registration, send verification
    """
    email = body.email.lower().strip()
    existing = (await db.execute(
        select(UserProfile)
        .options(selectinload(UserProfile.organization))
        .where(UserProfile.email == email)
    )).scalar_one_or_none()

    if existing and existing.password_hash and existing.email_verified_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_exists", "message": "An account with this email already exists. Please log in or reset your password."},
        )

    if existing and existing.password_hash and not existing.email_verified_at:
        # Already signed up, didn't verify yet — just re-send the email.
        sent = await _send_verification(db, existing)
        logger.info("Resent verification for unverified user_id=%s", existing.id)
        return SignupResponse(
            user_id=existing.id,
            email=existing.email,
            organization_id=existing.organization_id,
            verification_email_sent=sent,
            message="A new verification email has been sent. Check your inbox.",
        )

    if existing and not existing.password_hash:
        # Placeholder from an org invite — complete their registration.
        existing.full_name = body.full_name
        existing.phone = body.phone
        existing.password_hash = hash_password(body.password)
        existing.is_active = False  # gated until verified
        existing.email_verified_at = None
        user = existing
        await db.flush()
    else:
        # Brand-new user — create their organization first.
        org = Organization(
            name=body.organization_name,
            slug=f"{_slugify(body.organization_name)}-{uuid.uuid4().hex[:6]}",
            max_seats=5,
        )
        db.add(org)
        await db.flush()

        user = UserProfile(
            email=email,
            full_name=body.full_name,
            phone=body.phone,
            password_hash=hash_password(body.password),
            organization_id=org.id,
            role="owner",
            is_active=False,            # gated on email verification
            email_verified_at=None,
            onboarding_completed=False,
            timezone="UTC",
            language="en",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        user.organization = org

    sent = await _send_verification(db, user)
    logger.info("Signup created user_id=%s; verification_sent=%s", user.id, sent)
    return SignupResponse(
        user_id=user.id,
        email=user.email,
        organization_id=user.organization_id,
        verification_email_sent=sent,
    )


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Redeem a verification token. On success: marks the user verified +
    active, sends the welcome email, and issues access + refresh tokens so the
    UI can drop them straight into the dashboard."""
    user_id = await verification_service.consume(
        db, token=body.token, purpose="verify_email"
    )
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_or_expired_token", "message": "This verification link is invalid or has expired. Request a new one."},
        )

    user = (await db.execute(
        select(UserProfile)
        .options(selectinload(UserProfile.organization))
        .where(UserProfile.id == user_id)
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")

    from datetime import datetime, timezone as _tz

    user.email_verified_at = datetime.now(_tz.utc)
    user.is_active = True
    await db.flush()
    await db.refresh(user)

    # First-time welcome email (only after they actually verified).
    try:
        subject, html, text = email_templates.welcome(full_name=user.full_name)
        await email_service.send_email(
            to=user.email, subject=subject, html=html, text=text
        )
    except Exception:
        logger.exception("welcome email failed for %s", user.id)

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
        user=_user_read(user),
    )


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    body: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Re-send the verification email. Always returns 202 regardless of whether
    the email exists, to avoid leaking which addresses are registered."""
    email = body.email.lower().strip()
    user = (await db.execute(
        select(UserProfile).where(UserProfile.email == email)
    )).scalar_one_or_none()

    if user is not None and user.password_hash and not user.email_verified_at:
        await _send_verification(db, user)

    return {"message": "If an account exists for that email and isn't verified yet, a new link is on its way."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password (JSON body)."""
    return await _authenticate(body.email, body.password, db)


@router.post("/token")
async def token_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible login for Swagger UI.

    Use your email as 'username' and your password in the Swagger Authorize dialog.
    """
    result = await _authenticate(form_data.username, form_data.password, db)
    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Get a new access + refresh token pair using a refresh token."""
    try:
        payload = decode_token(body.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired, please log in again",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(UserProfile)
        .options(selectinload(UserProfile.organization))
        .where(UserProfile.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=_user_read(user),
    )


@router.get("/me", response_model=UserProfileRead)
async def me(user: UserProfile = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return _user_read(user)


async def _authenticate(email: str, password: str, db: AsyncSession) -> TokenResponse:
    """Login logic shared by JSON and OAuth2-form endpoints.

    Order of checks matters: we always verify the password BEFORE telling the
    caller anything specific. That way a wrong password and a non-existent
    email both return the same generic 401 — a timing-attack/email-enum mitigation.
    Only after the password is correct do we reveal "email_not_verified" or
    "account_deactivated" with their specific codes.
    """
    email = (email or "").strip().lower()
    user = (await db.execute(
        select(UserProfile)
        .options(selectinload(UserProfile.organization))
        .where(UserProfile.email == email)
    )).scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid email or password."},
        )

    if user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "email_not_verified",
                "message": "Please verify your email before signing in. Check your inbox or request a new link.",
                "email": user.email,
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_deactivated", "message": "This account is deactivated. Contact support."},
        )

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
        user=_user_read(user),
    )
