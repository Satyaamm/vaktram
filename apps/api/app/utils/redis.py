"""Upstash Redis client."""

from upstash_redis import Redis
from app.config import get_settings

settings = get_settings()

_redis: Redis | None = None


def get_redis_client() -> Redis:
    """Return a cached Upstash Redis client."""
    global _redis
    if _redis is None:
        if not settings.upstash_redis_url or not settings.upstash_redis_token:
            raise RuntimeError(
                "UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN must be set"
            )
        _redis = Redis(
            url=settings.upstash_redis_url,
            token=settings.upstash_redis_token,
        )
    return _redis
