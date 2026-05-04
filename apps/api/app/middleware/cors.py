"""CORS configuration.

Supports both an explicit allowlist (CORS_ORIGINS env var, comma-separated)
and a regex (CORS_ORIGIN_REGEX env var) — handy for Vercel preview deploys
which generate random subdomains like vaktram-abc123-team.vercel.app.

Defaults include localhost dev ports. In production set CORS_ORIGINS to your
Vercel production URL and (optionally) CORS_ORIGIN_REGEX to allow previews.

Security note: we always use ``allow_credentials=True`` because the API now
issues HttpOnly cookies for refresh tokens. That makes a permissive origin
regex catastrophic — any allowed origin can drive authenticated requests.
The validators below refuse to boot if the regex looks dangerously open.
"""

import logging
import os
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)


# Allow any *.vercel.app subdomain by default — Vercel preview URLs include
# the project name + commit hash + team, e.g.
# vaktram-fcwyvzha3-commons-projects-f30f22a6.vercel.app
DEFAULT_ORIGIN_REGEX = r"^https://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.vercel\.app$"

# Patterns we refuse to use with allow_credentials=True. The list is not
# exhaustive — it's a tripwire for the most common mistakes.
_DANGEROUS_REGEXES = (
    r".*",
    r".+",
    r"^.*$",
    r"^.+$",
    r"^https?://.*$",
)


def _validate_origin_regex(regex: str) -> None:
    """Refuse to boot on patterns that would let any origin in. We can't
    statically prove a regex is safe, but we can catch the obvious holes."""
    if regex.strip() in _DANGEROUS_REGEXES:
        raise RuntimeError(
            f"CORS_ORIGIN_REGEX={regex!r} is too permissive while "
            f"allow_credentials=True. Tighten it to a specific domain pattern."
        )
    # The regex must compile — otherwise CORSMiddleware silently allows
    # nothing and you get baffling cross-origin errors at runtime.
    try:
        re.compile(regex)
    except re.error as exc:
        raise RuntimeError(f"CORS_ORIGIN_REGEX failed to compile: {exc}")


def add_cors_middleware(app: FastAPI) -> None:
    settings = get_settings()
    origin_regex = os.getenv("CORS_ORIGIN_REGEX", DEFAULT_ORIGIN_REGEX)
    _validate_origin_regex(origin_regex)
    logger.info(
        "CORS configured: allowlist=%s regex=%s credentials=on",
        settings.cors_origins_list, origin_regex,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
