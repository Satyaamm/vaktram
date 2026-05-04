"""Refresh-token lifecycle: register, rotate, revoke.

Each refresh token carries a `jti` (JWT ID). We persist the jti in Redis with
a TTL matching the token's lifetime. Three operations:

  • register(jti, user_id, ttl)  ← issued at login / signup / refresh / verify
  • is_active(jti)               ← consulted on /refresh and /me
  • revoke(jti)                  ← consulted on /logout, and on /refresh after
                                   we successfully rotate (so the old token
                                   cannot be replayed)

When Redis is not configured (local dev), we fail open: every token is
considered active and no rotation tracking is performed. This keeps tests
running without a Redis dependency, but production MUST configure Redis.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Key namespaces. We store every active jti under one namespace and revoked
# jtis under another so a single round-trip can prove "this token is the one
# we issued AND has not been revoked".
_ACTIVE_PREFIX = "session:active:"
_REVOKED_PREFIX = "session:revoked:"


def _redis_or_none():
    settings = get_settings()
    if not (settings.upstash_redis_url and settings.upstash_redis_token):
        return None
    try:
        return get_redis_client()
    except Exception:
        logger.exception("Redis unavailable; session tracking disabled")
        return None


def register_refresh_jti(jti: str, user_id: str, ttl_seconds: int) -> None:
    """Mark a freshly-issued refresh token as active. Called on every code
    path that mints a refresh token (signup, login, verify-email, refresh,
    SSO callback)."""
    redis = _redis_or_none()
    if redis is None:
        return
    try:
        redis.set(_ACTIVE_PREFIX + jti, user_id, ex=ttl_seconds)
    except Exception:
        logger.exception("Failed to register session jti %s", jti)


def is_refresh_active(jti: str | None) -> bool:
    """Return True if the jti is in the active set and not in the revoked
    set. With Redis disabled (dev) we fall open and return True."""
    if not jti:
        return False
    redis = _redis_or_none()
    if redis is None:
        return True  # dev: trust the JWT signature alone
    try:
        if redis.get(_REVOKED_PREFIX + jti):
            return False
        return bool(redis.get(_ACTIVE_PREFIX + jti))
    except Exception:
        logger.exception("Failed to check session jti %s", jti)
        # Fail closed on Redis errors — better to log everyone out than to
        # silently accept revoked tokens. Production should never hit this.
        return False


def revoke_refresh_jti(jti: str | None, ttl_seconds: int = 86400) -> None:
    """Mark a jti as revoked. Idempotent. TTL should be ≥ token lifetime so
    the revocation outlives the token."""
    if not jti:
        return
    redis = _redis_or_none()
    if redis is None:
        return
    try:
        redis.set(_REVOKED_PREFIX + jti, "1", ex=ttl_seconds)
        redis.delete(_ACTIVE_PREFIX + jti)
    except Exception:
        logger.exception("Failed to revoke session jti %s", jti)


# ── Per-key rate limiting (used by email-sending endpoints) ──────────────
_RATE_PREFIX = "ratelimit:"


def hit_rate_limit(key: str, *, max_hits: int, window_seconds: int) -> bool:
    """Atomically increment a counter; return True if limit exceeded.

    Used to throttle expensive or abusable side-effects (e.g. sending email
    to a given address). When Redis is unavailable, fails open — better to
    deliver the side-effect than to lock users out. Operators relying on
    this must ensure Redis is reachable in production."""
    redis = _redis_or_none()
    if redis is None:
        return False
    try:
        rkey = _RATE_PREFIX + key
        count = redis.incr(rkey)
        if count == 1:
            redis.expire(rkey, window_seconds)
        return count > max_hits
    except Exception:
        logger.exception("Rate limit check failed for key=%s", key)
        return False
