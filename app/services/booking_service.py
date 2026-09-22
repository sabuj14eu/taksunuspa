# -*- coding: utf-8 -*-
"""Booking engine for a travelling spa.

Carried over from the LokalnyDowoz spa vertical: service hours give a slot
grid, a therapist without an overlapping booking claims the slot, and the
same overlap check runs again at write time so two guests clicking the same
slot cannot both get it.

Adapted for a home spa — the guest picks a duration, gives the address the
therapist should come to, and the area may add a travel fee.
"""
from datetime import date, datetime, timedelta

from ..extensions import db
from ..models.spa import (BOOKING_ACTIVE, Booking, HolidayHour, OpeningHour,
                          ServiceArea, Therapist)
from . import pricing_service

LEAD_HOURS = 2          # earliest bookable slot from now
TRAVEL_BUFFER_MIN = 30  # time between two bookings for the same therapist


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


def _free_therapist(starts_at, ends_at, therapist_id=None, exclude_id=None):
    """The first therapist with no overlapping booking. Because they travel
    between guests, a buffer is added either side of each existing booking.
    With no therapist rows at all the spa books as one resource.

    exclude_id leaves one booking out of the clash check: when a guest
    moves their own appointment it must not be found blocking itself.
    """
    buffer = timedelta(minutes=TRAVEL_BUFFER_MIN)
    window_start = starts_at - buffer
    window_end = ends_at + buffer

    def clashes(q):
        if exclude_id:
            q = q.filter(Booking.id != exclude_id)
        return q.first()

    if therapist_id:
        pool = [db.session.get(Therapist, therapist_id)]
    else:
        pool = (Therapist.query.filter_by(is_active=True)
                .order_by(Therapist.sort_order, Therapist.id).all())
    pool = [t for t in pool if t and t.is_active]

    if not pool:
        clash = clashes(Booking.query
                        .filter(Booking.therapist_id.is_(None),
                                Booking.status.in_(BOOKING_ACTIVE),
                                Booking.starts_at < window_end,
                                Booking.ends_at > window_start))
        return None if clash else "venue"

    for t in pool:
        clash = clashes(Booking.query
                        .filter(Booking.therapist_id == t.id,
                                Booking.status.in_(BOOKING_ACTIVE),
                                Booking.starts_at < window_end,
                                Booking.ends_at > window_start))
        if not clash:
            return t
    return None


def duration_of(treatment, option=None) -> int:
    if option is not None:
        return option.duration_min
    cheapest = treatment.cheapest_option
    return cheapest.duration_min if cheapest else treatment.duration_min


def slots_for(treatment, day: date, therapist_id=None, option=None,
              step_min=30, exclude_id=None):
    win = hours_for_day(day)
    if not win or not treatment:
        return []
    minutes = duration_of(treatment, option)
    step = max(15, step_min)
    cutoff = datetime.now() + timedelta(hours=LEAD_HOURS)
    out = []
    t = win[0]
    while t + minutes <= win[1]:
        starts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=t)
        if starts >= cutoff:
            ends = starts + timedelta(minutes=minutes)
            if _free_therapist(starts, ends, therapist_id, exclude_id):
                out.append({"time_min": t, "label": hhmm(t)})
        t += step
    return out


def next_available_day(treatment, from_day=None, therapist_id=None,
                       option=None, step_min=30, days=30, exclude_id=None):
    """The first day that actually has a free slot, or None.

    Today is usually not it: the last treatment has to finish by closing time
    and there is a two-hour lead, so from late afternoon today is already
    full. Opening the booking form on a day with nothing free reads as "no
    availability" rather than "look at tomorrow".
    """
    start = from_day or date.today()
    for i in range(days):
        d = start + timedelta(days=i)
        if slots_for(treatment, d, therapist_id, option, step_min, exclude_id):
            return d
    return None


