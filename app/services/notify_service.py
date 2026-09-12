# -*- coding: utf-8 -*-
"""Outbound alerts.

Telegram is the fast path for "a booking just came in"; the WhatsApp helper
builds a prefilled chat link, which is how most Bali customers actually want
to finish an order.
"""
import os
from urllib.parse import quote

import requests


def _send(chat_id: str, text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text}, timeout=4)
    except Exception:
        pass


def telegram_admin(text: str):
    _send(os.getenv("ADMIN_TELEGRAM_CHAT", ""), text)


def whatsapp_link(number: str, text: str = "") -> str:
    digits = "".join(c for c in (number or "") if c.isdigit())
    return f"https://wa.me/{digits}" + (f"?text={quote(text)}" if text else "")


def notify_order(order, site_url=""):
    lines = [f"🛒 New order {order.public_code} — Rp {order.total_idr:,}".replace(",", "."),
             f"{order.customer_name or '-'} · {order.customer_phone}",
             f"Payment: {order.payment_method}"]
    if order.address:
        lines.append(f"Deliver to: {order.address}")
    if site_url:
        lines.append(f"{site_url}/admin/orders")
    telegram_admin("\n".join(lines))


def notify_booking(booking, site_url=""):
    lines = [f"💆 New booking {booking.public_code}",
             f"{booking.treatment_name} — {booking.starts_at:%d %b %H:%M}",
             f"{booking.customer_name or '-'} · {booking.customer_phone}"]
    if site_url:
        lines.append(f"{site_url}/admin/bookings")
    telegram_admin("\n".join(lines))
