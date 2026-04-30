"""Structured JSON logging.

Emits one JSON object per log record with the request_id and tenant from the
contextvars set by RequestContextMiddleware. In development we keep human-
readable text logs; in staging/prod we switch to JSON for log aggregators.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar

from app.config import get_settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
org_id_var: ContextVar[str | None] = ContextVar("org_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if rid := request_id_var.get():
            payload["request_id"] = rid
        if uid := user_id_var.get():
            payload["user_id"] = uid
        if oid := org_id_var.get():
            payload["org_id"] = oid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Allow extra=... fields from log calls
        for k, v in record.__dict__.items():
            if k in payload or k.startswith("_"):
                continue
            if k in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message", "module",
                "msecs", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName", "taskName",
            ):
                continue
            try:
                json.dumps(v)
                payload[k] = v
            except TypeError:
                payload[k] = repr(v)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    if settings.environment in ("production", "staging"):
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Hush noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
