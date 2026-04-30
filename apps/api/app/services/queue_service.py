"""QStash queue service for publishing pipeline jobs.

Falls back to a local fire-and-forget call when QStash is not configured so
that local development and self-hosted installs without an Upstash account
still drive the pipeline forward. The fallback is detached from the request
that triggered it (asyncio.create_task) so the caller returns 200 quickly,
matching QStash's behavior.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

QSTASH_PUBLISH_URL = "https://qstash.upstash.io/v2/publish"
_INLINE_TIMEOUT = 600  # transcription/summarization can be long


async def publish_job(endpoint_path: str, payload: dict) -> str | None:
    """Publish a job for asynchronous processing.

    If QStash is configured: enqueue via QStash with retries.
    Otherwise: spawn a detached background task that calls the endpoint
    directly. Both paths behave the same from the caller's perspective —
    the request returns immediately and the work happens out-of-band.

    Returns the QStash message id, or `"inline:..."` for the fallback path.
    """
    destination = f"{settings.api_base_url}{endpoint_path}"

    if settings.qstash_token:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{QSTASH_PUBLISH_URL}/{destination}",
                headers={
                    "Authorization": f"Bearer {settings.qstash_token}",
                    "Content-Type": "application/json",
                    "Upstash-Retries": "3",
                },
                json=payload,
            )
            resp.raise_for_status()
            msg_id = resp.json().get("messageId")
            logger.info("QStash job published: %s -> %s", msg_id, endpoint_path)
            return msg_id

    # Inline fallback — never block the caller, fire-and-forget.
    asyncio.create_task(_call_inline(destination, payload))
    logger.info("QStash not configured; running %s inline", endpoint_path)
    return f"inline:{endpoint_path}"


async def _call_inline(url: str, payload: dict) -> None:
    """Call our own internal endpoint as if QStash had delivered the job."""
    try:
        async with httpx.AsyncClient(timeout=_INLINE_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 400:
                logger.error(
                    "Inline pipeline call failed %s: %d %s",
                    url, resp.status_code, resp.text[:200],
                )
            else:
                logger.info("Inline pipeline call ok: %s", url)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Inline pipeline call crashed for %s: %s", url, exc)


def verify_qstash_signature(body: bytes, signature: str) -> bool:
    """Verify that a request came from QStash using the signing keys."""
    current_key = settings.qstash_current_signing_key
    next_key = settings.qstash_next_signing_key

    if not current_key and not next_key:
        logger.warning("QStash signing keys not configured, skipping verification")
        return True

    for key in [current_key, next_key]:
        if not key:
            continue
        expected = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            return True

    return False
