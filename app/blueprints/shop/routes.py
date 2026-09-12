# -*- coding: utf-8 -*-
"""Our Product Line: group sub-menu, product pages, cart, checkout.

Layout follows the pattern the client asked for (spaairbali.com/spa-products):
one products page with a sub-menu across the groups, each group and each
product on its own indexable URL.
"""
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)

from ...i18n import lang, loc, t
from ...models.shop import DeliveryZone, Order, Product, ProductGroup
from ...models.site import SiteSetting
from ...money import rp
from ...services import media_service, pricing_service, seo_service, shop_service
from ...services.notify_service import notify_order

bp = Blueprint("shop", __name__)

CODE_KEY = "discount_code"


def _groups():
    return (ProductGroup.query.filter_by(is_active=True)
            .order_by(ProductGroup.sort_order, ProductGroup.id).all())


def _code():
    return session.get(CODE_KEY)


@bp.route("/products")
@bp.route("/products/<group_slug>")
def index(group_slug=None):
    site = SiteSetting.all_dict()
    groups = _groups()
    group = None
    if group_slug:
        group = ProductGroup.query.filter_by(slug=group_slug,
                                             is_active=True).first()
        if not group:
            abort(404)

    q = Product.query.filter_by(is_active=True)
    if group:
        q = q.filter_by(group_id=group.id)
    products = q.order_by(Product.sort_order, Product.id).all()

    if group:
        title, desc = seo_service.meta_for(
            "product_group", lang(), name=loc(group, "name"),
            brand=site.get("company_name", "Taksu Nusa Spa"),
            seo_title=group.seo_title,
            seo_desc=group.seo_desc or loc(group, "desc"))
    else:
        title, desc = seo_service.meta_for(
            "products", lang(),
            brand=site.get("company_name", "Taksu Nusa Spa"))

    base = current_app.config["SITE_URL"]
    crumbs = [(t()["home"], base + "/"),
              (t()["our_product_line"], base + "/products")]
    if group:
        crumbs.append((loc(group, "name"), None))

    return render_template(
        "shop/index.html", meta_title=title, meta_desc=desc,
        groups=groups, group=group, products=products,
        covers=media_service.covers_for("product", [p.id for p in products]),
        code=_code(),
        jsonld=seo_service.jsonld_breadcrumbs(crumbs))


@bp.route("/product/<slug>")
def detail(slug):
    p = Product.query.filter_by(slug=slug, is_active=True).first()
    if not p:
        abort(404)
    site = SiteSetting.all_dict()
    price = pricing_service.price_product(p, _code())
    base = current_app.config["SITE_URL"]

    title, desc = seo_service.meta_for(
        "product", lang(), name=loc(p, "name"), price=rp(price["final"]),
        brand=site.get("company_name", "Taksu Nusa Spa"),
        group=loc(p.group, "name") if p.group else "",
        seo_title=p.seo_title, seo_desc=p.seo_desc or loc(p, "short"))

    related = (Product.query.filter(Product.is_active.is_(True),
                                    Product.id != p.id,
                                    Product.group_id == p.group_id)
               .order_by(Product.sort_order, Product.id).limit(4).all())

    return render_template(
        "shop/detail.html", meta_title=title, meta_desc=desc, p=p, price=price,
        gallery=media_service.gallery("product", p.id), related=related,
        covers=media_service.covers_for("product", [r.id for r in related]),
        jsonld=seo_service.jsonld_product(
            name=loc(p, "name"), url=f"{base}/product/{p.slug}",
            price_idr=price["final"],
            image=(base + (p.image_url or "")) if p.image_url else None,
            description=loc(p, "short") or loc(p, "desc"), sku=p.sku,
            brand=p.producer or site.get("company_name"), in_stock=p.in_stock),
        jsonld_crumbs=seo_service.jsonld_breadcrumbs([
            (t()["home"], base + "/"),
            (t()["our_product_line"], base + "/products"),
            *([(loc(p.group, "name"), f"{base}/products/{p.group.slug}")]
              if p.group else []),
            (loc(p, "name"), None)]))


