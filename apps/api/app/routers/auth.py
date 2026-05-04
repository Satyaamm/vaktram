"""Auth endpoints: signup, login, token refresh, current user."""

from __future__ import annotations

import logging
import uuid

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
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
from app.services import email_service, email_templates, session_service, verification_service
from app.utils.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_verify,
    hash_password,
    verify_password,
)

_REFRESH_TTL_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

# Cookie names. The refresh cookie is HttpOnly so JS (and any XSS payload)
# cannot read it. The session-hint cookie is plain text and exists only so
# the Next.js edge middleware can decide whether a user is logged in for
# route gating — it carries no credential, just "1".
REFRESH_COOKIE = "vaktram_refresh"
SESSION_HINT_COOKIE = "vaktram_session"


def _set_session_cookies(response: Response, refresh_token: str) -> None:
    """Plant the HttpOnly refresh cookie and the public session-hint cookie."""
    settings = get_settings()
    is_prod = settings.environment == "production"
    # SameSite=None is required when API + frontend live on different
    # registrable domains (vaktram-api.onrender.com vs *.vercel.app); it
    # MUST be paired with Secure=True. In dev we relax to Lax over plain
    # HTTP so localhost continues to work.
    samesite = "none" if is_prod else "lax"
    secure = is_prod
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=_REFRESH_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/api/v1/auth",  # only sent on auth routes — narrows blast radius
    )
    response.set_cookie(
        key=SESSION_HINT_COOKIE,
        value="1",
        max_age=_REFRESH_TTL_SECONDS,
        httponly=False,
        secure=secure,
        samesite=samesite,
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.delete_cookie(SESSION_HINT_COOKIE, path="/")


def _issue_refresh_for(user_id) -> str:
    """Mint a refresh token AND register its jti so we can revoke it later."""
    token, jti = create_refresh_token(user_id)
    session_service.register_refresh_jti(jti, str(user_id), _REFRESH_TTL_SECONDS)
    return token

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
async def verify_email(
    body: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
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

    refresh_token = _issue_refresh_for(user.id)
    _set_session_cookies(response, refresh_token)
    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=refresh_token,
        user=_user_read(user),
    )


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    body: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Re-send the verification email. Always returns 202 regardless of whether
    the email exists, to avoid leaking which addresses are registered.

    Hard cap: 3 sends per email per hour. Without this an attacker can pin
    a victim's inbox by spamming this endpoint. The rate limit is keyed on
    the email address rather than the requester IP so a botnet can't sneak
    around it."""
    email = body.email.lower().strip()

    if session_service.hit_rate_limit(
        f"verify-email:{email}", max_hits=3, window_seconds=3600
    ):
        # Still 202 — never reveal whether the throttle reflects a real
        # account or just hot-traffic.
        return {"message": "If an account exists for that email and isn't verified yet, a new link is on its way."}

    user = (await db.execute(
        select(UserProfile).where(UserProfile.email == email)
    )).scalar_one_or_none()

    if user is not None and user.password_hash and not user.email_verified_at:
        await _send_verification(db, user)

    return {"message": "If an account exists for that email and isn't verified yet, a new link is on its way."}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password (JSON body)."""
    result = await _authenticate(body.email, body.password, db)
    _set_session_cookies(response, result.refresh_token)
    return result


@router.post("/token")
async def token_for_swagger(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible login for Swagger UI.

    Use your email as 'username' and your password in the Swagger Authorize dialog.
    """
    result = await _authenticate(form_data.username, form_data.password, db)
    _set_session_cookies(response, result.refresh_token)
    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    body: RefreshRequest | None = None,
    vaktram_refresh: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get a new access + refresh token pair using a refresh token.

    Token source order: HttpOnly cookie first (modern clients), JSON body
    second (legacy / Swagger). New clients should send no body and rely on
    the cookie alone, which means an XSS payload cannot exfiltrate the
    refresh credential.

    Refresh tokens rotate: the incoming token's jti is revoked and a fresh
    one is issued. Re-using a revoked jti is treated as a stolen token and
    the request is rejected with 401."""
    incoming = vaktram_refresh or (body.refresh_token if body else None)
    if not incoming:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    try:
        payload = decode_token(incoming)
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

    incoming_jti = payload.get("jti")
    if not session_service.is_refresh_active(incoming_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked, please log in again",
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

    # Rotate: invalidate the old jti before issuing a new one. Order matters:
    # if a concurrent /refresh with the same token arrives, only the first
    # one will see it active and revoke it; the second sees the revoked
    # state and rejects.
    session_service.revoke_refresh_jti(incoming_jti, _REFRESH_TTL_SECONDS)

    access_token = create_access_token(user.id, user.email)
    new_refresh_token = _issue_refresh_for(user.id)
    _set_session_cookies(response, new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=_user_read(user),
    )


@router.get("/me", response_model=UserProfileRead)
async def me(user: UserProfile = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return _user_read(user)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    body: LogoutRequest | None = None,
    vaktram_refresh: str | None = Cookie(default=None),
):
    """Revoke the supplied refresh token and clear session cookies.

    The endpoint is intentionally unauthenticated so a client whose access
    token already expired can still log out. The access token (short-lived,
    15 min) isn't tracked per-token; revoking the refresh forces re-auth on
    next /refresh, the realistic upper bound on a stolen access token."""
    _clear_session_cookies(response)
    incoming = vaktram_refresh or (body.refresh_token if body else None)
    if not incoming:
        return
    try:
        payload = decode_token(incoming)
    except jwt.InvalidTokenError:
        # Idempotent: already-invalid tokens succeed silently so the client
        # always gets a clean 204.
        return
    if payload.get("type") != "refresh":
        return
    session_service.revoke_refresh_jti(payload.get("jti"), _REFRESH_TTL_SECONDS)


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

    # Branchless timing equalisation: a missing user still triggers a bcrypt
    # round so login latency reveals nothing about whether the email exists.
    if not user or not user.password_hash:
        dummy_verify(password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid email or password."},
        )

    if not verify_password(password, user.password_hash):
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
        refresh_token=_issue_refresh_for(user.id),
        user=_user_read(user),
    )
