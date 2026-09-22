# -*- coding: utf-8 -*-
"""Outbound messages: WhatsApp to the owner and the therapist, Telegram as a
backup channel.

A server cannot send a WhatsApp message just by knowing a number. It needs an
account with a provider, so this speaks to whichever one is configured:

    WA_PROVIDER=fonnte   WA_TOKEN=...              (Indonesian, simplest)
    WA_PROVIDER=wablas   WA_TOKEN=...  WA_API_URL=https://xxx.wablas.com
    WA_PROVIDER=meta     WA_TOKEN=...  WA_PHONE_ID=...   (Meta Cloud API)

With none configured, nothing is sent automatically and the admin screens fall
back to a prefilled wa.me link — one tap to send by hand. That is the honest
default: silent failure would be worse than a button.

Note on Meta: outside a 24-hour window since the person last messaged you,
Meta only delivers pre-approved templates. Fonnte and Wablas drive a real
WhatsApp session and have no such restriction, which is why they suit a small
spa better.
"""
import os
from functools import wraps
from urllib.parse import quote

import requests
from flask import current_app

TIMEOUT = 8


# ---------------------------------------------------------------- helpers

def digits(number: str) -> str:
    """62812... — strips spaces, dashes and a leading +."""
    return "".join(c for c in (number or "") if c.isdigit())


def whatsapp_link(number: str, text: str = "") -> str:
    """A chat link a human taps to send. Always available, no account needed."""
    return f"https://wa.me/{digits(number)}" + (f"?text={quote(text)}" if text else "")


def wa_configured() -> bool:
    return bool(os.getenv("WA_TOKEN") and os.getenv("WA_PROVIDER", "none") != "none")


# ---------------------------------------------------------------- sending

def never_raises(default=None):
    """Notifications are an extra, never a dependency.

    The website is the record of a booking. A guest has already been told it
    is confirmed before any of this runs, so nothing in here — not a dead
    gateway, not a misconfigured template, not a bug of ours — may escape and
    turn a saved booking into an error page.
    """
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:                           # noqa: BLE001
                try:
                    current_app.logger.exception(
                        "notification failed in %s: %s", fn.__name__, exc)
                except Exception:                              # noqa: BLE001
                    pass
                # Callers that read a result get one shaped the way they
                # expect, so a swallowed error cannot become an unpack error.
                return default(exc) if callable(default) else default
        return wrapper
    return decorate


def _send_whatsapp(number: str, text: str):
    """(ok, detail). Never raises — a failed message must not fail a booking."""
    provider = os.getenv("WA_PROVIDER", "none").lower()
    token = os.getenv("WA_TOKEN", "")
    to = digits(number)

    if not to:
        return False, "no phone number"
    if provider == "none" or not token:
        return False, "no WhatsApp provider configured"

    try:
        if provider == "fonnte":
            r = requests.post("https://api.fonnte.com/send",
                              headers={"Authorization": token},
                              data={"target": to, "message": text},
                              timeout=TIMEOUT)
        elif provider == "wablas":
            base = os.getenv("WA_API_URL", "https://console.wablas.com").rstrip("/")
            r = requests.post(f"{base}/api/send-message",
                              headers={"Authorization": token},
                              data={"phone": to, "message": text},
                              timeout=TIMEOUT)
        elif provider == "meta":
            phone_id = os.getenv("WA_PHONE_ID", "")
            if not phone_id:
                return False, "WA_PHONE_ID is not set"
            r = requests.post(
                f"https://graph.facebook.com/v20.0/{phone_id}/messages",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "to": to,
                      "type": "text", "text": {"body": text}},
                timeout=TIMEOUT)
        else:
            return False, f"unknown provider '{provider}'"

        ok = 200 <= r.status_code < 300
        return ok, f"{r.status_code} {r.text[:200]}"
    except Exception as exc:                                   # noqa: BLE001
        # Deliberately broad. A gateway can fail in ways requests does not
        # wrap — a proxy error, a TLS problem, a bad JSON body — and none
        # of them may reach the caller, who is in the middle of taking a
        # booking.
        return False, f"{type(exc).__name__}: {exc}"[:200]


