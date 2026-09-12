# -*- coding: utf-8 -*-
"""Treatment booking engine.

Carried over from the LokalnyDowoz spa vertical: opening hours give a slot
grid, a therapist without an overlapping booking claims the slot, and the
same overlap check runs again at write time so two people clicking the same
slot cannot both get it.
"""
from datetime import date, datetime, timedelta

from ..extensions import db
from ..models.spa import (OpeningHour, HolidayHour, Therapist, Booking,
                          BOOKING_ACTIVE)
from . import pricing_service

LEAD_HOURS = 2          # earliest bookable slot from now


def hhmm(minutes) -> str:
    m = int(minutes or 0)
    return f"{m // 60:02d}:{m % 60:02d}"


def hours_for_day(day: date):
    """(open_min, close_min) or None when closed."""
    hol = HolidayHour.query.filter_by(day=day).first()
    if hol:
        if hol.is_closed or hol.open_min is None:
            return None
        return hol.open_min, hol.close_min
    h = OpeningHour.query.filter_by(weekday=day.weekday()).first()
    if not h or h.is_closed or h.open_min is None:
        return None
    return h.open_min, h.close_min


def _free_therapist(starts_at, ends_at, therapist_id=None):
    """The first therapist with no overlapping active booking. With no
    therapist rows at all the spa books as one room, returning "venue"."""
    if therapist_id:
        pool = [db.session.get(Therapist, therapist_id)]
    else:
        pool = (Therapist.query.filter_by(is_active=True)
                .order_by(Therapist.sort_order, Therapist.id).all())
    pool = [t for t in pool if t and t.is_active]

    if not pool:
        clash = (Booking.query
                 .filter(Booking.therapist_id.is_(None),
                         Booking.status.in_(BOOKING_ACTIVE),
                         Booking.starts_at < ends_at,
                         Booking.ends_at > starts_at).first())
        return None if clash else "venue"

    for t in pool:
        clash = (Booking.query
                 .filter(Booking.therapist_id == t.id,
                         Booking.status.in_(BOOKING_ACTIVE),
                         Booking.starts_at < ends_at,
                         Booking.ends_at > starts_at).first())
        if not clash:
            return t
    return None


def slots_for(treatment, day: date, therapist_id=None, step_min=30):
    win = hours_for_day(day)
    if not win or not treatment:
        return []
    step = max(15, step_min)
    cutoff = datetime.now() + timedelta(hours=LEAD_HOURS)
    out = []
    t = win[0]
    while t + treatment.duration_min <= win[1]:
        starts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=t)
        if starts >= cutoff:
            ends = starts + timedelta(minutes=treatment.duration_min)
            if _free_therapist(starts, ends, therapist_id):
                out.append({"time_min": t, "label": hhmm(t)})
        t += step
    return out


def book(treatment, day: date, time_min: int, *, name, phone, email="", note="",
         guests=1, therapist_id=None, lang="en", via="web",
         payment_method="pay_at_spa"):
    """(booking, error_key). error_key is an i18n key, not a message."""
    win = hours_for_day(day)
    if not win or time_min < win[0] or time_min + treatment.duration_min > win[1]:
        return None, "slot_gone"

    starts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=time_min)
    ends = starts + timedelta(minutes=treatment.duration_min)
    if starts < datetime.now():
        return None, "slot_gone"

    picked = _free_therapist(starts, ends, therapist_id)
    if not picked:
        return None, "slot_gone"

    # Price the booking through the same engine the menu used, so the
    # customer is charged the discount they were shown.
    p = pricing_service.price_treatment(treatment)
    guests = max(1, int(guests or 1))

    b = Booking(
        treatment_id=treatment.id,
        therapist_id=None if picked == "venue" else picked.id,
        customer_name=(name or "")[:80], customer_phone=phone[:30],
        customer_email=(email or "")[:120],
        starts_at=starts, ends_at=ends, guests=guests,
        treatment_name=treatment.name_en[:160],
        base_price_idr=p["base"] * guests,
        discount_idr=p["off"] * guests,
        total_idr=p["final"] * guests,
        discount_label=(p["label"] or "")[:80] or None,
        payment_method=payment_method,
        note=(note or "")[:400], lang=lang, created_via=via)
    db.session.add(b)
    db.session.commit()
    return b, None


def upcoming(limit=50):
    return (Booking.query.filter(Booking.status.in_(BOOKING_ACTIVE),
                                 Booking.starts_at >= datetime.now())
            .order_by(Booking.starts_at).limit(limit).all())
