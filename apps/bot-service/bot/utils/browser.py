"""
Playwright browser setup helper.
Configures Chromium with the correct flags for headless meeting join,
PulseAudio audio routing, and fake media streams.
"""

import logging
import os
from typing import Optional, Tuple

from playwright.async_api import Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)


async def create_browser_context(
    playwright: Playwright,
    headless: bool = True,
    storage_state_path: Optional[str] = None,
) -> Tuple[Browser, BrowserContext]:
    """
    Create a Chromium browser and context configured for meeting bots.

    If `storage_state_path` points at an existing Playwright storage_state
    JSON (cookies + localStorage from a previously-authenticated session),
    it is loaded into the new context. This is how Zoho joins bypass the
    guest-page CAPTCHA: the operator logs in once on a laptop, saves the
    state, and ships it to the bot host. The bot then reuses that session
    so Zoho treats the join as an already-signed-in user.

    Returns (browser, context) tuple.
    """
    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        # Audio: route to PulseAudio virtual sink
        "--use-fake-ui-for-media-stream",       # auto-accept mic/camera prompts
        "--autoplay-policy=no-user-gesture-required",
        # Reduce detection
        "--disable-features=TranslateUI",
        "--disable-extensions",
    ]

    # When running inside Docker with PulseAudio, ensure audio goes to the virtual sink
    pulse_server = os.getenv("PULSE_SERVER", "")
    if pulse_server:
        browser_args.append(f"--alsa-output-device=pulse")

    browser = await playwright.chromium.launch(
        headless=headless,
        args=browser_args,
    )

    context_kwargs = {
        "viewport": {"width": 1280, "height": 720},
        "user_agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "permissions": ["microphone", "camera"],
        "ignore_https_errors": True,
    }

    if storage_state_path and os.path.exists(storage_state_path):
        context_kwargs["storage_state"] = storage_state_path
        logger.info("Loading browser storage_state from %s", storage_state_path)
    elif storage_state_path:
        logger.info(
            "storage_state_path=%s not found on disk — falling back to guest session",
            storage_state_path,
        )

    context = await browser.new_context(**context_kwargs)

    # Stealth: override navigator.webdriver
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    """)

    return browser, context
