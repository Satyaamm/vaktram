"""Transactional email templates.

We deliberately keep these as Python string templates (no Jinja) — the
transactional set is small (welcome, summary-ready, tracker-hit, password
reset, invitation), the variables are typed, and rendering must never fail.
For richer marketing email use the lifecycle ESP (Loops / Customer.io).

Each template returns ``(subject, html, text)`` so callers can drop it
straight into ``email_service.send_email()``.
"""

from __future__ import annotations

import html as _html
import os

BRAND = os.getenv("VAKTRAM_BRAND_NAME", "Vaktram")
APP_URL = os.getenv("FRONTEND_BASE_URL", "https://app.vaktram.com")
PRIMARY = "#0f766e"  # teal-700, matches the dashboard


def _frame(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html><body style="margin:0;background:#f8fafc;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#0f172a">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
    <tr><td align="center" style="padding:32px 16px">
      <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0"
             style="max-width:560px;background:#ffffff;border-radius:12px;
                    box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden">
        <tr><td style="padding:24px 32px;background:{PRIMARY};color:#ffffff;
                       font-size:18px;font-weight:700">{_html.escape(BRAND)}</td></tr>
        <tr><td style="padding:32px">
          <h1 style="margin:0 0 16px;font-size:22px;font-weight:600">{_html.escape(title)}</h1>
          {body_html}
        </td></tr>
        <tr><td style="padding:16px 32px;background:#f1f5f9;font-size:12px;color:#64748b">
          You're receiving this because of activity on your {_html.escape(BRAND)} account.
          <br/><a href="{APP_URL}/settings" style="color:{PRIMARY}">Manage notifications</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def _button(text: str, href: str) -> str:
    return (
        f'<a href="{_html.escape(href, quote=True)}" '
        f'style="display:inline-block;background:{PRIMARY};color:#ffffff;'
        f'text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600">'
        f"{_html.escape(text)}</a>"
    )


# ── Templates ────────────────────────────────────────────────────────

def welcome(*, full_name: str | None) -> tuple[str, str, str]:
    name = full_name.split(" ")[0] if full_name else "there"
    subject = f"Welcome to {BRAND}"
    body = f"""
        <p>Hi {_html.escape(name)},</p>
        <p>Welcome to {BRAND}. You're 3 steps away from your first AI-summarized meeting:</p>
        <ol style="line-height:1.8">
          <li><a href="{APP_URL}/settings" style="color:{PRIMARY}">Connect your calendar</a> — we'll auto-join your scheduled meetings.</li>
          <li><a href="{APP_URL}/settings/ai-config" style="color:{PRIMARY}">Plug in your LLM key</a> — pick OpenAI, Anthropic, Gemini, Groq, or Bedrock.</li>
          <li>Hold a meeting. We'll send you the transcript + summary the moment it's ready.</li>
        </ol>
        <p style="margin-top:24px">{_button("Open the dashboard", APP_URL + "/dashboard")}</p>
    """
    return subject, _frame(f"Welcome, {name}", body), (
        f"Welcome to {BRAND}. Get started: {APP_URL}/dashboard"
    )


def summary_ready(*, meeting_title: str, meeting_id: str) -> tuple[str, str, str]:
    subject = f'Your "{meeting_title}" summary is ready'
    body = f"""
        <p>Your meeting summary, action items, and full transcript are ready.</p>
        <p style="margin-top:16px">{_button("View summary", f"{APP_URL}/meetings/{meeting_id}")}</p>
    """
    return subject, _frame("Summary ready", body), (
        f'"{meeting_title}" is ready: {APP_URL}/meetings/{meeting_id}'
    )


def tracker_hit(*, tracker_name: str, meeting_title: str, hits: list[str], meeting_id: str) -> tuple[str, str, str]:
    subject = f'"{tracker_name}" mentioned in {meeting_title}'
    items = "".join(f"<li>{_html.escape(h)[:240]}</li>" for h in hits[:5])
    body = f"""
        <p>Your <b>{_html.escape(tracker_name)}</b> tracker matched in
        <b>{_html.escape(meeting_title)}</b>:</p>
        <ul style="line-height:1.6">{items}</ul>
        <p style="margin-top:16px">{_button("Open meeting", f"{APP_URL}/meetings/{meeting_id}")}</p>
    """
    return subject, _frame(f"{tracker_name} mentioned", body), (
        f"{tracker_name} mentioned in {meeting_title}: {APP_URL}/meetings/{meeting_id}"
    )


def email_verification(*, full_name: str | None, verify_url: str) -> tuple[str, str, str]:
    name = full_name.split(" ")[0] if full_name else "there"
    subject = f"Verify your {BRAND} email"
    body = f"""
        <p>Hi {_html.escape(name)},</p>
        <p>Confirm your email so you can start using {BRAND}. The link expires in 24 hours.</p>
        <p style="margin-top:16px">{_button("Verify email", verify_url)}</p>
        <p style="font-size:12px;color:#64748b;margin-top:24px">
          If you didn't sign up for {BRAND}, you can ignore this — no account will be created.
        </p>
    """
    return subject, _frame("Confirm your email", body), (
        f"Verify your {BRAND} email: {verify_url}"
    )


def password_reset(*, reset_url: str) -> tuple[str, str, str]:
    subject = f"Reset your {BRAND} password"
    body = f"""
        <p>Tap the button below to choose a new password. The link expires in 30 minutes.</p>
        <p style="margin-top:16px">{_button("Reset password", reset_url)}</p>
        <p style="font-size:12px;color:#64748b;margin-top:24px">
          If you didn't request this, you can safely ignore the email.
        </p>
    """
    return subject, _frame("Reset your password", body), (
        f"Reset your {BRAND} password: {reset_url} (expires in 30 minutes)"
    )


def org_invitation(*, inviter_name: str, organization_name: str, accept_url: str) -> tuple[str, str, str]:
    subject = f"{inviter_name} invited you to {organization_name} on {BRAND}"
    body = f"""
        <p><b>{_html.escape(inviter_name)}</b> invited you to join
        <b>{_html.escape(organization_name)}</b> on {BRAND}.</p>
        <p style="margin-top:16px">{_button("Accept invitation", accept_url)}</p>
    """
    return subject, _frame("You're invited", body), (
        f"{inviter_name} invited you to {organization_name}: {accept_url}"
    )
