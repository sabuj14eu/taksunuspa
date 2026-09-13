# -*- coding: utf-8 -*-
"""Treatments, therapists and bookings.

Taksu Nusa is a home spa: the therapist travels to the guest's villa, hotel
or home. So a booking carries a service address and an area, not a room
number, and the areas we cover are part of the public site.

The booking engine came from the LokalnyDowoz spa vertical and keeps its
shape — opening hours produce a slot grid, a free therapist claims the slot,
and overlapping bookings are refused at write time.
"""
import secrets
from datetime import datetime

from ..extensions import db

BOOKING_ACTIVE = ["requested", "confirmed"]
BOOKING_STATUSES = BOOKING_ACTIVE + ["completed", "cancelled", "no_show"]


class TreatmentCategory(db.Model):
    """Sub-menu of the treatment menu: Massage, Body Rituals, Packages."""
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
    # Fallback duration and price, used when the treatment has no options.
    duration_min = db.Column(db.Integer, nullable=False, default=60)
    price_idr = db.Column(db.Integer, nullable=False, default=0)
    per_person = db.Column(db.Boolean, default=False)   # couple massage
    image_url = db.Column(db.String(400))
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    category = db.relationship("TreatmentCategory", backref="treatments")

    KIND = "treatment"

    @property
    def base_price(self):
        return self.price_idr

    @property
    def discount_target_id(self):
        return self.id

    @property
    def active_options(self):
        # Always shortest first. A spa menu reads 60 / 90 / 120, and ordering
        # by a separate sort field just lets a forgotten default scramble it.
        return sorted([o for o in self.options if o.is_active],
                      key=lambda o: o.duration_min)

    @property
    def cheapest_option(self):
        opts = self.active_options
        return min(opts, key=lambda o: o.price_idr) if opts else None


class TreatmentOption(db.Model):
    """A duration and its price: the same massage at 60, 90 or 120 minutes.

    The public menu shows every option side by side, and the guest books one.
    Discounts scoped to the parent treatment reach these through
    `discount_target_id`, so a sale marks all durations at once.
    """
    __tablename__ = "treatment_options"
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatments.id"),
                             nullable=False)
    duration_min = db.Column(db.Integer, nullable=False, default=60)
    price_idr = db.Column(db.Integer, nullable=False, default=0)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    treatment = db.relationship("Treatment", backref="options")

    KIND = "treatment"

    @property
    def base_price(self):
        return self.price_idr

    @property
    def discount_target_id(self):
        """Scoped discounts target the treatment, not the individual duration."""
        return self.treatment_id

    @property
    def category_id(self):
        return self.treatment.category_id if self.treatment else None


class Therapist(db.Model):
    """A bookable person. With no rows the spa books as a single resource."""
    __tablename__ = "therapists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    # WhatsApp number in international form, digits only (628123456789).
    phone = db.Column(db.String(30))
    role_en = db.Column(db.String(80), default="Therapist")
    role_idn = db.Column(db.String(80))
    languages = db.Column(db.String(120), default="English, Indonesian")
    bio_en = db.Column(db.Text, default="")
    bio_idn = db.Column(db.Text, default="")
    photo_url = db.Column(db.String(400))
    # Share of each treatment the therapist keeps. The usual arrangement here
    # is a split of the treatment price rather than a wage.
    commission_pct = db.Column(db.Integer, default=0)
    is_available_today = db.Column(db.Boolean, default=True)
    show_on_site = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class ServiceArea(db.Model):
    """Where the therapists travel. Shown as the "Areas we cover" section and
    offered in the booking form; a travel fee can apply per area."""
    __tablename__ = "service_areas"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(90), nullable=False)
    slug = db.Column(db.String(90), unique=True, nullable=False)
    travel_fee_idr = db.Column(db.Integer, default=0)   # 0 = free travel
    note_en = db.Column(db.String(200), default="")
    note_idn = db.Column(db.String(200), default="")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Highlight(db.Model):
    """A "why guests choose us" tile."""
    __tablename__ = "highlights"
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(8), default="✦")
    title_en = db.Column(db.String(90), nullable=False)
    title_idn = db.Column(db.String(90))
    text_en = db.Column(db.String(300), default="")
    text_idn = db.Column(db.String(300), default="")
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class OpeningHour(db.Model):
    """Service hours — when a therapist can start a treatment."""
    __tablename__ = "opening_hours"
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.Integer, nullable=False, unique=True)  # 0 = Monday
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
    option_id = db.Column(db.Integer, db.ForeignKey("treatment_options.id"))
    therapist_id = db.Column(db.Integer, db.ForeignKey("therapists.id"))
    area_id = db.Column(db.Integer, db.ForeignKey("service_areas.id"))

    customer_name = db.Column(db.String(80))
    customer_phone = db.Column(db.String(30), nullable=False)
    customer_email = db.Column(db.String(120))
    # Where the therapist goes: villa name, hotel and room number, address.
    service_address = db.Column(db.String(400))

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    guests = db.Column(db.Integer, default=1)

    # Snapshots: the menu may change after the booking is taken.
    treatment_name = db.Column(db.String(160))
    duration_min = db.Column(db.Integer, default=60)
    base_price_idr = db.Column(db.Integer, default=0)
    discount_idr = db.Column(db.Integer, default=0)
    travel_fee_idr = db.Column(db.Integer, default=0)
    total_idr = db.Column(db.Integer, default=0)
    discount_label = db.Column(db.String(80))

    payment_method = db.Column(db.String(20), default="cash")
    payment_status = db.Column(db.String(12), default="unpaid")
    lang = db.Column(db.String(3), default="en")
    note = db.Column(db.String(400))
    status = db.Column(db.String(12), default="requested")
    created_via = db.Column(db.String(12), default="web")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # What the therapist earns from this booking, and the payout that settled
    # it. Null fee means "work it out from the therapist's current rate" —
    # so a rate set after a booking was taken still applies to it.
    therapist_fee_idr = db.Column(db.Integer)
    payout_id = db.Column(db.Integer, db.ForeignKey("payouts.id"))

    treatment = db.relationship("Treatment")
    option = db.relationship("TreatmentOption")
    therapist = db.relationship("Therapist")
    area = db.relationship("ServiceArea")
    payout = db.relationship("Payout", backref="bookings")

    @property
    def fee_due(self) -> int:
        """The therapist's share, snapshotted once paid."""
        if self.therapist_fee_idr is not None:
            return self.therapist_fee_idr
        if not self.therapist:
            return 0
        pct = self.therapist.commission_pct or 0
        # The travel fee reimburses the trip, so commission is on the treatment.
        base = max(0, (self.total_idr or 0) - (self.travel_fee_idr or 0))
        return base * pct // 100
