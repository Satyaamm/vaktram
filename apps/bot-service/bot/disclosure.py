"""Recording-consent disclosure.

Two-party-consent jurisdictions (CA, IL, FL, MA, MD, NH, PA, WA, etc., plus
GDPR territories) require that everyone in the call is told it's being
recorded. We satisfy that by posting a short chat message immediately after
the bot joins. This is best-effort — if chat is disabled or the selectors
have shifted, the bot logs and continues; we record consent in our DB based
on the join itself plus the chat-attempt result.
"""

from __future__ import annotations

import logging
import os
from typing import Sequence

from playwright.async_api import Page

logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = (
    "Hi — Vaktram (https://vaktram.com) is recording and transcribing this "
    "meeting for note-taking. The host can stop recording at any time."
)


def consent_message() -> str:
    return os.getenv("VAKTRAM_CONSENT_MESSAGE", DEFAULT_MESSAGE)


# Each platform exposes (open-chat selectors, input selectors, send selectors).
# First match wins per list.
_PROFILES: dict[str, dict[str, list[str]]] = {
    "google_meet": {
        "open_chat": [
            'button[aria-label*="Chat with everyone" i]',
            'button[aria-label*="Chat" i]',
        ],
        "input": [
            'textarea[aria-label*="Send a message" i]',
            'textarea[aria-label*="message" i]',
            '[role="textbox"][aria-label*="message" i]',
        ],
        "send": [
            'button[aria-label*="Send message" i]',
            'button[aria-label*="Send" i]',
        ],
    },
    "zoom": {
        "open_chat": [
            'button[aria-label*="open the chat" i]',
            'button:has-text("Chat")',
        ],
        "input": [
            'textarea[aria-label*="chat message" i]',
            '[contenteditable="true"][aria-label*="chat" i]',
        ],
        "send": [
            'button[aria-label*="Send message" i]',
        ],
    },
    "teams": {
        "open_chat": [
            'button[aria-label*="Show conversation" i]',
            'button[aria-label*="Chat" i]',
        ],
        "input": [
            '[contenteditable="true"][aria-label*="Type a new message" i]',
            '[contenteditable="true"][aria-label*="message" i]',
        ],
        "send": [
            'button[aria-label*="Send" i]',
        ],
    },
    "zoho": {
        "open_chat": [
            'button[aria-label*="Chat" i]',
            'button[title*="Chat" i]',
            'button:has-text("Chat")',
        ],
        "input": [
            'textarea[placeholder*="message" i]',
            'textarea[aria-label*="message" i]',
            '[contenteditable="true"][aria-label*="message" i]',
        ],
        "send": [
            'button[aria-label*="Send" i]',
            'button[title*="Send" i]',
        ],
    },
}


async def announce(page: Page, *, platform: str, message: str | None = None) -> bool:
    """Try to send the consent message in the meeting chat.

    Returns True on success, False otherwise. Never raises — caller logs and
    continues regardless.
    """
    profile = _PROFILES.get(platform)
    if profile is None:
        logger.info("no consent-disclosure profile for platform=%s", platform)
        return False

    text = (message or consent_message()).strip()
    if not text:
        return False

    try:
        if not await _click_first(page, profile["open_chat"]):
            logger.info("could not open chat panel on %s", platform)
            return False

        if not await _fill_first(page, profile["input"], text):
            logger.info("could not focus chat input on %s", platform)
            return False

        # Try the explicit Send button; fall back to Enter.
        if not await _click_first(page, profile["send"]):
            try:
                await page.keyboard.press("Enter")
            except Exception:
                return False

        logger.info("recording-consent disclosure posted to %s", platform)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("consent disclosure failed on %s: %s", platform, exc)
        return False


async def _click_first(page: Page, selectors: Sequence[str]) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            await loc.click(timeout=4_000)
            return True
        except Exception:
            continue
    return False


async def _fill_first(page: Page, selectors: Sequence[str], text: str) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            try:
                await loc.fill(text, timeout=4_000)
            except Exception:
                # contenteditable elements sometimes need .type instead of .fill
                await loc.click(timeout=2_000)
                await loc.type(text, delay=15)
            return True
        except Exception:
            continue
    return False
