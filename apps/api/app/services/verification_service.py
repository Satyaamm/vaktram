"""Email verification token issue + redeem.

Tokens are 32-byte URL-safe random strings. We store ONLY their sha256 hash —
the plaintext only exists in the email link, so a DB leak can't grant access.
Default lifetime: 24h for verify_email, 30 min for password_reset.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import EmailVerificationToken

VERIFY_TTL = timedelta(hours=24)
RESET_TTL = timedelta(minutes=30)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def issue(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    purpose: str = "verify_email",
) -> str:
    """Generate a token, persist its hash, return the plaintext."""
    plaintext = secrets.token_urlsafe(32)
    ttl = VERIFY_TTL if purpose == "verify_email" else RESET_TTL
    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=_hash(plaintext),
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + ttl,
        )
    )
    await db.flush()
    return plaintext


async def consume(
    db: AsyncSession, *, token: str, purpose: str = "verify_email"
) -> uuid.UUID | None:
    """Look up + redeem a token. Returns user_id on success, None otherwise.

    Valid only if: hash matches, purpose matches, not expired, not already used.
    Marks `used_at` so it can't be replayed.
    """
    row = (await db.execute(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.token_hash == _hash(token))
        .where(EmailVerificationToken.purpose == purpose)
    )).scalar_one_or_none()
    if row is None:
        return None
    if row.used_at is not None:
        return None
    if row.expires_at < datetime.now(timezone.utc):
        return None
    row.used_at = datetime.now(timezone.utc)
    await db.flush()
    return row.user_id


async def invalidate_existing(
    db: AsyncSession, *, user_id: uuid.UUID, purpose: str = "verify_email"
) -> None:
    """Mark any outstanding tokens for this user+purpose as used so old
    links stop working before we issue a new one."""
    rows = (await db.execute(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.user_id == user_id)
        .where(EmailVerificationToken.purpose == purpose)
        .where(EmailVerificationToken.used_at.is_(None))
    )).scalars().all()
    now = datetime.now(timezone.utc)
    for r in rows:
        r.used_at = now
    await db.flush()
