"""Observability bootstrap: structured logging, Sentry, and OpenTelemetry.

All three are env-gated and no-op when their config vars are unset, so local
development and CI runs without external accounts work unchanged.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import get_settings
from app.utils.logging import configure_logging

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)
_initialized = False


def init_observability(app: "FastAPI") -> None:
    """Wire logging, Sentry, and OTel into the FastAPI app. Idempotent."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    settings = get_settings()
    configure_logging(level=logging.DEBUG if settings.debug else logging.INFO)
    _init_sentry(settings)
    _init_otel(app, settings)


def _init_sentry(settings) -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("sentry-sdk not installed; skipping Sentry init")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
            SqlalchemyIntegration(),
        ],
    )
    logger.info("Sentry initialized for environment=%s", settings.environment)


def _init_otel(app: "FastAPI", settings) -> None:
    if not settings.otel_exporter_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("OpenTelemetry packages not installed; skipping OTel init")
        return

    resource = Resource.create(
        {
            "service.name": settings.app_name.lower().replace(" ", "-"),
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint))
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/healthz")
    HTTPXClientInstrumentor().instrument()
    try:
        from app.utils.database import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except Exception:  # noqa: BLE001
        pass

    logger.info("OpenTelemetry initialized → %s", settings.otel_exporter_endpoint)
