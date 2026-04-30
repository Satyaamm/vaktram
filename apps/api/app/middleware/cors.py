"""CORS configuration.

Supports both an explicit allowlist (CORS_ORIGINS env var, comma-separated)
and a regex (CORS_ORIGIN_REGEX env var) — handy for Vercel preview deploys
which generate random subdomains like vaktram-abc123-team.vercel.app.

Defaults include localhost dev ports. In production set CORS_ORIGINS to your
Vercel production URL and (optionally) CORS_ORIGIN_REGEX to allow previews.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


# Allow any *.vercel.app subdomain by default — Vercel preview URLs include
# the project name + commit hash + team, e.g.
# vaktram-fcwyvzha3-commons-projects-f30f22a6.vercel.app
DEFAULT_ORIGIN_REGEX = r"^https://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.vercel\.app$"


def add_cors_middleware(app: FastAPI) -> None:
    settings = get_settings()
    origin_regex = os.getenv("CORS_ORIGIN_REGEX", DEFAULT_ORIGIN_REGEX)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
