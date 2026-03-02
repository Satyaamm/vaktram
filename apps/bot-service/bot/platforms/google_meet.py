"""
Google Meet bot implemented with Playwright.
Joins a Google Meet call via a browser, captures system audio through PulseAudio,
and streams it for transcription.
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

# Google Meet DOM selectors (these may change; keep them configurable)
SELECTORS = {
    "name_input": 'input[aria-label="Your name"]',
    "join_button": "button:has-text('Ask to join'), button:has-text('Join now')",
    "mute_mic": 'button[aria-label*="Turn off microphone"]',
    "mute_camera": 'button[aria-label*="Turn off camera"]',
    "leave_button": 'button[aria-label="Leave call"]',
    "participant_count": '[data-participant-id]',
    "end_screen": 'div:has-text("You left the meeting")',
}


class GoogleMeetBot(BaseMeetingBot):
    """Playwright-based Google Meet bot."""

    def __init__(
        self,
        meeting_url: str,
        bot_name: str,
        meeting_id: str,
    ):
        super().__init__(meeting_url, bot_name, meeting_id)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._audio_capture: Optional[AudioCapture] = None

    async def join(self) -> None:
        """Launch browser, navigate to meet link, and join."""
        self.state = BotState.JOINING
        logger.info("[%s] Joining Google Meet: %s", self.meeting_id, self.meeting_url)

        try:
            self._playwright = await async_playwright().start()

            self._browser, self._context = await create_browser_context(
                self._playwright,
                headless=os.getenv("HEADLESS", "true").lower() == "true",
            )

            self._page = await self._context.new_page()

            # Navigate to the meeting
            await self._page.goto(self.meeting_url, wait_until="networkidle", timeout=30_000)

            # Mute mic and camera before joining
            await self._try_click(SELECTORS["mute_mic"], timeout=5_000)
            await self._try_click(SELECTORS["mute_camera"], timeout=5_000)

            # Enter display name if the field is present (guest join)
            name_input = self._page.locator(SELECTORS["name_input"])
            if await name_input.count() > 0:
                await name_input.fill(self.bot_name)

            # Click "Ask to join" or "Join now"
            join_btn = self._page.locator(SELECTORS["join_button"]).first
            await join_btn.click(timeout=10_000)

            # Wait briefly for the meeting UI to load
            await asyncio.sleep(5)

            self.state = BotState.IN_MEETING
            logger.info("[%s] Successfully joined meeting", self.meeting_id)

        except Exception as exc:
            self.set_error(f"Failed to join: {exc}")
            logger.exception("[%s] Join failed", self.meeting_id)
            raise

    async def leave(self) -> None:
        """Click leave button and close browser."""
        if self.state in (BotState.LEFT, BotState.IDLE):
            return

        self.state = BotState.LEAVING
        logger.info("[%s] Leaving meeting", self.meeting_id)

        try:
            if self._page and not self._page.is_closed():
                await self._try_click(SELECTORS["leave_button"], timeout=5_000)
                await asyncio.sleep(1)
        except Exception:
            logger.warning("[%s] Could not click leave button", self.meeting_id)

        await self._cleanup_browser()
        self.state = BotState.LEFT

    async def start_recording(self) -> None:
        """Start capturing audio via PulseAudio virtual sink."""
        if self.state != BotState.IN_MEETING:
            raise RuntimeError("Cannot start recording: not in meeting")

        self._audio_capture = AudioCapture(meeting_id=self.meeting_id)
        await self._audio_capture.start()
        self.state = BotState.RECORDING
        logger.info("[%s] Recording started", self.meeting_id)

    async def stop_recording(self) -> None:
        """Stop audio capture."""
        if self._audio_capture:
            await self._audio_capture.stop()
            self._audio_capture = None
            logger.info("[%s] Recording stopped", self.meeting_id)

    async def is_meeting_active(self) -> bool:
        """Check whether the meeting is still ongoing by looking for end-screen."""
        if self._page is None or self._page.is_closed():
            return False
        end = self._page.locator(SELECTORS["end_screen"])
        return await end.count() == 0

    async def participant_count(self) -> int:
        """Return approximate number of participants visible in the DOM."""
        if self._page is None or self._page.is_closed():
            return 0
        els = self._page.locator(SELECTORS["participant_count"])
        return await els.count()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _try_click(self, selector: str, timeout: int = 3_000) -> bool:
        """Attempt to click a selector, return False on failure."""
        try:
            locator = self._page.locator(selector).first
            await locator.click(timeout=timeout)
            return True
        except Exception:
            return False

    async def _cleanup_browser(self) -> None:
        """Close browser resources."""
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