def book(treatment, day: date, time_min: int, *, name, phone, option=None,
         email="", note="", guests=1, therapist_id=None, area_id=None,
         service_address="", lang="en", via="web", payment_method="cash",
         force=False):
    """(booking, error_key). error_key is an i18n key, not a message.

    `force` is for staff taking a booking by phone: it skips the opening
    hours, lead time and double-booking checks, because the person on the
    phone may be arranging something the calendar cannot know about. It is
    never set from the public form.
    """
    minutes = duration_of(treatment, option)
    starts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=time_min)
    ends = starts + timedelta(minutes=minutes)

    if force:
        picked = (db.session.get(Therapist, therapist_id) if therapist_id
                  else "venue")
        if picked is None:
            return None, "slot_gone"
    else:
        win = hours_for_day(day)
        if not win or time_min < win[0] or time_min + minutes > win[1]:
            return None, "slot_gone"
        if starts < datetime.now():
            return None, "slot_gone"
        picked = _free_therapist(starts, ends, therapist_id)
        if not picked:
            return None, "slot_gone"

    # Priced through the same engine the menu used, so the guest is charged
    # the discount they were shown.
    priced = option if option is not None else treatment
    p = pricing_service.price_of("treatment", priced)

    guests = max(1, int(guests or 1))
    # A per-person treatment (couple massage) multiplies by heads; everything
    # else is one price for the session however many people are in the room.
    units = guests if treatment.per_person else 1

    area = db.session.get(ServiceArea, int(area_id)) if area_id else None
    travel = (area.travel_fee_idr or 0) if area else 0

    b = Booking(
        treatment_id=treatment.id,
        option_id=option.id if option is not None else None,
        therapist_id=None if picked == "venue" else picked.id,
        area_id=area.id if area else None,
        customer_name=(name or "")[:80], customer_phone=phone[:30],
        customer_email=(email or "")[:120],
        service_address=(service_address or "")[:400],
        starts_at=starts, ends_at=ends, guests=guests,
        treatment_name=treatment.name_en[:160], duration_min=minutes,
        base_price_idr=p["base"] * units,
        discount_idr=p["off"] * units,
        travel_fee_idr=travel,
        total_idr=p["final"] * units + travel,
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


# ------------------------------------------------- changes made by the guest

def _reprice(b, treatment, option):
    """Re-run the same pricing the menu shows, for the new selection."""
    priced = option if option is not None else treatment
    p = pricing_service.price_of("treatment", priced)
    units = max(1, b.guests or 1) if treatment.per_person else 1
    travel = b.travel_fee_idr or 0
    b.base_price_idr = p["base"] * units
    b.discount_idr = p["off"] * units
    b.total_idr = p["final"] * units + travel
    b.discount_label = (p["label"] or "")[:80] or None


def amend(b, *, treatment=None, option=None, day=None, time_min=None,
          service_address=None, area_id=None, note=None, guests=None,
          by="customer"):
    """Change a booking the guest already holds. (booking, error_key).

    Everything a guest is allowed to change goes through here so the rules
    live in one place: the slot is re-checked against the calendar, the price
    is recalculated from the menu, and the therapist is re-picked if the time
    moved. Nothing is written unless every check passes.
    """
    if not b or not b.is_active:
        return None, "booking_not_changeable"
    if by == "customer" and not b.customer_may_change:
        return None, "booking_too_late"

    treatment = treatment or b.treatment
    if not treatment or not treatment.is_active:
        return None, "booking_not_changeable"

    # An option must belong to the treatment it is priced against, or a guest
    # could pay a 60-minute price for a 120-minute treatment.
    if option is not None and (option.treatment_id != treatment.id
                               or not option.is_active):
        return None, "booking_not_changeable"

    minutes = duration_of(treatment, option)
    if day is not None and time_min is not None:
        starts = (datetime.combine(day, datetime.min.time())
                  + timedelta(minutes=int(time_min)))
    else:
        starts = b.starts_at
    ends = starts + timedelta(minutes=minutes)

    moved = (starts != b.starts_at or ends != b.ends_at)
    if moved:
        win = hours_for_day(starts.date())
        opens = starts.hour * 60 + starts.minute
        if not win or opens < win[0] or opens + minutes > win[1]:
            return None, "slot_gone"
        if starts < datetime.now() + timedelta(hours=LEAD_HOURS):
            return None, "slot_gone"
        # Keep the same therapist if they are still free; otherwise find one.
        picked = (_free_therapist(starts, ends, b.therapist_id, exclude_id=b.id)
                  or _free_therapist(starts, ends, exclude_id=b.id))
        if not picked:
            return None, "slot_gone"
        b.therapist_id = None if picked == "venue" else picked.id
        b.starts_at, b.ends_at = starts, ends
    elif minutes != b.duration_min:
        # Same start, longer treatment: the extra time must also be free.
        picked = (_free_therapist(starts, ends, b.therapist_id, exclude_id=b.id)
                  or _free_therapist(starts, ends, exclude_id=b.id))
        if not picked:
            return None, "slot_gone"
        b.therapist_id = None if picked == "venue" else picked.id
        b.ends_at = ends

    if area_id is not None:
        area = db.session.get(ServiceArea, int(area_id)) if area_id else None
        b.area_id = area.id if area else None
        b.travel_fee_idr = (area.travel_fee_idr or 0) if area else 0
    if service_address is not None:
        b.service_address = (service_address or "")[:400]
    if note is not None:
        b.note = (note or "")[:400]
    if guests is not None:
        b.guests = max(1, int(guests))

    b.treatment_id = treatment.id
    b.option_id = option.id if option is not None else None
    b.treatment_name = treatment.name_en[:160]
    b.duration_min = minutes
    _reprice(b, treatment, option)

    db.session.commit()
    return b, None


def cancel(b, by="customer"):
    """(booking, error_key). Cancelling frees the slot for everyone else."""
    if not b or not b.is_active:
        return None, "booking_not_changeable"
    if by == "customer" and not b.customer_may_change:
        return None, "booking_too_late"
    b.status = "cancelled"
    b.cancelled_at = datetime.now()
    b.cancelled_by = by
    db.session.commit()
    return b, None