def _send_whatsapp_template(number: str, template: str, params, lang_code):
    """Send an approved WhatsApp template. (ok, detail), never raises.

    Meta only accepts free text from a business inside the 24-hour window
    that opens when the customer messages first. A booking confirmation goes
    to someone who may never have messaged us, so it has to be a template
    that Meta approved in advance — this is that path. Providers that drive a
    linked handset (fonnte, wablas) have no template concept and fall back to
    the rendered text.
    """
    provider = os.getenv("WA_PROVIDER", "none").lower()
    token = os.getenv("WA_TOKEN", "")
    to = digits(number)

    if not to:
        return False, "no phone number"
    if provider != "meta":
        return False, f"provider '{provider}' does not send templates"
    if not token:
        return False, "no WhatsApp provider configured"
    phone_id = os.getenv("WA_PHONE_ID", "")
    if not phone_id:
        return False, "WA_PHONE_ID is not set"
    if not template:
        return False, "no template name configured"

    body = {"messaging_product": "whatsapp", "to": to, "type": "template",
            "template": {"name": template,
                         "language": {"code": lang_code},
                         "components": [{
                             "type": "body",
                             "parameters": [{"type": "text",
                                             "text": str(p)[:1024]}
                                            for p in params]}]}}
    try:
        r = requests.post(
            f"https://graph.facebook.com/v20.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json=body, timeout=TIMEOUT)
        return 200 <= r.status_code < 300, f"{r.status_code} {r.text[:200]}"
    except Exception as exc:                                   # noqa: BLE001
        # Deliberately broad. A gateway can fail in ways requests does not
        # wrap — a proxy error, a TLS problem, a bad JSON body — and none
        # of them may reach the caller, who is in the middle of taking a
        # booking.
        return False, f"{type(exc).__name__}: {exc}"[:200]


def _send_telegram(chat_id: str, text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        return False, "Telegram not configured"
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text},
                          timeout=TIMEOUT)
        return 200 <= r.status_code < 300, f"{r.status_code} {r.text[:200]}"
    except Exception as exc:                                   # noqa: BLE001
        # Deliberately broad. A gateway can fail in ways requests does not
        # wrap — a proxy error, a TLS problem, a bad JSON body — and none
        # of them may reach the caller, who is in the middle of taking a
        # booking.
        return False, f"{type(exc).__name__}: {exc}"[:200]


def _log(channel, purpose, recipient, name, body, ok, detail):
    """Recorded outside the caller's transaction: an alert that fails to log
    must not roll back the booking it was announcing."""
    from ..extensions import db
    from ..models.messaging import MessageLog
    try:
        db.session.add(MessageLog(
            channel=channel, purpose=purpose, recipient=str(recipient)[:60],
            recipient_name=(name or "")[:80], body=(body or "")[:4000],
            ok=ok, detail=(detail or "")[:300]))
        db.session.commit()
    except Exception:
        db.session.rollback()


# mail_service records its attempts in the same place, so one screen shows
# every message the site tried to send on any channel.
log_message = _log


def send_whatsapp(number, text, purpose="message", name=""):
    ok, detail = _send_whatsapp(number, text)
    _log("whatsapp", purpose, digits(number), name, text, ok, detail)
    return ok, detail


def telegram_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN"))


def send_telegram(chat_id, text, purpose="message", name=""):
    ok, detail = _send_telegram(str(chat_id or ""), text)
    _log("telegram", purpose, chat_id, name, text, ok, detail)
    return ok, detail


@never_raises()
def telegram_admin(text: str, purpose="message"):
    chat = os.getenv("ADMIN_TELEGRAM_CHAT", "")
    ok, detail = _send_telegram(chat, text)
    if chat:
        _log("telegram", purpose, chat, "admin", text, ok, detail)
    return ok, detail


