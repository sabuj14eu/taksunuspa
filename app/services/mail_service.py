# -*- coding: utf-8 -*-
"""E-mail, sent best-effort.

Configured entirely by environment, so a site with no SMTP details simply
does not send and says so in the message log. Nothing here may raise: a
booking is never lost because a mail server was unreachable.

    MAIL_HOST=smtp.example.com
    MAIL_PORT=587
    MAIL_USER=bookings@taksunusaspa.com
    MAIL_PASSWORD=...
    MAIL_FROM="Taksu Nusa Spa <bookings@taksunusaspa.com>"
    MAIL_SECURITY=starttls        # starttls | ssl | none
    ADMIN_EMAIL=owner@example.com
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

TIMEOUT = 15


def configured() -> bool:
    return bool(os.getenv("MAIL_HOST") and _sender())


def admin_address() -> str:
    return (os.getenv("ADMIN_EMAIL") or "").strip()


def _sender() -> str:
    raw = (os.getenv("MAIL_FROM") or os.getenv("MAIL_USER") or "").strip()
    if not raw:
        return ""
    name, addr = parseaddr(raw)
    return formataddr((name or "Taksu Nusa Spa", addr)) if addr else ""


def _deliver(to: str, subject: str, body: str):
    """(ok, detail). Never raises."""
    if not to:
        return False, "no e-mail address"
    if not configured():
        return False, "no mail server configured"

    msg = EmailMessage()
    msg["From"] = _sender()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    host = os.getenv("MAIL_HOST")
    port = int(os.getenv("MAIL_PORT") or 587)
    user = os.getenv("MAIL_USER") or ""
    password = os.getenv("MAIL_PASSWORD") or ""
    security = (os.getenv("MAIL_SECURITY") or "starttls").lower()

    try:
        if security == "ssl":
            server = smtplib.SMTP_SSL(host, port, timeout=TIMEOUT,
                                      context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(host, port, timeout=TIMEOUT)
        with server:
            if security == "starttls":
                server.starttls(context=ssl.create_default_context())
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True, "sent"
    except Exception as exc:                                   # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"[:200]


def send(to: str, subject: str, body: str, purpose="message", name=""):
    """Deliver and record the attempt, successful or not."""
    ok, detail = _deliver((to or "").strip(), subject, body)
    from .notify_service import log_message
    log_message("email", purpose, to, name, f"{subject}\n\n{body}", ok, detail)
    return ok, detail
