"""Microsoft Teams meeting bot via the Teams web client.

Teams meeting links are of the form
`https://teams.microsoft.com/l/meetup-join/...`. The web client allows guest
joins without a Microsoft 365 account when the organizer enabled it.
Audio capture flows through the same PulseAudio sink as the other platforms.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from bot.audio.capture import AudioCapture
from bot.platforms.base import BaseMeetingBot, BotState
from bot.utils.browser import create_browser_context

logger = logging.getLogger(__name__)


SELECTORS: dict[str, list[str]] = {
    "join_on_web_button": [
        'button:has-text("Continue on this browser")',
        'a:has-text("Continue on this browser")',
        'button:has-text("Join on the web instead")',
    ],
    "name_input": [
        'input[placeholder*="name" i]',
        '#username',
    ],
    "join_now": [
        'button:has-text("Join now")',
        'button[aria-label*="Join now" i]',
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
        'div:has-text("The meeting has ended")',
        'h1:has-text("The meeting has ended")',
    ],
    "denied_screen": [
        'div:has-text("Sorry, but you were denied access")',
        'div:has-text("not letting you in")',
    ],
    "participant_count": [
        '[aria-label*="participants" i]',
    ],
}


class TeamsBot(BaseMeetingBot):
    def __init__(self, meeting_url: str, bot_name: str, meeting_id: str):
        super().__init__(meeting_url, bot_name, meeting_id)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._audio_capture: Optional[AudioCapture] = None

    async def join(self) -> None:
        self.state = BotState.JOINING
        logger.info("[%s] Joining Teams: %s", self.meeting_id, self.meeting_url)
        try:
            self._playwright = await async_playwright().start()
            self._browser, self._context = await create_browser_context(
                self._playwright,
                headless=os.getenv("HEADLESS", "true").lower() == "true",
            )
            self._page = await self._context.new_page()
            await self._page.goto(self.meeting_url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(3)

            # Teams sometimes shows a "Join on web vs desktop" picker first.
            await self._click_first(SELECTORS["join_on_web_button"])
            await asyncio.sleep(2)

            await self._fill_first(SELECTORS["name_input"], self.bot_name)

            if not await self._click_first(SELECTORS["join_now"]):
                raise RuntimeError("No Teams 'Join now' button found")

            joined = await self._wait_for(SELECTORS["in_call_marker"], timeout_ms=120_000)
            if not joined:
                raise RuntimeError("Did not enter Teams meeting within timeout")

            self.state = BotState.IN_MEETING
        except Exception as exc:
            self.set_error(f"Teams join failed: {exc}")
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
