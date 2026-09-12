"""Indonesian rupiah formatting. Prices are whole rupiah — no cents in
day-to-day Bali pricing, so 150000 renders as 'Rp 150.000'."""
from decimal import Decimal, InvalidOperation


def to_int(value) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(Decimal(str(value).replace(" ", "").replace(".", "")
                           .replace(",", "")))
    except (InvalidOperation, ValueError):
        return 0


def rp(value) -> str:
    """150000 -> 'Rp 150.000'"""
    try:
        n = int(round(float(value or 0)))
    except (TypeError, ValueError):
        n = 0
    return "Rp " + f"{n:,}".replace(",", ".")
