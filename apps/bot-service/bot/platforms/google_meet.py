"""
Google Meet bot implemented with Playwright.

Reliability notes:
* Meet streams data continuously, so `wait_until="networkidle"` never resolves
  within a sensible timeout — we use `domcontentloaded` and explicit waits.
* Selectors are checked through a list of fallbacks so a small DOM change in
  Meet doesn't fully break the joiner. New selectors get added to the front
  of each list when Google ships UI tweaks.
* `is_meeting_active()` checks both the visible end-of-meeting screen and the
  participant count — when only the bot is left, the call is over.
"""

import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from bot.audio.capture import AudioCapture
from bot.platforms.base import BaseMeetingBot, BotState
from bot.utils.browser import create_browser_context

logger = logging.getLogger(__name__)

# Each entry is a list of selectors tried in order — first match wins.
SELECTORS: dict[str, list[str]] = {
    "name_input": [
        'input[aria-label="Your name"]',
        'input[placeholder*="name" i]',
        'input[type="text"]',
    ],
    "join_button": [
        'button:has-text("Ask to join")',
        'button:has-text("Join now")',
        'button:has-text("Join meeting")',
        '[role="button"]:has-text("Ask to join")',
    ],
    "mute_mic": [
        'button[aria-label*="Turn off microphone" i]',
        'button[aria-label*="Mute microphone" i]',
        'div[role="button"][aria-label*="microphone" i][data-is-muted="false"]',
    ],
    "mute_camera": [
        'button[aria-label*="Turn off camera" i]',
        'button[aria-label*="camera off" i]',
    ],
    "leave_button": [
        'button[aria-label="Leave call"]',
        'button[aria-label*="Leave" i]',
    ],
    "participant_count": [
        '[data-participant-id]',
        '[aria-label*="participants" i]',
    ],
    "end_screen": [
        'div:has-text("You left the meeting")',
        'div:has-text("Rejoin")',
        'h1:has-text("You left")',
    ],
    "denied_screen": [
        'div:has-text("You can\'t join this video call")',
        'div:has-text("Your request to join was denied")',
    ],
}

JOIN_TIMEOUT_MS = 60_000     # full join window
NAV_TIMEOUT_MS = 30_000      # initial page load
INTERACTION_TIMEOUT_MS = 8_000


class GoogleMeetBot(BaseMeetingBot):
    """Playwright-based Google Meet bot."""

    def __init__(self, meeting_url: str, bot_name: str, meeting_id: str):
        super().__init__(meeting_url, bot_name, meeting_id)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._audio_capture: Optional[AudioCapture] = None

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def join(self) -> None:
        self.state = BotState.JOINING
        logger.info("[%s] Joining Google Meet: %s", self.meeting_id, self.meeting_url)

        try:
            self._playwright = await async_playwright().start()
            self._browser, self._context = await create_browser_context(
                self._playwright,
                headless=os.getenv("HEADLESS", "true").lower() == "true",
            )
            self._page = await self._context.new_page()

            # Use domcontentloaded — Meet's network never goes idle.
            await self._page.goto(
                self.meeting_url,
                wait_until="domcontentloaded",
                timeout=NAV_TIMEOUT_MS,
            )
            # Give the join lobby a moment to render.
            await asyncio.sleep(3)

            # Mute mic + camera (best effort — buttons may already be muted).
            await self._click_first(SELECTORS["mute_mic"])
            await self._click_first(SELECTORS["mute_camera"])

            # Fill display name if a guest input is shown.
            await self._fill_first(SELECTORS["name_input"], self.bot_name)

            # Click join. This is the only required interaction.
            if not await self._click_first(SELECTORS["join_button"]):
                raise RuntimeError("No join button found — UI may have changed")

            # Wait until either the call UI loads, or the IdP denies entry.
            joined = await self._wait_for_in_call(timeout_ms=JOIN_TIMEOUT_MS)
            if not joined:
                raise RuntimeError("Did not enter the meeting within timeout")

            self.state = BotState.IN_MEETING
            logger.info("[%s] Successfully joined meeting", self.meeting_id)

        except Exception as exc:
            self.set_error(f"Failed to join: {exc}")
            logger.exception("[%s] Join failed", self.meeting_id)
            await self._cleanup_browser()
            raise

    async def leave(self) -> None:
        if self.state in (BotState.LEFT, BotState.IDLE):
            return

        self.state = BotState.LEAVING
        logger.info("[%s] Leaving meeting", self.meeting_id)

        try:
            if self._page and not self._page.is_closed():
                await self._click_first(SELECTORS["leave_button"])
                await asyncio.sleep(1)
        except Exception:
            logger.warning("[%s] Could not click leave button", self.meeting_id)

        await self._cleanup_browser()
        self.state = BotState.LEFT

    async def start_recording(self) -> None:
        if self.state != BotState.IN_MEETING:
            raise RuntimeError("Cannot start recording: not in meeting")
        self._audio_capture = AudioCapture(meeting_id=self.meeting_id)
        await self._audio_capture.start()
        self.state = BotState.RECORDING
        logger.info("[%s] Recording started", self.meeting_id)

    async def stop_recording(self) -> None:
        if self._audio_capture:
            await self._audio_capture.stop()
            self._audio_capture = None
            logger.info("[%s] Recording stopped", self.meeting_id)

    # ── Meeting state probes ───────────────────────────────────────────

    async def is_meeting_active(self) -> bool:
        """Return False when the bot has been kicked, the host ended the
        call, or only the bot is left."""
        if self._page is None or self._page.is_closed():
            return False
        for sel in SELECTORS["end_screen"]:
            if await self._page.locator(sel).count() > 0:
                logger.info("[%s] End-of-meeting screen detected", self.meeting_id)
                return False
        for sel in SELECTORS["denied_screen"]:
            if await self._page.locator(sel).count() > 0:
                logger.warning("[%s] Bot was denied/removed", self.meeting_id)
                return False
        # If the participant count is exactly 1, only we're left — call over.
        count = await self.participant_count()
        if count == 1:
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

    # ── Internal helpers ───────────────────────────────────────────────

    async def _wait_for_in_call(self, timeout_ms: int) -> bool:
        """Poll for either the leave button (joined) or denied screen."""
        deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
        while asyncio.get_event_loop().time() < deadline:
            if not self._page or self._page.is_closed():
                return False
            for sel in SELECTORS["leave_button"]:
                if await self._page.locator(sel).count() > 0:
                    return True
            for sel in SELECTORS["denied_screen"]:
                if await self._page.locator(sel).count() > 0:
                    return False
            await asyncio.sleep(2)
        return False

    async def _click_first(self, selectors: list[str]) -> bool:
        for sel in selectors:
            if await self._try_click(sel, timeout=INTERACTION_TIMEOUT_MS):
                return True
        return False

    async def _fill_first(self, selectors: list[str], value: str) -> bool:
        if not self._page:
            return False
        for sel in selectors:
            try:
                loc = self._page.locator(sel).first
                if await loc.count() == 0:
                    continue
                await loc.fill(value, timeout=INTERACTION_TIMEOUT_MS)
                return True
            except Exception:
                continue
        return False

    async def _try_click(self, selector: str, timeout: int) -> bool:
        try:
            if not self._page:
                return False
            loc = self._page.locator(selector).first
            if await loc.count() == 0:
                return False
            await loc.click(timeout=timeout)
            return True
        except Exception:
            return False

    async def _cleanup_browser(self) -> None:
        for closer in (
            lambda: self._context and self._context.close(),
            lambda: self._browser and self._browser.close(),
            lambda: self._playwright and self._playwright.stop(),
        ):
            try:
                result = closer()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
