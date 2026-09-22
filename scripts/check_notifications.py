#!/usr/bin/env python3
"""Why did that booking not message anyone?

Prints what is switched on, what the last bookings actually tried to send, and
what to put in .env to fix it. Optionally sends a real test message.

    python -m scripts.check_notifications
    python -m scripts.check_notifications --send 6281236729448
    python -m scripts.check_notifications --send-email you@example.com
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.models.messaging import MessageLog  # noqa: E402
from app.models.spa import Booking  # noqa: E402
from app.services import mail_service, notify_service  # noqa: E402

HINTS = {
    "whatsapp": [
        "WA_PROVIDER=meta        # or fonnte / wablas while Meta is pending",
        "WA_TOKEN=...            # from the provider",
        "WA_PHONE_ID=...         # Meta only",
        "WA_TEMPLATE_BOOKING=... # Meta only: your approved Utility template",
    ],
    "email": [
        "MAIL_HOST=smtp.gmail.com",
        "MAIL_PORT=587",
        "MAIL_USER=you@gmail.com",
        "MAIL_PASSWORD=...       # a Gmail app password, not your login",
        "MAIL_FROM=Taksu Nusa Spa <you@gmail.com>",
        "ADMIN_EMAIL=you@gmail.com   # where your own copy goes",
    ],
    "telegram": [
        "TELEGRAM_BOT_TOKEN=...  # free, from @BotFather in Telegram",
        "ADMIN_TELEGRAM_CHAT=... # your own chat id",
    ],
}


def run(send_to=None, send_email=None):
    app = create_app()
    with app.app_context():
        status = notify_service.notification_status()

        print("\n=== What is switched on ===")
        for name, (on, why) in status.items():
            print(f"  {'✅' if on else '❌'} {name:9} {why}")

        off = [n for n, (on, _w) in status.items() if not on]
        if off:
            print("\n=== Put this in .env on the server, then "
                  "`docker compose up -d` ===")
            for name in off:
                print(f"\n  # {name}")
                for line in HINTS[name]:
                    print(f"  {line}")

        print("\n=== The last 10 messages the site tried to send ===")
        rows = MessageLog.query.order_by(MessageLog.id.desc()).limit(10).all()
        if not rows:
            print("  Nothing at all. Either no booking has been taken since "
                  "this version was deployed, or the deploy did not happen.")
        for m in rows:
            mark = "✅" if m.ok else "❌"
            when = m.created_at.strftime("%d %b %H:%M") if m.created_at else "?"
            print(f"  {mark} {when}  {m.channel:9} {m.purpose:20} "
                  f"→ {m.recipient or '-'}")
            if not m.ok and m.detail:
                print(f"       {m.detail[:100]}")

        print("\n=== The last 5 bookings ===")
        for b in Booking.query.order_by(Booking.id.desc()).limit(5).all():
            print(f"  #{b.public_code}  {b.starts_at:%d %b %H:%M}  "
                  f"{b.treatment_name}  {b.customer_name or '-'}  "
                  f"{b.customer_phone}  {b.customer_email or 'no e-mail'}")

        if send_to:
            print(f"\n=== Sending a test WhatsApp to {send_to} ===")
            ok, detail = notify_service.send_whatsapp(
                send_to, "Test from Taksu Nusa Spa. If you can read this, "
                         "WhatsApp notifications are working.",
                purpose="test")
            print(f"  {'✅ sent' if ok else '❌ not sent'} — {detail}")

        if send_email:
            print(f"\n=== Sending a test e-mail to {send_email} ===")
            ok, detail = mail_service.send(
                send_email, "Test from Taksu Nusa Spa",
                "If you can read this, e-mail notifications are working.",
                purpose="test")
            print(f"  {'✅ sent' if ok else '❌ not sent'} — {detail}")

        print()


if __name__ == "__main__":
    args = sys.argv[1:]

    def after(flag):
        return args[args.index(flag) + 1] if flag in args and \
            len(args) > args.index(flag) + 1 else None

    run(send_to=after("--send"), send_email=after("--send-email"))
