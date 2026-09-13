"""Indonesian rupiah formatting. Prices are whole rupiah — no cents in
day-to-day Bali pricing, so 150000 renders as 'Rp 150.000'."""
import re
from decimal import Decimal, InvalidOperation

_NOT_DIGITS = re.compile(r"[^\d-]")


def to_int(value) -> int:
    """Whatever a person types for an amount, as whole rupiah.

    Everything that is not a digit is dropped, so the thousands dots and
    commas people copy from the site come through, and so does the "Rp" they
    copy with them — that used to fall through to 0 and quietly price a jar of
    honey at nothing.
    """
    if value is None or value == "":
        return 0
    try:
        cleaned = _NOT_DIGITS.sub("", str(value))
        cleaned = "-" + cleaned.replace("-", "") if cleaned.startswith("-") \
            else cleaned.replace("-", "")
        return int(Decimal(cleaned)) if cleaned not in ("", "-") else 0
    except (InvalidOperation, ValueError):
        return 0


def parses_as_amount(value) -> bool:
    """True when the text actually contains a number. Lets a save warn about
    'one hundred thousand' rather than storing it as free."""
    return bool(re.search(r"\d", str(value or "")))


def rp(value) -> str:
    """150000 -> 'Rp 150.000'"""
    try:
        n = int(round(float(value or 0)))
    except (TypeError, ValueError):
        n = 0
    return "Rp " + f"{n:,}".replace(",", ".")
