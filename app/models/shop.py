# -*- coding: utf-8 -*-
"""Product line + online orders.

ProductGroup is what the product page shows as its sub-menu (Honey, Spa Oils,
Gift Sets ...), matching how spaairbali.com splits its product page. Orders
are delivered inside the spa's service areas and paid cash on delivery, by
bank transfer, or online, so an order carries both a payment method and a
payment status.
"""
import json
import secrets
from datetime import datetime
from ..extensions import db

ORDER_STATUSES = ["new", "confirmed", "packed", "delivering", "completed",
                  "cancelled"]
ORDER_OPEN = ["new", "confirmed", "packed", "delivering"]
PAYMENT_METHODS = ["cod", "cash", "transfer", "online"]
PAYMENT_STATUSES = ["unpaid", "paid", "refunded"]


class ProductGroup(db.Model):
    """Sub-menu entry on the product page."""
    __tablename__ = "product_groups"
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(90), nullable=False)
    name_idn = db.Column(db.String(90))
    slug = db.Column(db.String(90), unique=True, nullable=False)
    desc_en = db.Column(db.Text, default="")
    desc_idn = db.Column(db.Text, default="")
    icon = db.Column(db.String(8), default="🍯")
    image_url = db.Column(db.String(400))
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("product_groups.id"))
    name_en = db.Column(db.String(160), nullable=False)
    name_idn = db.Column(db.String(160))
    slug = db.Column(db.String(160), unique=True, nullable=False)
    short_en = db.Column(db.String(300), default="")
    short_idn = db.Column(db.String(300), default="")
    desc_en = db.Column(db.Text, default="")
    desc_idn = db.Column(db.Text, default="")
    size_label = db.Column(db.String(40))          # "250 ml", "500 ml"
    sku = db.Column(db.String(40))
    price_idr = db.Column(db.Integer, nullable=False, default=0)
    weight_g = db.Column(db.Integer, default=0)    # for delivery pricing later
    stock = db.Column(db.Integer, default=0)
    track_stock = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(400))
    producer = db.Column(db.String(120))           # "Yustika, Balangan"
    nib = db.Column(db.String(40))                 # Indonesian business number
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("ProductGroup", backref="products")

    KIND = "product"

    @property
    def base_price(self):
        return self.price_idr

    @property
    def discount_target_id(self):
        return self.id

    @property
    def in_stock(self):
        return (not self.track_stock) or (self.stock or 0) > 0


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    public_code = db.Column(db.String(8), unique=True,
                            default=lambda: secrets.token_hex(4).upper())
    customer_name = db.Column(db.String(80))
    customer_phone = db.Column(db.String(30), nullable=False)
    customer_email = db.Column(db.String(120))
    address = db.Column(db.String(400))
    city = db.Column(db.String(80))
    note = db.Column(db.String(400))
    subtotal_idr = db.Column(db.Integer, default=0)
    discount_idr = db.Column(db.Integer, default=0)
    delivery_idr = db.Column(db.Integer, default=0)
    total_idr = db.Column(db.Integer, default=0)
    payment_method = db.Column(db.String(20), default="cod")
    payment_status = db.Column(db.String(12), default="unpaid")
    payment_ref = db.Column(db.String(80))         # transfer proof / gateway id
    status = db.Column(db.String(12), default="new")
    lang = db.Column(db.String(3), default="en")
    created_via = db.Column(db.String(12), default="web")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def items_total_qty(self):
        return sum(i.qty for i in self.items)


class OrderItem(db.Model):
    """Line snapshot: name and price are frozen at order time."""
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    name = db.Column(db.String(200))
    size_label = db.Column(db.String(40))
    qty = db.Column(db.Integer, nullable=False, default=1)
    unit_price_idr = db.Column(db.Integer, default=0)     # before discount
    unit_final_idr = db.Column(db.Integer, default=0)     # after discount
    discount_label = db.Column(db.String(80))
    line_total_idr = db.Column(db.Integer, default=0)

    order = db.relationship("Order", backref=db.backref("items", lazy="joined"))
    product = db.relationship("Product")


class OrderEvent(db.Model):
    """Audit trail for the admin order screen."""
    __tablename__ = "order_events"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    kind = db.Column(db.String(20))
    detail = db.Column(db.String(300))
    actor = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", backref="events")


class DeliveryZone(db.Model):
    """Flat delivery fee per area, with a free-over threshold."""
    __tablename__ = "delivery_zones"
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(90), nullable=False)
    name_idn = db.Column(db.String(90))
    fee_idr = db.Column(db.Integer, default=0)
    free_over_idr = db.Column(db.Integer, default=0)   # 0 = never free
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def fee_for(self, subtotal_idr: int) -> int:
        if self.free_over_idr and subtotal_idr >= self.free_over_idr:
            return 0
        return self.fee_idr or 0


def dump_items(items) -> str:
    return json.dumps(items, ensure_ascii=False)
