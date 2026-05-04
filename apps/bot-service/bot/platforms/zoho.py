"""Zoho Meeting bot via the Zoho web client.

Zoho Meeting links come in two shapes (per the official Zoho Meeting API
docs at https://www.zoho.com/meeting/api-integration/):

  • https://meeting.zoho.com/join?key=<10-digit-key>      (canonical)
  • https://meet.zoho.com/<short-code>                    (share link)

Regional domains exist too: meeting.zoho.in / .eu / .com.au / .com.cn —
the same meeting key works across all of them.

Per Zoho's docs at help.zoho.com, the guest join page asks for:
    1. Name
    2. "Meeting ID or Meeting Link" (auto-filled when the URL has a key)
    3. CAPTCHA   ← see CAPTCHA NOTE below
    4. Password  (only if the host configured one — passed via env)

CAPTCHA NOTE
────────────
Zoho protects the public guest-join page with a CAPTCHA. A headless
Playwright bot cannot solve this on its own. Three workable paths:

  (a) Run with HEADLESS=false on a host with a real display and a human
      operator who solves the CAPTCHA on first join (cookies persist).
  (b) Wire in a CAPTCHA-solving service via env CAPTCHA_API_KEY (2Captcha,
      Anti-Captcha, etc.) — the hook is in `_solve_captcha_if_present`.
  (c) Have the host start the meeting from an authenticated Zoho session
      and add the bot as an attendee where the join link bypasses the
      challenge (org-level allow-listing).

Audio capture flows through the same PulseAudio sink as the other
platforms.

Selectors are best-effort fallbacks; Zoho's web client is a SPA whose
DOM isn't fully documented, so each role lists multiple candidates.
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
    # Zoho form labels are "Name" and "Meeting ID or Meeting Link". The
    # latter is auto-filled from the URL `key` param, but we set it
    # defensively in case the bot landed on the bare /join page.
    "name_input": [
        'input[name="name"]',
        'input[id*="name" i]',
        'input[placeholder*="name" i]',
        'input[aria-label*="name" i]',
    ],
    "meeting_id_input": [
        'input[name="meetingKey"]',
        'input[name="key"]',
        'input[placeholder*="Meeting ID" i]',
        'input[placeholder*="Meeting Link" i]',
        'input[aria-label*="Meeting ID" i]',
    ],
    "password_input": [
        'input[name="password"]',
        'input[type="password"]',
        'input[placeholder*="password" i]',
    ],
    "join_now": [
        'button:has-text("Join meeting")',
        'button:has-text("Join Meeting")',
        'button[type="submit"]:has-text("Join")',
        'input[type="submit"][value*="Join" i]',
    ],
    "captcha_iframe": [
        'iframe[src*="recaptcha"]',
        'iframe[src*="hcaptcha"]',
        'iframe[title*="captcha" i]',
        'div.g-recaptcha',
    ],
    "in_call_marker": [
        'button[aria-label*="Leave" i]',
        'button[title*="Leave" i]',
        'button:has-text("Leave")',
        'div[class*="meeting-controls" i]',
        'div[class*="control-bar" i]',
    ],
    "leave_button": [
        'button[aria-label*="Leave" i]',
        'button[title*="Leave" i]',
        'button:has-text("Leave")',
    ],
    "end_screen": [
        'div:has-text("This meeting has ended")',
        'div:has-text("The meeting has ended")',
        'div:has-text("Meeting has been ended")',
        'h1:has-text("Meeting ended")',
    ],
    "denied_screen": [
        'div:has-text("Waiting for approval")',
        'div:has-text("Host has not admitted you")',
        'div:has-text("waiting for the host")',
        'div:has-text("denied access")',
        'div:has-text("The meeting is locked")',
    ],
    "participant_count": [
        'button[aria-label*="participants" i]',
        'div[class*="participant-count" i]',
    ],
}


class ZohoBot(BaseMeetingBot):
    def __init__(self, meeting_url: str, bot_name: str, meeting_id: str):
        super().__init__(meeting_url, bot_name, meeting_id)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._audio_capture: Optional[AudioCapture] = None

    async def join(self) -> None:
        self.state = BotState.JOINING
        logger.info("[%s] Joining Zoho Meeting: %s", self.meeting_id, self.meeting_url)
        try:
            self._playwright = await async_playwright().start()
            self._browser, self._context = await create_browser_context(
                self._playwright,
                headless=os.getenv("HEADLESS", "true").lower() == "true",
            )
            self._page = await self._context.new_page()
            await self._page.goto(
                self.meeting_url, wait_until="domcontentloaded", timeout=30_000
            )
            await asyncio.sleep(3)

            await self._fill_first(SELECTORS["name_input"], self.bot_name)

            # If the host configured a meeting password, ZOHO_MEETING_PASSWORD
            # is passed in via the bot dispatch env. The field is absent for
            # password-less meetings; .fill is a no-op then.
            password = os.getenv("ZOHO_MEETING_PASSWORD", "")
            if password:
                await self._fill_first(SELECTORS["password_input"], password)

            # Best-effort CAPTCHA hand-off (see CAPTCHA NOTE in module docstring).
            await self._solve_captcha_if_present()

            if not await self._click_first(SELECTORS["join_now"]):
                raise RuntimeError("No Zoho 'Join meeting' button found")

            joined = await self._wait_for(
                SELECTORS["in_call_marker"], timeout_ms=120_000
            )
            if not joined:
                raise RuntimeError(
                    "Did not enter Zoho meeting within timeout — likely "
                    "blocked by CAPTCHA, host-approval, or a meeting password"
                )

            self.state = BotState.IN_MEETING
        except Exception as exc:
            self.set_error(f"Zoho join failed: {exc}")
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

    async def _solve_captcha_if_present(self) -> None:
        """Detect a CAPTCHA challenge and either solve it (if a service is
        configured) or wait for a human operator (if HEADLESS=false)."""
        if self._page is None:
            return
        captcha_seen = False
        for sel in SELECTORS["captcha_iframe"]:
            if await self._page.locator(sel).count() > 0:
                captcha_seen = True
                break
        if not captcha_seen:
            return

        api_key = os.getenv("CAPTCHA_API_KEY", "")
        if api_key:
            # Plug your CAPTCHA solver here (2Captcha, Anti-Captcha, etc.).
            # Left intentionally unimplemented — the bot logs and continues
            # so the failure surfaces as a clear "didn't enter meeting"
            # error rather than a silent solver-stub success.
            logger.warning(
                "[%s] CAPTCHA detected but no solver wired up; install your "
                "preferred service in _solve_captcha_if_present()",
                self.meeting_id,
            )
            return

        if os.getenv("HEADLESS", "true").lower() == "false":
            logger.warning(
                "[%s] CAPTCHA detected — waiting up to 90s for a human to solve",
                self.meeting_id,
            )
            await asyncio.sleep(90)
            return

        logger.error(
            "[%s] CAPTCHA detected on a headless run with no solver — "
            "join will fail. See bot/platforms/zoho.py CAPTCHA NOTE.",
            self.meeting_id,
        )

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