def telegram_contacts():
    """Everyone who has messaged the bot recently, from getUpdates.

    This is how a therapist gets connected without anyone hunting for a
    numeric id: they send the bot any message, and their name and chat id
    appear here to be linked.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return [], "No bot token set"
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                         timeout=TIMEOUT)
        if r.status_code != 200:
            return [], f"{r.status_code} {r.text[:150]}"
        seen, out = set(), []
        for upd in r.json().get("result", []):
            msg = upd.get("message") or upd.get("edited_message") or {}
            chat = msg.get("chat") or {}
            cid = chat.get("id")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            name = " ".join(x for x in [chat.get("first_name"),
                                        chat.get("last_name")] if x) \
                or chat.get("username") or str(cid)
            out.append({"chat_id": str(cid), "name": name,
                        "username": chat.get("username") or ""})
        return out, None
    except requests.RequestException as exc:
        return [], str(exc)[:200]


@never_raises()
def notify_admin(text: str, purpose="message"):
    """Owner's WhatsApp first, Telegram as well when it is set up."""
    from ..models.site import SiteSetting
    try:
        cfg = SiteSetting.all_dict()
    except Exception:
        cfg = {}
    number = cfg.get("admin_whatsapp") or cfg.get("whatsapp") or \
        os.getenv("WHATSAPP_NUMBER", "")
    if number and wa_configured():
        send_whatsapp(number, text, purpose=purpose, name="admin")
    telegram_admin(text, purpose=purpose)


# ---------------------------------------------------------------- messages

def booking_text(b, site_url="", for_therapist=False) -> str:
    """The message body. Kept in one place so the automatic send and the
    one-tap link never say different things."""
    when = f"{b.starts_at:%a %d %b, %H:%M}"
    lines = ["💆 " + ("New treatment for you" if for_therapist
                      else f"New booking {b.public_code}"),
             f"{b.treatment_name} · {b.duration_min} min",
             f"When: {when}"]
    if b.guests and b.guests > 1:
        lines.append(f"Guests: {b.guests}")
    lines.append(f"Guest: {b.customer_name or '-'} · {b.customer_phone}")
    if b.area:
        lines.append(f"Area: {b.area.name}")
    if b.service_address:
        lines.append(f"Address: {b.service_address}")
    if b.note:
        lines.append(f"Note: {b.note}")
    if for_therapist:
        fee = b.fee_due
        if fee:
            lines.append(f"Your fee: Rp {fee:,}".replace(",", "."))
        lines.append("Please confirm you can take it.")
    else:
        lines.append(f"Total: Rp {b.total_idr:,}".replace(",", "."))
        lines.append(f"Payment: {b.payment_method}")
        if site_url:
            lines.append(f"{site_url}/admin/bookings")
    return "\n".join(lines)


def order_text(o, site_url="") -> str:
    lines = [f"🛒 New order {o.public_code}",
             f"Total: Rp {o.total_idr:,}".replace(",", "."),
             f"{o.customer_name or '-'} · {o.customer_phone}",
             f"Payment: {o.payment_method}"]
    for i in o.items:
        lines.append(f"  {i.qty} × {i.name}")
    if o.address:
        lines.append(f"Deliver to: {o.address}")
    if site_url:
        lines.append(f"{site_url}/admin/orders")
    return "\n".join(lines)


# ------------------------------------------------- what the customer receives

def _money(n):
    return "Rp " + f"{int(n or 0):,}".replace(",", ".")


def customer_booking_text(b, site_url="", event="confirmed") -> str:
    """The guest's own copy. It carries the manage link and nothing else —
    no therapist name, no staff number, no way to arrange anything off-site."""
    head = {"confirmed": "Booking Confirmed",
            "changed": "Booking Updated",
            "cancelled": "Booking Cancelled"}.get(event, "Booking")
    lines = [f"Taksu Nusa Spa — {head}",
             "",
             f"Booking: #{b.public_code}",
             f"Service: {b.treatment_name} {b.duration_min} min",
             f"Date: {b.starts_at:%d %B %Y}",
             f"Time: {b.starts_at:%H:%M}"]
    if b.service_address:
        lines.append(f"Address: {b.service_address}")
    elif b.area:
        lines.append(f"Area: {b.area.name}")
    lines.append(f"Total: {_money(b.total_idr)}")
    lines.append(f"Status: {b.status.title()}")
    if event != "cancelled" and site_url:
        lines += ["", "Manage / modify / cancel:",
                  f"{site_url}{b.manage_path()}"]
    return "\n".join(lines)


def customer_template_params(b, site_url=""):
    """The ordered {{1}}..{{7}} values for the approved Utility template.

    Meta rejects a parameter containing a newline or a run of spaces, so each
    one is a single tidy line.
    """
    where = b.service_address or (b.area.name if b.area else "-")
    return [b.public_code,
            f"{b.treatment_name} {b.duration_min} min",
            f"{b.starts_at:%d %B %Y}",
            f"{b.starts_at:%H:%M}",
            " ".join(where.split()),
            b.status.title(),
            f"{site_url}{b.manage_path()}"]


