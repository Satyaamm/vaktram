"""Rate limiting middleware using Upstash Redis."""

from __future__ import annotations

import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import get_settings
from app.utils.redis import get_redis_client

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Upstash Redis."""

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.rpm = requests_per_minute or settings.rate_limit_per_minute

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/healthz", "/api/v1/health"):
            return await call_next(request)

        # Identify caller by user id (from JWT) or IP
        user_id: str | None = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            # Lightweight extraction -- full verification happens later
            import jwt as _jwt

            try:
                payload = _jwt.decode(
                    auth.split(" ", 1)[1],
                    options={"verify_signature": False},
                )
                user_id = payload.get("sub")
            except Exception:
                pass

        identifier = user_id or (request.client.host if request.client else "unknown")
        key = f"rate_limit:{identifier}"

        try:
            redis = get_redis_client()
            now = int(time.time())
            window_start = now - 60

            # Use a sorted set: score = timestamp
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{now}:{id(request)}": now})
            pipe.zcard(key)
            pipe.expire(key, 120)
            results = pipe.execute()

            request_count = results[2]
            if request_count > self.rpm:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later.",
                )
        except HTTPException:
            raise
        except Exception:
            # If Redis is down, allow the request through
            pass

        response = await call_next(request)
        return response
