"""Cross-instance WebSocket fan-out via Upstash Redis pub/sub.

publish() writes a message to a channel; each API replica's subscriber loop
forwards it to the local ConnectionManager. This means a transcribe worker
running on a different pod can still notify a UI WebSocket connected to a
different API replica.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()
_CHANNEL_PREFIX = "rt"


def channel_for_meeting(meeting_id: str) -> str:
    return f"{_CHANNEL_PREFIX}:meeting:{meeting_id}"


def channel_for_user(user_id: str) -> str:
    return f"{_CHANNEL_PREFIX}:user:{user_id}"


async def publish(channel: str, payload: dict[str, Any]) -> None:
    """Best-effort fire-and-forget publish.

    The Upstash REST client is sync; we run it in a thread so we don't block
    the event loop. If Redis is unconfigured we just log — the local
    ConnectionManager broadcast is still called separately by the caller.
    """
    if not (_settings.upstash_redis_url and _settings.upstash_redis_token):
        logger.debug("realtime publish (noop, no redis): %s %s", channel, payload)
        return
    try:
        from app.utils.redis import get_redis_client

        await asyncio.to_thread(
            get_redis_client().publish, channel, json.dumps(payload, default=str)
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("realtime publish failed for %s: %s", channel, e)
