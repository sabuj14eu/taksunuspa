# -*- coding: utf-8 -*-
"""The single place that decides what anything costs.

Every price on the site goes through `price_of()`, so a discount created in
admin shows up identically on a product card, a product page, a spa treatment
and the cart. When several discounts could apply to one item the customer
gets the biggest saving; ties break on `priority`, then on the newest row.
"""
from datetime import date

from ..models.discount import Discount


def _candidates(kind: str, item, with_code=None):
    """Discounts that could apply to this item, automatic ones plus, when the
    customer typed a code, the one matching that code."""
    today = date.today()
    typed = (with_code or "").strip().upper()
    group_id = getattr(item, "group_id", None)
    category_id = getattr(item, "category_id", None)
    matches = {
        "all": True,
        "products": kind == "product",
        "treatments": kind == "treatment",
        "product_group": kind == "product" and group_id is not None,
        "product": kind == "product",
        "treatment_category": kind == "treatment" and category_id is not None,
        "treatment": kind == "treatment",
    }
    target = {
        "product_group": group_id,
        "product": item.id,
        "treatment_category": category_id,
        "treatment": item.id,
    }
    out = []
    for d in Discount.query.filter_by(is_active=True).all():
        if not d.is_live(today):
            continue
        if not d.is_automatic and (d.code or "").upper() != typed:
            continue
        if not matches.get(d.scope):
            continue
        if d.scope in target and d.target_id != target[d.scope]:
            continue
        out.append(d)
    return out


def best_discount(kind: str, item, with_code=None):
    """(discount, rupiah_off) or (None, 0)."""
    base = int(getattr(item, "base_price", 0) or 0)
    if base <= 0:
        return None, 0
    best, best_off = None, 0
    for d in _candidates(kind, item, with_code):
        off = d.amount_off(base)
        if off > best_off or (off == best_off and off > 0 and best
                              and (d.priority or 0) > (best.priority or 0)):
            best, best_off = d, off
    return best, best_off


def price_of(kind: str, item, with_code=None) -> dict:
    """What the templates render.

    base    — the list price, shown struck through when discounted
    final   — what the customer pays
    off     — rupiah saved
    pct     — rounded percentage, for the "-20%" badge
    """
    base = int(getattr(item, "base_price", 0) or 0)
    d, off = best_discount(kind, item, with_code)
    final = max(0, base - off)
    return {
        "base": base,
        "final": final,
        "off": off,
        "pct": (off * 100 // base) if base and off else 0,
        "discount": d,
        "label": (d.label_en if d else None),
        "has_discount": off > 0,
    }


def price_product(product, with_code=None):
    return price_of("product", product, with_code)


def price_treatment(treatment, with_code=None):
    return price_of("treatment", treatment, with_code)


def live_discounts():
    """Everything currently running — for the admin dashboard and the site
    banner ("Grand opening: 20% off all treatments")."""
    today = date.today()
    rows = (Discount.query.filter_by(is_active=True)
            .order_by(Discount.priority.desc(), Discount.id.desc()).all())
    return [d for d in rows if d.is_live(today)]


def find_code(code: str):
    """A live, code-gated discount, or None."""
    typed = (code or "").strip().upper()
    if not typed:
        return None
    today = date.today()
    for d in Discount.query.filter_by(is_active=True).all():
        if not d.is_automatic and (d.code or "").upper() == typed and d.is_live(today):
            return d
    return None
