"""Request-scoped context middleware.

Assigns each request a UUIDv4 request_id and decodes user/org from the JWT (if
present) into contextvars consumed by structured logging. Also records the
request duration for observability.
"""

from __future__ import annotations

import logging
import time
import uuid

import jwt as _jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import org_id_var, request_id_var, user_id_var

logger = logging.getLogger("vaktram.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        rt = request_id_var.set(rid)

        # Lightweight JWT inspection — full verification happens in deps.
        ut = ot = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                claims = _jwt.decode(
                    auth.split(" ", 1)[1],
                    options={"verify_signature": False},
                )
                ut = user_id_var.set(claims.get("sub"))
                ot = org_id_var.set(claims.get("org"))
            except Exception:  # noqa: BLE001
                pass

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            request_id_var.reset(rt)
            if ut is not None:
                user_id_var.reset(ut)
            if ot is not None:
                org_id_var.reset(ot)

        response.headers["x-request-id"] = rid
        logger.info(
            "%s %s -> %s in %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            dur_ms,
            extra={"duration_ms": round(dur_ms, 1), "status": response.status_code},
        )
        return response
