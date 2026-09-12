# -*- coding: utf-8 -*-
"""Spa treatments and bookings.

Extracted from the LokalnyDowoz spa vertical and reduced to a single venue:
Taksu Nusa Spa is one house, not a marketplace, so the venue columns moved
into SiteSetting and everything here hangs off the treatment menu.

The booking engine keeps the original shape — opening hours produce a slot
grid, a free therapist claims the slot, and overlapping bookings are refused.
"""
import secrets
from datetime import datetime
from ..extensions import db

BOOKING_ACTIVE = ["requested", "confirmed"]
BOOKING_STATUSES = BOOKING_ACTIVE + ["completed", "cancelled", "no_show"]


class TreatmentCategory(db.Model):
    """Sub-menu of the spa menu: Massage, Body Treatment, Facial, Packages."""
    __tablename__ = "treatment_categories"
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(90), nullable=False)
    name_idn = db.Column(db.String(90))
    slug = db.Column(db.String(90), unique=True, nullable=False)
    desc_en = db.Column(db.String(400), default="")
    desc_idn = db.Column(db.String(400), default="")
    icon = db.Column(db.String(8), default="💆")
    image_url = db.Column(db.String(400))
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Treatment(db.Model):
    __tablename__ = "treatments"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("treatment_categories.id"))
    name_en = db.Column(db.String(160), nullable=False)
    name_idn = db.Column(db.String(160))
    slug = db.Column(db.String(160), unique=True, nullable=False)
    desc_en = db.Column(db.Text, default="")
    desc_idn = db.Column(db.Text, default="")
    duration_min = db.Column(db.Integer, nullable=False, default=60)
    price_idr = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(400))
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    category = db.relationship("TreatmentCategory", backref="treatments")

    # Discounts key off these two, same as products.
    KIND = "treatment"

    @property
    def base_price(self):
        return self.price_idr


class Therapist(db.Model):
    """A bookable resource. With no rows the venue books as a single room."""
    __tablename__ = "therapists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    photo_url = db.Column(db.String(400))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class OpeningHour(db.Model):
    __tablename__ = "opening_hours"
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.Integer, nullable=False, unique=True)  # 0=Mon
    open_min = db.Column(db.Integer)
    close_min = db.Column(db.Integer)
    is_closed = db.Column(db.Boolean, default=False)


class HolidayHour(db.Model):
    """One-off override: Nyepi, Galungan, private events."""
    __tablename__ = "holiday_hours"
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Date, nullable=False, unique=True)
    open_min = db.Column(db.Integer)
    close_min = db.Column(db.Integer)
    is_closed = db.Column(db.Boolean, default=True)
    label = db.Column(db.String(80))


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    public_code = db.Column(db.String(8), unique=True,
                            default=lambda: secrets.token_hex(4).upper())
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatments.id"),
                             nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey("therapists.id"))
    customer_name = db.Column(db.String(80))
    customer_phone = db.Column(db.String(30), nullable=False)
    customer_email = db.Column(db.String(120))
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    guests = db.Column(db.Integer, default=1)
    # Snapshots: the menu may change price or wording after the booking.
    treatment_name = db.Column(db.String(160))
    base_price_idr = db.Column(db.Integer, default=0)
    discount_idr = db.Column(db.Integer, default=0)
    total_idr = db.Column(db.Integer, default=0)
    discount_label = db.Column(db.String(80))
    payment_method = db.Column(db.String(20), default="pay_at_spa")
    lang = db.Column(db.String(3), default="en")
    note = db.Column(db.String(400))
    status = db.Column(db.String(12), default="requested")
    created_via = db.Column(db.String(12), default="web")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    treatment = db.relationship("Treatment")
    therapist = db.relationship("Therapist")
