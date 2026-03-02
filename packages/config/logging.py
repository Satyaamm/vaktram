"""
Shared logging configuration for all Vaktram services.
"""

import logging
import os
import sys
from typing import Optional


def setup_logging(
    service_name: str = "vaktram",
    level: Optional[str] = None,
    json_format: bool = False,
) -> logging.Logger:
    """
    Configure logging for a service.

    Args:
        service_name: Name of the service (used as logger name and in log output)
        level: Log level string (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var.
        json_format: If True, output structured JSON logs (for production).

    Returns:
        Configured root logger for the service.
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if json_format:
        formatter = JsonFormatter(service_name)
    else:
        formatter = logging.Formatter(
            f"%(asctime)s [{service_name}] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)

    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "asyncio", "playwright"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger = logging.getLogger(service_name)
    logger.info("Logging initialized (level=%s)", log_level)
    return logger


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for production environments."""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        if hasattr(record, "meeting_id"):
            log_entry["meeting_id"] = record.meeting_id

        return json.dumps(log_entry)