@never_raises(lambda exc: (False, False))
def notify_customer(b, site_url="", event="confirmed"):
    """Tell the guest, on WhatsApp and by e-mail. (whatsapp_ok, email_ok).

    Best-effort by design: the booking is already saved and shown on screen
    before this runs, so a gateway being down costs a notification, never a
    booking.
    """
    text = customer_booking_text(b, site_url, event)
    provider = os.getenv("WA_PROVIDER", "none").lower()
    wa_ok = False

    if b.customer_phone and wa_configured():
        if provider == "meta":
            tpl = os.getenv("WA_TEMPLATE_BOOKING", "").strip()
            lang_code = os.getenv("WA_TEMPLATE_LANG", "en").strip() or "en"
            if tpl:
                wa_ok, detail = _send_whatsapp_template(
                    b.customer_phone, tpl,
                    customer_template_params(b, site_url), lang_code)
                _log("whatsapp", f"customer_{event}", digits(b.customer_phone),
                     b.customer_name, text, wa_ok, f"template {tpl}: {detail}")
            else:
                _log("whatsapp", f"customer_{event}", digits(b.customer_phone),
                     b.customer_name, text, False,
                     "WA_TEMPLATE_BOOKING is not set — Meta needs an approved "
                     "template to message a customer who has not messaged first")
        else:
            # fonnte / wablas drive a linked handset and take plain text.
            wa_ok, _ = send_whatsapp(b.customer_phone, text,
                                     purpose=f"customer_{event}",
                                     name=b.customer_name)

    email_ok = False
    if b.customer_email:
        from . import mail_service
        subject = f"Taksu Nusa Spa — {event.title()} — #{b.public_code}"
        email_ok, _ = mail_service.send(b.customer_email, subject, text,
                                        purpose=f"customer_{event}",
                                        name=b.customer_name)
    return wa_ok, email_ok


@never_raises()
def notify_booking(booking, site_url=""):
    """Everything that happens after a booking is saved.

    Each channel is independent and none of them can fail the booking: the
    guest has already seen the confirmation on the website, which stays the
    record of the booking whatever the messaging gateways do.
    """
    text = booking_text(booking, site_url)
    notify_admin(text, purpose="new_booking")

    from . import mail_service
    if mail_service.admin_address():
        mail_service.send(mail_service.admin_address(),
                          f"New booking #{booking.public_code}", text,
                          purpose="new_booking", name="Admin")

    notify_customer(booking, site_url, event="confirmed")

    # If the booking already has a therapist, tell them straight away.
    if booking.therapist:
        notify_therapist(booking, site_url)


@never_raises()
def notify_order(order, site_url=""):
    notify_admin(order_text(order, site_url), purpose="new_order")


@never_raises(lambda exc: (False, f"{type(exc).__name__}: {exc}"[:200]))
def notify_therapist(booking, site_url=""):
    """(ok, detail). Tries WhatsApp, then Telegram, which is free.

    False with a reason when neither is available — the caller then shows the
    one-tap wa.me link instead of failing silently.
    """
    th = booking.therapist
    if not th:
        return False, "no therapist assigned"
    text = booking_text(booking, site_url, for_therapist=True)

    if th.phone and wa_configured():
        ok, detail = send_whatsapp(th.phone, text,
                                   purpose="therapist_assigned", name=th.name)
        if ok:
            return True, detail
        # Fall through: a paid gateway that is down should not stop the free
        # channel from getting the message there.

    if th.telegram_chat_id and telegram_configured():
        return send_telegram(th.telegram_chat_id, text,
                             purpose="therapist_assigned", name=th.name)

    if not th.phone and not th.telegram_chat_id:
        return False, f"{th.name} has no WhatsApp number or Telegram saved"
    if th.phone and not wa_configured():
        return False, ("no WhatsApp provider configured — connect Telegram for "
                       "free automatic messages")
    return False, "could not deliver on any channel"


def therapist_link(booking, site_url=""):
    """Prefilled wa.me link — works with no provider account at all."""
    th = booking.therapist
    if not th or not th.phone:
        return None
    return whatsapp_link(th.phone, booking_text(booking, site_url,
                                                for_therapist=True))
