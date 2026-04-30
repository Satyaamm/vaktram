"""Transactional email via Resend.

No-ops in dev (just logs the message). When RESEND_API_KEY is set in
staging/prod, sends real email.
"""

from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


async def send_email(
    *,
    to: str | list[str],
    subject: str,
    html: str,
    text: str | None = None,
    from_email: str | None = None,
) -> bool:
    """Send a transactional email. Returns True on success, False otherwise."""
    sender = from_email or _settings.resend_from_email
    recipients = [to] if isinstance(to, str) else to
    if not _settings.resend_api_key:
        logger.info("EMAIL[dev] %s -> %s: %s", sender, recipients, subject)
        return True
    try:
        import resend

        resend.api_key = _settings.resend_api_key
        resend.Emails.send(
            {
                "from": sender,
                "to": recipients,
                "subject": subject,
                "html": html,
                "text": text or _strip_tags(html),
            }
        )
        return True
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to send email to %s: %s", recipients, e)
        return False


def _strip_tags(html: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", html)