# ---------- cart ----------

@bp.route("/cart")
def cart():
    zone_id = session.get("zone_id")
    totals = shop_service.totals(_code(), zone_id)
    return render_template("shop/cart.html", meta_title=t()["cart"],
                           meta_desc="", noindex=True, totals=totals,
                           code=_code(),
                           zones=DeliveryZone.query.filter_by(is_active=True)
                           .order_by(DeliveryZone.sort_order).all(),
                           zone_id=zone_id)


@bp.route("/cart/add", methods=["POST"])
def cart_add():
    pid = request.form.get("product_id", type=int)
    p = Product.query.filter_by(id=pid, is_active=True).first() if pid else None
    if not p:
        abort(400)
    if not p.in_stock:
        flash(t()["out_of_stock"])
        return redirect(url_for("shop.detail", slug=p.slug))
    shop_service.add(p.id, request.form.get("qty", type=int) or 1)
    if request.form.get("buy_now"):
        return redirect(url_for("shop.checkout"))
    return redirect(request.form.get("back") or url_for("shop.cart"))


@bp.route("/cart/update", methods=["POST"])
def cart_update():
    for key, value in request.form.items():
        if key.startswith("qty_"):
            pid = key[4:]
            if pid.isdigit():
                try:
                    shop_service.set_qty(int(pid), int(value))
                except ValueError:
                    continue
    code = request.form.get("code", "").strip()
    if code:
        if pricing_service.find_code(code):
            session[CODE_KEY] = code.upper()
            flash(f"{t()['discount']}: {code.upper()}")
        else:
            session.pop(CODE_KEY, None)
            flash(t()["no_results"])
    elif "code" in request.form:
        session.pop(CODE_KEY, None)
    zone_id = request.form.get("zone_id", type=int)
    session["zone_id"] = zone_id or None
    return redirect(url_for("shop.cart"))


@bp.route("/cart/remove/<int:pid>", methods=["POST"])
def cart_remove(pid):
    shop_service.remove(pid)
    return redirect(url_for("shop.cart"))


# ---------- checkout ----------

@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    site = SiteSetting.all_dict()
    zones = (DeliveryZone.query.filter_by(is_active=True)
             .order_by(DeliveryZone.sort_order).all())

    if request.method == "POST":
        f = request.form
        zone_id = f.get("zone_id", type=int)
        session["zone_id"] = zone_id or None
        phone = f.get("phone", "").strip()
        if not phone:
            flash(t()["phone"])
            return redirect(url_for("shop.checkout"))

        order, err = shop_service.place_order(
            name=f.get("name", ""), phone=phone, email=f.get("email", ""),
            address=f.get("address", ""), city=f.get("city", ""),
            note=f.get("note", ""), payment_method=f.get("payment_method", "cod"),
            code=_code(), zone_id=zone_id, lang=lang())
        if err:
            flash(t().get(err, err))
            return redirect(url_for("shop.cart"))

        session.pop(CODE_KEY, None)
        notify_order(order, current_app.config["SITE_URL"])
        return redirect(url_for("shop.order_view", code=order.public_code))

    totals = shop_service.totals(_code(), session.get("zone_id"))
    if not totals["lines"]:
        flash(t()["empty_cart"])
        return redirect(url_for("shop.index"))
    return render_template("shop/checkout.html", meta_title=t()["checkout"],
                           meta_desc="", noindex=True, totals=totals,
                           zones=zones, zone_id=session.get("zone_id"),
                           bank=site.get("bank_details", ""))


@bp.route("/order/<code>")
def order_view(code):
    o = Order.query.filter_by(public_code=code.upper()).first()
    if not o:
        abort(404)
    site = SiteSetting.all_dict()
    return render_template("shop/order.html", o=o, meta_title=f"Order {o.public_code}",
                           meta_desc="", noindex=True,
                           bank=site.get("bank_details", ""))
