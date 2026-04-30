"""Zoom web-client meeting bot.

Joins via Zoom's browser client (`zoom.us/wc/<id>/join`). This works without
the Zoom SDK as long as the meeting allows web-client joins. Real audio
capture still flows through the same PulseAudio sink as Google Meet, since
the browser plays meeting audio to the system output.

Limits:
* Zoom may force the user to log in for some meetings — those will fail.
* Waiting room: handled by polling for the participant grid to appear.
* Encrypted meetings without a web-client option must use the Zoom SDK
  (planned later).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from bot.audio.capture import AudioCapture
from bot.platforms.base import BaseMeetingBot, BotState
from bot.utils.browser import create_browser_context

logger = logging.getLogger(__name__)


SELECTORS: dict[str, list[str]] = {
    "name_input": [
        '#inputname',
        'input[placeholder*="name" i]',
        'input[type="text"]',
    ],
    "join_button": [
        'button:has-text("Join")',
        'button#joinBtn',
    ],
    "in_call_marker": [
        'button[aria-label*="Leave" i]',
        'button:has-text("Leave")',
    ],
    "leave_button": [
        'button[aria-label*="Leave" i]',
        'button:has-text("Leave")',
    ],
    "end_screen": [
        'div:has-text("This meeting has been ended")',
        'div:has-text("Meeting ended")',
    ],
    "denied_screen": [
        'div:has-text("removed")',
        'div:has-text("not allowed")',
    ],
    "participant_count": [
        '[aria-label*="participants" i]',
        '.participants-section-container__participants-summary',
    ],
}


def _extract_zoom_meeting_id(url: str) -> tuple[str, str | None]:
    """Return (meeting_id, password) from any flavor of Zoom URL."""
    m = re.search(r"/(?:j|wc)/(\d+)", url)
    if not m:
        raise ValueError(f"Could not parse Zoom meeting id from {url}")
    meeting_id = m.group(1)
    pwd = parse_qs(urlparse(url).query).get("pwd", [None])[0]
    return meeting_id, pwd


def _to_web_client_url(url: str) -> str:
    """Coerce any zoom URL into the web-client form."""
    meeting_id, pwd = _extract_zoom_meeting_id(url)
    base = f"https://zoom.us/wc/{meeting_id}/join"
    return f"{base}?pwd={pwd}" if pwd else base


class ZoomBot(BaseMeetingBot):
    def __init__(self, meeting_url: str, bot_name: str, meeting_id: str):
        super().__init__(meeting_url, bot_name, meeting_id)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._audio_capture: Optional[AudioCapture] = None

    async def join(self) -> None:
        self.state = BotState.JOINING
        target = _to_web_client_url(self.meeting_url)
        logger.info("[%s] Joining Zoom (web client): %s", self.meeting_id, target)

        try:
            self._playwright = await async_playwright().start()
            self._browser, self._context = await create_browser_context(
                self._playwright,
                headless=os.getenv("HEADLESS", "true").lower() == "true",
            )
            self._page = await self._context.new_page()
            await self._page.goto(target, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(3)

            await self._fill_first(SELECTORS["name_input"], self.bot_name)
            if not await self._click_first(SELECTORS["join_button"]):
                raise RuntimeError("No Zoom join button found")

            joined = await self._wait_for(SELECTORS["in_call_marker"], timeout_ms=60_000)
            if not joined:
                raise RuntimeError("Did not enter Zoom meeting within timeout")

            self.state = BotState.IN_MEETING
            logger.info("[%s] Joined Zoom meeting", self.meeting_id)
        except Exception as exc:
            self.set_error(f"Zoom join failed: {exc}")
            await self._cleanup()
            raise

    async def leave(self) -> None:
        if self.state in (BotState.LEFT, BotState.IDLE):
            return
        self.state = BotState.LEAVING
        try:
            if self._page and not self._page.is_closed():
                await self._click_first(SELECTORS["leave_button"])
                await asyncio.sleep(1)
        except Exception:
            pass
        await self._cleanup()
        self.state = BotState.LEFT

    async def start_recording(self) -> None:
        if self.state != BotState.IN_MEETING:
            raise RuntimeError("Cannot start recording: not in meeting")
        self._audio_capture = AudioCapture(meeting_id=self.meeting_id)
        await self._audio_capture.start()
        self.state = BotState.RECORDING

    async def stop_recording(self) -> None:
        if self._audio_capture:
            await self._audio_capture.stop()
            self._audio_capture = None

    async def is_meeting_active(self) -> bool:
        if self._page is None or self._page.is_closed():
            return False
        for sel in SELECTORS["end_screen"] + SELECTORS["denied_screen"]:
            if await self._page.locator(sel).count() > 0:
                return False
        return True

    async def participant_count(self) -> int:
        if self._page is None or self._page.is_closed():
            return 0
        for sel in SELECTORS["participant_count"]:
            n = await self._page.locator(sel).count()
            if n > 0:
                return n
        return 0

    # ── helpers ───────────────────────────────────────────────────────

    async def _click_first(self, selectors: list[str]) -> bool:
        for sel in selectors:
            try:
                if not self._page:
                    return False
                loc = self._page.locator(sel).first
                if await loc.count() == 0:
                    continue
                await loc.click(timeout=8_000)
                return True
            except Exception:
                continue
        return False

    async def _fill_first(self, selectors: list[str], value: str) -> bool:
        for sel in selectors:
            try:
                if not self._page:
                    return False
                loc = self._page.locator(sel).first
                if await loc.count() == 0:
                    continue
                await loc.fill(value, timeout=8_000)
                return True
            except Exception:
                continue
        return False

    async def _wait_for(self, selectors: list[str], timeout_ms: int) -> bool:
        deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
        while asyncio.get_event_loop().time() < deadline:
            for sel in selectors:
                if self._page and await self._page.locator(sel).count() > 0:
                    return True
            await asyncio.sleep(2)
        return False

    async def _cleanup(self) -> None:
        for closer in (
            lambda: self._context and self._context.close(),
            lambda: self._browser and self._browser.close(),
            lambda: self._playwright and self._playwright.stop(),
        ):
            try:
                r = closer()
                if asyncio.iscoroutine(r):
                    await r
            except Exception:
                pass
        self._page = self._context = self._browser = self._playwright = None
