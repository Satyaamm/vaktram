"""
Playwright browser setup helper.
Configures Chromium with the correct flags for headless meeting join,
PulseAudio audio routing, and fake media streams.
"""

import os
from typing import Tuple

from playwright.async_api import Browser, BrowserContext, Playwright


async def create_browser_context(
    playwright: Playwright,
    headless: bool = True,
) -> Tuple[Browser, BrowserContext]:
    """
    Create a Chromium browser and context configured for meeting bots.

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

    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        permissions=["microphone", "camera"],
        ignore_https_errors=True,
    )

    # Stealth: override navigator.webdriver
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    """)

    return browser, context
