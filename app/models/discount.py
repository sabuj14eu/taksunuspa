# -*- coding: utf-8 -*-
"""One discount table for the whole site.

A discount is written once and can target everything, one product group, one
treatment category, or a single item — so the same admin screen puts a sale
badge on a jar of honey and on a Balinese massage. Automatic discounts apply
themselves in the shop and the booking form; a discount with a `code` waits
for the customer to type it at checkout.
"""
from datetime import datetime
from ..extensions import db

SCOPES = ["all", "products", "treatments", "product_group", "product",
          "treatment_category", "treatment"]
KINDS = ["percent", "amount"]


class Discount(db.Model):
    __tablename__ = "discounts"
    id = db.Column(db.Integer, primary_key=True)
    label_en = db.Column(db.String(80), nullable=False)
    label_idn = db.Column(db.String(80))
    scope = db.Column(db.String(20), nullable=False, default="all")
    target_id = db.Column(db.Integer)          # group / category / item id
    kind = db.Column(db.String(10), nullable=False, default="percent")
    value = db.Column(db.Integer, nullable=False, default=0)  # 20 => 20% or Rp 20
    code = db.Column(db.String(24))            # NULL = applies automatically
    min_subtotal_idr = db.Column(db.Integer, default=0)
    starts_on = db.Column(db.Date)
    ends_on = db.Column(db.Date)
    priority = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_automatic(self):
        return not (self.code or "").strip()

    def is_live(self, on_day=None):
        day = on_day or datetime.utcnow().date()
        if not self.is_active:
            return False
        if self.starts_on and day < self.starts_on:
            return False
        if self.ends_on and day > self.ends_on:
            return False
        return True

    def amount_off(self, base_idr: int) -> int:
        """Rupiah taken off `base_idr`, never more than the price itself."""
        base = int(base_idr or 0)
        if base <= 0 or (self.value or 0) <= 0:
            return 0
        off = base * int(self.value) // 100 if self.kind == "percent" else int(self.value)
        return max(0, min(off, base))

    def badge(self) -> str:
        return f"-{self.value}%" if self.kind == "percent" else f"-{self.value:,}".replace(",", ".")
