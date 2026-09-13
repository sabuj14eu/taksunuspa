# -*- coding: utf-8 -*-
"""Money in, money out.

Deliberately small: what a spa owner needs on a Sunday evening is what came
in this week, what is owed to each therapist, and what was spent — not a
general ledger. Income is read from bookings and orders that already exist;
only expenses and payouts need tables of their own.
"""
from datetime import datetime

from ..extensions import db

EXPENSE_CATEGORIES = [
    "supplies",       # oils, towels, candles
    "products",       # stock bought for resale
    "transport",      # fuel, driver
    "rent",
    "salary",         # fixed staff pay, as opposed to therapist commission
    "marketing",
    "utilities",
    "fees",           # bank, payment gateway, licences
    "other",
]

PAY_METHODS = ["cash", "transfer", "other"]


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(20), nullable=False, default="other")
    description = db.Column(db.String(200))
    paid_to = db.Column(db.String(120))
    amount_idr = db.Column(db.Integer, nullable=False, default=0)
    method = db.Column(db.String(12), default="cash")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payout(db.Model):
    """A payment made to a therapist, covering a set of bookings.

    Bookings point back at the payout that settled them, so "what is still
    owed" is simply the bookings with no payout — no period arithmetic to get
    wrong, and no double-paying a booking that spans two weeks.
    """
    __tablename__ = "payouts"
    id = db.Column(db.Integer, primary_key=True)
    therapist_id = db.Column(db.Integer, db.ForeignKey("therapists.id"),
                             nullable=False)
    amount_idr = db.Column(db.Integer, nullable=False, default=0)
    bookings_count = db.Column(db.Integer, default=0)
    paid_on = db.Column(db.Date, nullable=False)
    method = db.Column(db.String(12), default="cash")
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    therapist = db.relationship("Therapist", backref="payouts")
