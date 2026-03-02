"""
Shared utility functions used across Vaktram services.
"""

import hashlib
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from packages.shared.constants import SUPPORTED_PLATFORMS


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with an optional prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC datetime as an ISO 8601 string."""
    return utc_now().isoformat()


def detect_platform(meeting_url: str) -> Optional[str]:
    """
    Detect the meeting platform from a URL.

    Returns the platform key (e.g., 'google_meet') or None if unrecognized.
    """
    for platform_key, config in SUPPORTED_PLATFORMS.items():
        if re.match(config["url_pattern"], meeting_url):
            return platform_key
    return None


def validate_meeting_url(meeting_url: str) -> bool:
    """Check if the URL matches any supported platform pattern."""
    return detect_platform(meeting_url) is not None


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    remaining = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {remaining}s"
    hours = minutes // 60
    remaining_min = minutes % 60
    return f"{hours}h {remaining_min}m"


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def hash_content(content: str) -> str:
    """Generate a SHA-256 hash of content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dictionaries."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


class RateLimiter:
    """Simple in-memory token-bucket rate limiter."""

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: list[float] = []

    def allow(self) -> bool:
        """Return True if the call is allowed under the rate limit."""
        now = time.time()
        self._calls = [t for t in self._calls if now - t < self.period]
        if len(self._calls) < self.max_calls:
            self._calls.append(now)
            return True
        return False

    def reset(self) -> None:
        self._calls.clear()
