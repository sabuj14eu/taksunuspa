# -*- coding: utf-8 -*-
"""Cart and orders.

The cart lives in the session as {product_id: qty} and is priced fresh on
every read, so a discount that starts or ends while a cart sits open is
reflected immediately. Nothing about money is trusted from the browser.
"""
from flask import session

from ..extensions import db
from ..models.shop import (Product, Order, OrderItem, OrderEvent, DeliveryZone,
                           PAYMENT_METHODS)
from . import pricing_service

CART_KEY = "cart"
MAX_QTY = 99


# ---------- cart ----------

def _raw():
    cart = session.get(CART_KEY)
    return cart if isinstance(cart, dict) else {}


def _save(cart):
    session[CART_KEY] = cart
    session.modified = True


def add(product_id: int, qty: int = 1):
    cart = _raw()
    key = str(int(product_id))
    cart[key] = min(MAX_QTY, max(1, cart.get(key, 0) + max(1, int(qty))))
    _save(cart)


def set_qty(product_id: int, qty: int):
    cart = _raw()
    key = str(int(product_id))
    qty = int(qty)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = min(MAX_QTY, qty)
    _save(cart)


def remove(product_id: int):
    set_qty(product_id, 0)


def clear():
    session.pop(CART_KEY, None)
    session.modified = True


def count() -> int:
    return sum(int(q) for q in _raw().values())


def lines(code=None):
    """Priced cart lines. Inactive or deleted products drop out silently."""
    cart = _raw()
    if not cart:
        return []
    ids = [int(k) for k in cart if str(k).isdigit()]
    products = {p.id: p for p in
                Product.query.filter(Product.id.in_(ids), Product.is_active.is_(True)).all()}
    out = []
    for pid in ids:
        p = products.get(pid)
        if not p:
            continue
        qty = int(cart[str(pid)])
        if p.track_stock:
            qty = min(qty, max(0, p.stock or 0))
        if qty <= 0:
            continue
        price = pricing_service.price_product(p, code)
        out.append({"product": p, "qty": qty, "price": price,
                    "line_total": price["final"] * qty,
                    "line_off": price["off"] * qty})
    return out


def totals(code=None, zone_id=None):
    rows = lines(code)
    subtotal = sum(r["price"]["base"] * r["qty"] for r in rows)
    discount = sum(r["line_off"] for r in rows)
    goods = subtotal - discount
    zone = db.session.get(DeliveryZone, int(zone_id)) if zone_id else None
    delivery = zone.fee_for(goods) if zone else 0
    return {"lines": rows, "subtotal": subtotal, "discount": discount,
            "goods": goods, "delivery": delivery, "zone": zone,
            "total": goods + delivery, "count": sum(r["qty"] for r in rows)}


# ---------- checkout ----------

def place_order(*, name, phone, email="", address="", city="", note="",
                payment_method="cod", code=None, zone_id=None, lang="en",
                via="web"):
    """(order, error_key). Prices are recomputed here — never read from the
    form — so a tampered checkout page cannot change what is charged."""
    t = totals(code, zone_id)
    if not t["lines"]:
        return None, "cart_empty_err"
    if payment_method not in PAYMENT_METHODS:
        payment_method = "cod"

    order = Order(
        customer_name=(name or "")[:80], customer_phone=phone[:30],
        customer_email=(email or "")[:120], address=(address or "")[:400],
        city=(city or "")[:80], note=(note or "")[:400],
        subtotal_idr=t["subtotal"], discount_idr=t["discount"],
        delivery_idr=t["delivery"], total_idr=t["total"],
        payment_method=payment_method, lang=lang, created_via=via)
    db.session.add(order)
    db.session.flush()      # need order.id for the lines

    for row in t["lines"]:
        p, qty, price = row["product"], row["qty"], row["price"]
        db.session.add(OrderItem(
            order_id=order.id, product_id=p.id,
            name=p.name_en[:200], size_label=p.size_label, qty=qty,
            unit_price_idr=price["base"], unit_final_idr=price["final"],
            discount_label=(price["label"] or "")[:80] or None,
            line_total_idr=row["line_total"]))
        if p.track_stock:
            p.stock = max(0, (p.stock or 0) - qty)

    db.session.add(OrderEvent(order_id=order.id, kind="created",
                              detail=f"{t['count']} item(s), {payment_method}",
                              actor="customer"))
    db.session.commit()
    clear()
    return order, None


def set_status(order: Order, status: str, actor="admin"):
    order.status = status
    if status == "completed" and order.payment_status == "unpaid" \
            and order.payment_method in ("cod", "cash"):
        order.payment_status = "paid"
    db.session.add(OrderEvent(order_id=order.id, kind="status",
                              detail=status, actor=actor))
    db.session.commit()


def set_payment(order: Order, payment_status: str, ref=None, actor="admin"):
    order.payment_status = payment_status
    if ref:
        order.payment_ref = ref[:80]
    db.session.add(OrderEvent(order_id=order.id, kind="payment",
                              detail=payment_status, actor=actor))
    db.session.commit()
