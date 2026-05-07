"""Generate a Zoho storage_state.json by logging in interactively.

Run this on your laptop ONCE. It opens a real Chromium window pointed
at Zoho's login page; you log in (and solve the CAPTCHA if shown), then
press Enter in the terminal. The resulting JSON contains cookies +
localStorage that authenticate your session — keep it private (it's
equivalent to your Zoho password).

Usage:
    pip install playwright
    playwright install chromium
    python infra/scripts/generate-zoho-state.py [output_path]

Default output_path is ./zoho_state.json (current directory).

After it saves, ship the file to the bot host:

    scp zoho_state.json root@212.38.94.234:/root/zoho_state.json

Then re-run `bash infra/scripts/deploy-bot-vps.sh` so the container
picks up the new mount, OR just restart the bot:

    ssh root@212.38.94.234 'docker restart bot'
    (a restart alone is NOT enough — the mount is set at `docker run`
    time, so a fresh deploy is what wires the bind in. If you SCP'd
    the state AFTER the last deploy, you must redeploy once.)
"""

from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "zoho_state.json"
    print(f"Saving authenticated Zoho session to: {out}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://accounts.zoho.com/signin")

        print("=" * 64)
        print(" 1. Log into Zoho in the Chromium window that just opened.")
        print(" 2. Solve the CAPTCHA if it appears.")
        print(" 3. Wait until you see your Zoho dashboard / mail / etc.")
        print(" 4. Come back here and press Enter to save the session.")
        print("=" * 64)
        input()

        context.storage_state(path=out)
        print(f"\n[ok] Saved {out}")
        print(f"\nNext: scp {out} root@212.38.94.234:/root/zoho_state.json")
        print("Then:  bash infra/scripts/deploy-bot-vps.sh")
        browser.close()


if __name__ == "__main__":
    main()
