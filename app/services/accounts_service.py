# -*- coding: utf-8 -*-
"""What came in, what went out, and what is owed to whom.

Income is derived from bookings and orders rather than kept in a separate
ledger, so the numbers cannot drift from the bookings and orders screens.
Cancelled work never counts. Only expenses and payouts are recorded directly.
"""
from calendar import monthrange
from datetime import date, datetime, timedelta

from sqlalchemy import func

from ..extensions import db
from ..models.finance import Expense, Payout
from ..models.shop import Order
from ..models.spa import Booking, Therapist

# Bookings that represent work actually done or committed to.
EARNING_BOOKINGS = ["confirmed", "completed"]
# Orders that represent a real sale.
EARNING_ORDERS = ["confirmed", "packed", "delivering", "completed"]


def period_bounds(name: str, today=None):
    """(start, end, label) for the period picker. End is inclusive."""
    today = today or date.today()
    if name == "today":
        return today, today, "Today"
    if name == "week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6), "This week"
    if name == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6), "Last week"
    if name == "last_month":
        first_this = today.replace(day=1)
        end = first_this - timedelta(days=1)
        return end.replace(day=1), end, end.strftime("%B %Y")
    if name == "year":
        return date(today.year, 1, 1), date(today.year, 12, 31), str(today.year)
    # default: this month
    start = today.replace(day=1)
    return start, today.replace(day=monthrange(today.year, today.month)[1]), \
        today.strftime("%B %Y")


def _span(start: date, end: date):
    """Datetime bounds for a date range, end inclusive."""
    return (datetime.combine(start, datetime.min.time()),
            datetime.combine(end + timedelta(days=1), datetime.min.time()))


def treatment_income(start: date, end: date) -> int:
    """Bookings are counted on the day the treatment happens, not the day it
    was taken — that is the day the money is earned."""
    lo, hi = _span(start, end)
    return int(db.session.query(func.coalesce(func.sum(Booking.total_idr), 0))
               .filter(Booking.status.in_(EARNING_BOOKINGS),
                       Booking.starts_at >= lo, Booking.starts_at < hi)
               .scalar() or 0)


def product_income(start: date, end: date) -> int:
    lo, hi = _span(start, end)
    return int(db.session.query(func.coalesce(func.sum(Order.total_idr), 0))
               .filter(Order.status.in_(EARNING_ORDERS),
                       Order.created_at >= lo, Order.created_at < hi)
               .scalar() or 0)


def therapist_cost(start: date, end: date) -> int:
    """Commission earned in the period, paid or not."""
    lo, hi = _span(start, end)
    rows = (Booking.query.filter(Booking.status.in_(EARNING_BOOKINGS),
                                 Booking.therapist_id.isnot(None),
                                 Booking.starts_at >= lo,
                                 Booking.starts_at < hi).all())
    return sum(b.fee_due for b in rows)


def expenses_total(start: date, end: date) -> int:
    return int(db.session.query(func.coalesce(func.sum(Expense.amount_idr), 0))
               .filter(Expense.day >= start, Expense.day <= end)
               .scalar() or 0)


def expenses_by_category(start: date, end: date):
    rows = (db.session.query(Expense.category,
                             func.coalesce(func.sum(Expense.amount_idr), 0))
            .filter(Expense.day >= start, Expense.day <= end)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount_idr).desc()).all())
    return [(c, int(v)) for c, v in rows]


def summary(start: date, end: date) -> dict:
    treatments = treatment_income(start, end)
    products = product_income(start, end)
    therapists = therapist_cost(start, end)
    other = expenses_total(start, end)
    income = treatments + products
    costs = therapists + other
    return {
        "start": start, "end": end,
        "treatment_income": treatments,
        "product_income": products,
        "income": income,
        "therapist_cost": therapists,
        "expenses": other,
        "costs": costs,
        "net": income - costs,
        "by_category": expenses_by_category(start, end),
        "bookings": booking_count(start, end),
        "orders": order_count(start, end),
    }


def booking_count(start: date, end: date) -> int:
    lo, hi = _span(start, end)
    return Booking.query.filter(Booking.status.in_(EARNING_BOOKINGS),
                                Booking.starts_at >= lo,
                                Booking.starts_at < hi).count()


def order_count(start: date, end: date) -> int:
    lo, hi = _span(start, end)
    return Order.query.filter(Order.status.in_(EARNING_ORDERS),
                              Order.created_at >= lo,
                              Order.created_at < hi).count()


def daily_income(start: date, end: date):
    """[(day, treatments, products)] — enough for a simple bar row."""
    out = []
    day = start
    while day <= end:
        out.append((day, treatment_income(day, day), product_income(day, day)))
        day += timedelta(days=1)
    return out


# ---------------------------------------------------------------- payouts

def unpaid_by_therapist():
    """[{therapist, bookings, amount}] for work done but not yet paid out.

    Only past treatments count: a booking next Friday is not money the
    therapist is owed today.
    """
    now = datetime.now()
    rows = (Booking.query
            .filter(Booking.status.in_(EARNING_BOOKINGS),
                    Booking.therapist_id.isnot(None),
                    Booking.payout_id.is_(None),
                    Booking.ends_at <= now)
            .order_by(Booking.starts_at).all())
    grouped = {}
    for b in rows:
        entry = grouped.setdefault(b.therapist_id,
                                   {"therapist": b.therapist, "bookings": [],
                                    "amount": 0})
        entry["bookings"].append(b)
        entry["amount"] += b.fee_due
    return sorted(grouped.values(),
                  key=lambda e: e["therapist"].sort_order if e["therapist"] else 0)


def pay_therapist(therapist: Therapist, paid_on: date, method="cash", note=""):
    """Settle every unpaid booking for this therapist. Returns the payout, or
    None when there is nothing owed."""
    now = datetime.now()
    rows = (Booking.query
            .filter(Booking.status.in_(EARNING_BOOKINGS),
                    Booking.therapist_id == therapist.id,
                    Booking.payout_id.is_(None),
                    Booking.ends_at <= now).all())
    if not rows:
        return None

    payout = Payout(therapist_id=therapist.id, paid_on=paid_on,
                    method=method, note=(note or "")[:200],
                    amount_idr=0, bookings_count=0)
    db.session.add(payout)
    db.session.flush()

    total = 0
    for b in rows:
        fee = b.fee_due
        b.therapist_fee_idr = fee      # freeze it, so a later rate change
        b.payout_id = payout.id        # cannot rewrite what was paid
        total += fee
    payout.amount_idr = total
    payout.bookings_count = len(rows)
    db.session.commit()
    return payout
