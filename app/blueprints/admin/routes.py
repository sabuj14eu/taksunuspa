# -*- coding: utf-8 -*-
"""Admin panel.

Everything the owner touches day to day lives here: the spa menu, the product
line, one discount screen that reaches both, orders, bookings, opening hours
and the site settings that feed the public pages and their structured data.
"""
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ...models.discount import KINDS, SCOPES, Discount
from ...models.media import MediaImage, Review
from ...models.shared import AuditLog
from ...models.shop import (ORDER_STATUSES, PAYMENT_METHODS, PAYMENT_STATUSES,
                            DeliveryZone, Order, Product, ProductGroup)
from ...models.site import (ContactMessage, FaqItem, MenuItem, Page,
                            SiteSetting)
from ...models.spa import (BOOKING_STATUSES, Booking, Highlight, HolidayHour,
                           OpeningHour, ServiceArea, Therapist, Treatment,
                           TreatmentCategory, TreatmentOption)
from ...models.user import User
from ...money import to_int
from ...services import media_service, seo_service, shop_service
from ...services.booking_service import hhmm

bp = Blueprint("admin", __name__)

SETTING_KEYS = [
    # identity
    "company_name", "brand_short", "tagline_en", "tagline_idn",
    "about_en", "about_idn", "nib",
    # contact
    "phone", "whatsapp", "email", "address", "city", "postal_code",
    "lat", "lng", "maps_url", "service_hours", "service_scope", "price_range",
    "facebook_url", "instagram_url", "tiktok_url",
    # home page copy
    "hero_eyebrow_en", "hero_eyebrow_idn", "hero_line1_en", "hero_line1_idn",
    "hero_line2_en", "hero_line2_idn", "hero_image",
    "rating_value", "rating_note_en", "rating_note_idn",
    "treatments_eyebrow_en", "treatments_intro_en", "treatments_intro_idn",
    "experience_eyebrow_en", "experience_title_en", "experience_title_idn",
    "therapists_eyebrow_en", "therapists_title_en", "therapists_title_idn",
    "therapists_intro_en", "therapists_intro_idn",
    "gallery_eyebrow_en", "products_eyebrow_en",
    "areas_note_en", "areas_note_idn",
    "reviews_eyebrow_en", "reviews_title_en", "reviews_title_idn",
    "cta_eyebrow_en", "cta_title_en", "cta_title_idn",
    "cta_text_en", "cta_text_idn",
    # plumbing
    "og_image", "meta_desc", "bank_details", "slot_step_min",
    "footer_note_en", "footer_note_idn",
]


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*a, **kw):
        if current_user.role not in ("admin", "staff"):
            abort(403)
        return fn(*a, **kw)
    return wrapper


bp.before_request(admin_required(lambda: None))


def _log(action, entity, detail=""):
    db.session.add(AuditLog(actor=getattr(current_user, "name", "?"),
                            action=action, entity=entity, detail=detail[:400]))


def _s(form, key, default=""):
    return (form.get(key) or default).strip()


def _b(form, key):
    return bool(form.get(key))


def _i(form, key, default=0):
    v = form.get(key)
    if v in (None, ""):
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _day(form, key):
    raw = _s(form, key)
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def _get_or_404(model, obj_id):
    row = db.session.get(model, obj_id)
    if not row:
        abort(404)
    return row


# ---------------------------------------------------------------- dashboard

@bp.route("/")
def dashboard():
    today = date.today()
    week_ago = today - timedelta(days=7)
    orders_open = Order.query.filter(Order.status.in_(
        ["new", "confirmed", "packed", "delivering"])).count()
    revenue_week = (db.session.query(func.coalesce(func.sum(Order.total_idr), 0))
                    .filter(Order.created_at >= week_ago,
                            Order.status != "cancelled").scalar() or 0)
    bookings_today = Booking.query.filter(
        Booking.starts_at >= datetime.combine(today, datetime.min.time()),
        Booking.starts_at < datetime.combine(today + timedelta(days=1),
                                             datetime.min.time())).count()
    low_stock = (Product.query.filter(Product.is_active.is_(True),
                                      Product.track_stock.is_(True),
                                      Product.stock <= 5)
                 .order_by(Product.stock).limit(10).all())
    return render_template(
        "admin/dashboard.html", active="dash",
        orders_open=orders_open, revenue_week=revenue_week,
        bookings_today=bookings_today, low_stock=low_stock,
        recent_orders=Order.query.order_by(Order.created_at.desc()).limit(8).all(),
        next_bookings=Booking.query.filter(Booking.starts_at >= datetime.now())
        .order_by(Booking.starts_at).limit(8).all(),
        unread=ContactMessage.query.filter_by(is_read=False).count(),
        live_discounts=[d for d in Discount.query.filter_by(is_active=True).all()
                        if d.is_live()])


# ---------------------------------------------------------------- products

@bp.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        f = request.form
        pid = _i(f, "id")
        p = _get_or_404(Product, pid) if pid else Product(name_en="", slug="")
        old_slug = p.slug
        p.name_en = _s(f, "name_en") or p.name_en or "Product"
        p.name_idn = _s(f, "name_idn")
        p.slug = seo_service.unique_slug(Product, _s(f, "slug") or p.name_en,
                                         ignore_id=p.id)
        p.group_id = _i(f, "group_id") or None
        p.short_en = _s(f, "short_en")
        p.short_idn = _s(f, "short_idn")
        p.desc_en = _s(f, "desc_en")
        p.desc_idn = _s(f, "desc_idn")
        p.size_label = _s(f, "size_label")
        p.sku = _s(f, "sku")
        p.price_idr = to_int(_s(f, "price_idr"))
        p.stock = _i(f, "stock")
        p.track_stock = _b(f, "track_stock")
        p.weight_g = _i(f, "weight_g")
        p.producer = _s(f, "producer")
        p.nib = _s(f, "nib")
        p.seo_title = _s(f, "seo_title")
        p.seo_desc = _s(f, "seo_desc")
        p.is_featured = _b(f, "is_featured")
        p.is_active = _b(f, "is_active")
        p.sort_order = _i(f, "sort_order")
        if not pid:
            db.session.add(p)
        db.session.flush()
        if old_slug and old_slug != p.slug:
            seo_service.record_redirect(f"/product/{old_slug}", f"/product/{p.slug}")
        _log("save", "product", p.name_en)
        db.session.commit()

        photo = request.files.get("photo")
        if photo and photo.filename:
            img = media_service.save_upload(photo, "product", p.id,
                                            alt_en=p.name_en)
            if img and not p.image_url:
                p.image_url = img.url
                db.session.commit()
        flash(f"Saved: {p.name_en}")
        return redirect(url_for("admin.products", edit=p.id))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/products.html", active="products",
        rows=Product.query.order_by(Product.sort_order, Product.id).all(),
        groups=ProductGroup.query.order_by(ProductGroup.sort_order).all(),
        edit=db.session.get(Product, edit_id) if edit_id else None,
        covers=media_service.covers_for(
            "product", [p.id for p in Product.query.all()]))


@bp.route("/products/<int:pid>/delete", methods=["POST"])
def product_delete(pid):
    p = _get_or_404(Product, pid)
    p.is_active = False           # keep it: past order lines point here
    _log("archive", "product", p.name_en)
    db.session.commit()
    flash(f"Archived: {p.name_en}")
    return redirect(url_for("admin.products"))


@bp.route("/product-groups", methods=["GET", "POST"])
def product_groups():
    if request.method == "POST":
        f = request.form
        gid = _i(f, "id")
        g = _get_or_404(ProductGroup, gid) if gid else ProductGroup(name_en="",
                                                                    slug="")
        old_slug = g.slug
        g.name_en = _s(f, "name_en") or g.name_en or "Group"
        g.name_idn = _s(f, "name_idn")
        g.slug = seo_service.unique_slug(ProductGroup, _s(f, "slug") or g.name_en,
                                         ignore_id=g.id)
        g.desc_en = _s(f, "desc_en")
        g.desc_idn = _s(f, "desc_idn")
        g.icon = _s(f, "icon") or "🍯"
        g.seo_title = _s(f, "seo_title")
        g.seo_desc = _s(f, "seo_desc")
        g.sort_order = _i(f, "sort_order")
        g.is_active = _b(f, "is_active")
        if not gid:
            db.session.add(g)
        db.session.flush()
        if old_slug and old_slug != g.slug:
            seo_service.record_redirect(f"/products/{old_slug}",
                                        f"/products/{g.slug}")
        _log("save", "product_group", g.name_en)
        db.session.commit()
        flash(f"Saved: {g.name_en}")
        return redirect(url_for("admin.product_groups"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/product_groups.html", active="groups",
        rows=ProductGroup.query.order_by(ProductGroup.sort_order,
                                         ProductGroup.id).all(),
        edit=db.session.get(ProductGroup, edit_id) if edit_id else None)


# ---------------------------------------------------------------- treatments

@bp.route("/treatments", methods=["GET", "POST"])
def treatments():
    if request.method == "POST":
        f = request.form
        tid = _i(f, "id")
        tr = _get_or_404(Treatment, tid) if tid else Treatment(name_en="", slug="")
        old_slug = tr.slug
        tr.name_en = _s(f, "name_en") or tr.name_en or "Treatment"
        tr.name_idn = _s(f, "name_idn")
        tr.slug = seo_service.unique_slug(Treatment, _s(f, "slug") or tr.name_en,
                                          ignore_id=tr.id)
        tr.category_id = _i(f, "category_id") or None
        tr.desc_en = _s(f, "desc_en")
        tr.desc_idn = _s(f, "desc_idn")
        tr.duration_min = _i(f, "duration_min", 60) or 60
        tr.price_idr = to_int(_s(f, "price_idr"))
        tr.per_person = _b(f, "per_person")
        tr.seo_title = _s(f, "seo_title")
        tr.seo_desc = _s(f, "seo_desc")
        tr.is_featured = _b(f, "is_featured")
        tr.is_active = _b(f, "is_active")
        tr.sort_order = _i(f, "sort_order")
        if not tid:
            db.session.add(tr)
        db.session.flush()
        if old_slug and old_slug != tr.slug:
            seo_service.record_redirect(f"/treatment/{old_slug}",
                                        f"/treatment/{tr.slug}")
        _log("save", "treatment", tr.name_en)
        db.session.commit()

        photo = request.files.get("photo")
        if photo and photo.filename:
            img = media_service.save_upload(photo, "treatment", tr.id,
                                            alt_en=tr.name_en)
            if img and not tr.image_url:
                tr.image_url = img.url
                db.session.commit()
        flash(f"Saved: {tr.name_en}")
        return redirect(url_for("admin.treatments", edit=tr.id))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/treatments.html", active="treatments",
        rows=Treatment.query.order_by(Treatment.sort_order, Treatment.id).all(),
        cats=TreatmentCategory.query.order_by(TreatmentCategory.sort_order).all(),
        edit=db.session.get(Treatment, edit_id) if edit_id else None,
        covers=media_service.covers_for(
            "treatment", [x.id for x in Treatment.query.all()]))


@bp.route("/treatments/<int:tid>/delete", methods=["POST"])
def treatment_delete(tid):
    tr = _get_or_404(Treatment, tid)
    tr.is_active = False
    _log("archive", "treatment", tr.name_en)
    db.session.commit()
    flash(f"Archived: {tr.name_en}")
    return redirect(url_for("admin.treatments"))


@bp.route("/treatments/<int:tid>/durations", methods=["POST"])
def treatment_durations(tid):
    """Add or update one duration tier — 60 / 90 / 120 minutes and its price."""
    tr = _get_or_404(Treatment, tid)
    f = request.form
    oid = _i(f, "option_id")
    if _s(f, "action") == "delete" and oid:
        o = _get_or_404(TreatmentOption, oid)
        if o.treatment_id == tr.id:
            db.session.delete(o)
            db.session.commit()
            flash("Duration removed")
        return redirect(url_for("admin.treatments", edit=tr.id))

    o = _get_or_404(TreatmentOption, oid) if oid else TreatmentOption(
        treatment_id=tr.id)
    if o.treatment_id != tr.id:
        abort(400)
    o.duration_min = _i(f, "duration_min", 60) or 60
    o.price_idr = to_int(_s(f, "price_idr"))
    o.sort_order = _i(f, "sort_order")
    o.is_active = _b(f, "is_active")
    if not oid:
        db.session.add(o)
    db.session.commit()
    flash(f"{tr.name_en}: {o.duration_min} min saved")
    return redirect(url_for("admin.treatments", edit=tr.id))


# ---------------------------------------------------------------- areas

@bp.route("/areas", methods=["GET", "POST"])
def areas():
    if request.method == "POST":
        f = request.form
        aid = _i(f, "id")
        a = _get_or_404(ServiceArea, aid) if aid else ServiceArea(name="", slug="")
        a.name = _s(f, "name") or a.name or "Area"
        a.slug = seo_service.unique_slug(ServiceArea, _s(f, "slug") or a.name,
                                         ignore_id=a.id)
        a.travel_fee_idr = to_int(_s(f, "travel_fee_idr"))
        a.note_en = _s(f, "note_en")
        a.note_idn = _s(f, "note_idn")
        a.sort_order = _i(f, "sort_order")
        a.is_active = _b(f, "is_active")
        if not aid:
            db.session.add(a)
        _log("save", "service_area", a.name)
        db.session.commit()
        flash(f"Saved: {a.name}")
        return redirect(url_for("admin.areas"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/areas.html", active="areas",
        rows=ServiceArea.query.order_by(ServiceArea.sort_order,
                                        ServiceArea.id).all(),
        edit=db.session.get(ServiceArea, edit_id) if edit_id else None)


@bp.route("/areas/<int:aid>/delete", methods=["POST"])
def area_delete(aid):
    a = _get_or_404(ServiceArea, aid)
    a.is_active = False       # bookings reference it
    db.session.commit()
    flash(f"Hidden: {a.name}")
    return redirect(url_for("admin.areas"))


# ---------------------------------------------------------------- therapists

@bp.route("/therapists", methods=["GET", "POST"])
def therapists():
    if request.method == "POST":
        f = request.form
        tid = _i(f, "id")
        th = _get_or_404(Therapist, tid) if tid else Therapist(name="")
        th.name = _s(f, "name") or th.name or "Therapist"
        th.role_en = _s(f, "role_en") or "Therapist"
        th.role_idn = _s(f, "role_idn")
        th.languages = _s(f, "languages")
        th.bio_en = _s(f, "bio_en")
        th.bio_idn = _s(f, "bio_idn")
        th.is_available_today = _b(f, "is_available_today")
        th.show_on_site = _b(f, "show_on_site")
        th.sort_order = _i(f, "sort_order")
        th.is_active = _b(f, "is_active")
        if not tid:
            db.session.add(th)
        db.session.flush()

        photo = request.files.get("photo")
        if photo and photo.filename:
            img = media_service.save_upload(photo, "therapist", th.id,
                                            alt_en=th.name)
            if img:
                th.photo_url = img.url
        _log("save", "therapist", th.name)
        db.session.commit()
        flash(f"Saved: {th.name}")
        return redirect(url_for("admin.therapists"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/therapists.html", active="therapists",
        rows=Therapist.query.order_by(Therapist.sort_order, Therapist.id).all(),
        edit=db.session.get(Therapist, edit_id) if edit_id else None)


# ---------------------------------------------------------------- highlights

@bp.route("/highlights", methods=["GET", "POST"])
def highlights():
    if request.method == "POST":
        f = request.form
        hid = _i(f, "id")
        h = _get_or_404(Highlight, hid) if hid else Highlight(title_en="")
        h.icon = _s(f, "icon") or "✦"
        h.title_en = _s(f, "title_en") or "Highlight"
        h.title_idn = _s(f, "title_idn")
        h.text_en = _s(f, "text_en")
        h.text_idn = _s(f, "text_idn")
        h.sort_order = _i(f, "sort_order")
        h.is_visible = _b(f, "is_visible")
        if not hid:
            db.session.add(h)
        db.session.commit()
        flash(f"Saved: {h.title_en}")
        return redirect(url_for("admin.highlights"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/highlights.html", active="highlights",
        rows=Highlight.query.order_by(Highlight.sort_order, Highlight.id).all(),
        edit=db.session.get(Highlight, edit_id) if edit_id else None)


@bp.route("/highlights/<int:hid>/delete", methods=["POST"])
def highlight_delete(hid):
    db.session.delete(_get_or_404(Highlight, hid))
    db.session.commit()
    return redirect(url_for("admin.highlights"))


@bp.route("/treatment-categories", methods=["GET", "POST"])
def treatment_categories():
    if request.method == "POST":
        f = request.form
        cid = _i(f, "id")
        c = (_get_or_404(TreatmentCategory, cid) if cid
             else TreatmentCategory(name_en="", slug=""))
        old_slug = c.slug
        c.name_en = _s(f, "name_en") or c.name_en or "Category"
        c.name_idn = _s(f, "name_idn")
        c.slug = seo_service.unique_slug(TreatmentCategory,
                                         _s(f, "slug") or c.name_en,
                                         ignore_id=c.id)
        c.desc_en = _s(f, "desc_en")
        c.desc_idn = _s(f, "desc_idn")
        c.icon = _s(f, "icon") or "💆"
        c.seo_title = _s(f, "seo_title")
        c.seo_desc = _s(f, "seo_desc")
        c.sort_order = _i(f, "sort_order")
        c.is_active = _b(f, "is_active")
        if not cid:
            db.session.add(c)
        db.session.flush()
        if old_slug and old_slug != c.slug:
            seo_service.record_redirect(f"/treatments/{old_slug}",
                                        f"/treatments/{c.slug}")
        _log("save", "treatment_category", c.name_en)
        db.session.commit()
        flash(f"Saved: {c.name_en}")
        return redirect(url_for("admin.treatment_categories"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/treatment_categories.html", active="spa_cats",
        rows=TreatmentCategory.query.order_by(TreatmentCategory.sort_order,
                                              TreatmentCategory.id).all(),
        edit=db.session.get(TreatmentCategory, edit_id) if edit_id else None)


# ---------------------------------------------------------------- discounts

@bp.route("/discounts", methods=["GET", "POST"])
def discounts():
    if request.method == "POST":
        f = request.form
        did = _i(f, "id")
        d = _get_or_404(Discount, did) if did else Discount(label_en="")
        d.label_en = _s(f, "label_en") or "Discount"
        d.label_idn = _s(f, "label_idn")
        d.scope = _s(f, "scope") if _s(f, "scope") in SCOPES else "all"
        d.target_id = _i(f, "target_id") or None
        d.kind = _s(f, "kind") if _s(f, "kind") in KINDS else "percent"
        d.value = to_int(_s(f, "value"))
        d.code = (_s(f, "code") or "").upper() or None
        d.min_subtotal_idr = to_int(_s(f, "min_subtotal_idr"))
        d.starts_on = _day(f, "starts_on")
        d.ends_on = _day(f, "ends_on")
        d.priority = _i(f, "priority")
        d.is_active = _b(f, "is_active")
        if not did:
            db.session.add(d)
        _log("save", "discount", d.label_en)
        db.session.commit()
        flash(f"Saved: {d.label_en}")
        return redirect(url_for("admin.discounts"))

    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/discounts.html", active="discounts", scopes=SCOPES, kinds=KINDS,
        rows=Discount.query.order_by(Discount.is_active.desc(),
                                     Discount.id.desc()).all(),
        edit=db.session.get(Discount, edit_id) if edit_id else None,
        groups=ProductGroup.query.order_by(ProductGroup.sort_order).all(),
        products=Product.query.order_by(Product.sort_order).all(),
        cats=TreatmentCategory.query.order_by(TreatmentCategory.sort_order).all(),
        treatments=Treatment.query.order_by(Treatment.sort_order).all(),
        today=date.today())


@bp.route("/discounts/<int:did>/delete", methods=["POST"])
def discount_delete(did):
    d = _get_or_404(Discount, did)
    db.session.delete(d)
    _log("delete", "discount", d.label_en)
    db.session.commit()
    flash("Discount deleted")
    return redirect(url_for("admin.discounts"))


# ---------------------------------------------------------------- orders

@bp.route("/orders")
def orders():
    status = request.args.get("status", "")
    q = Order.query
    if status in ORDER_STATUSES:
        q = q.filter_by(status=status)
    return render_template(
        "admin/orders.html", active="orders", statuses=ORDER_STATUSES,
        status=status,
        rows=q.order_by(Order.created_at.desc()).limit(200).all())


@bp.route("/orders/<int:oid>", methods=["GET", "POST"])
def order_detail(oid):
    o = _get_or_404(Order, oid)
    if request.method == "POST":
        f = request.form
        new_status = _s(f, "status")
        if new_status in ORDER_STATUSES and new_status != o.status:
            shop_service.set_status(o, new_status,
                                    getattr(current_user, "name", "admin"))
        pay = _s(f, "payment_status")
        if pay in PAYMENT_STATUSES and pay != o.payment_status:
            shop_service.set_payment(o, pay, _s(f, "payment_ref"),
                                     getattr(current_user, "name", "admin"))
        flash(f"Order {o.public_code} updated")
        return redirect(url_for("admin.order_detail", oid=o.id))
    return render_template("admin/order_detail.html", active="orders", o=o,
                           statuses=ORDER_STATUSES,
                           payment_statuses=PAYMENT_STATUSES,
                           payment_methods=PAYMENT_METHODS)


# ---------------------------------------------------------------- bookings

@bp.route("/bookings", methods=["GET", "POST"])
def bookings():
    if request.method == "POST":
        b = _get_or_404(Booking, _i(request.form, "id"))
        status = _s(request.form, "status")
        if status in BOOKING_STATUSES:
            b.status = status
            _log("status", "booking", f"{b.public_code} -> {status}")
            db.session.commit()
            flash(f"Booking {b.public_code}: {status}")
        return redirect(url_for("admin.bookings"))

    scope = request.args.get("scope", "upcoming")
    q = Booking.query
    if scope == "upcoming":
        q = q.filter(Booking.starts_at >= datetime.now())
        rows = q.order_by(Booking.starts_at).limit(200).all()
    else:
        rows = q.order_by(Booking.starts_at.desc()).limit(200).all()
    return render_template("admin/bookings.html", active="bookings", rows=rows,
                           scope=scope, statuses=BOOKING_STATUSES)


# ---------------------------------------------------------------- schedule

@bp.route("/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "POST":
        f = request.form
        if f.get("form") == "hours":
            for wd in range(7):
                h = OpeningHour.query.filter_by(weekday=wd).first()
                if not h:
                    h = OpeningHour(weekday=wd)
                    db.session.add(h)
                h.is_closed = _b(f, f"closed_{wd}")
                h.open_min = _hm(f.get(f"open_{wd}"))
                h.close_min = _hm(f.get(f"close_{wd}"))
            _log("save", "hours", "opening hours")
            db.session.commit()
            flash("Opening hours saved")
        elif f.get("form") == "holiday":
            day = _day(f, "day")
            if day:
                h = HolidayHour.query.filter_by(day=day).first() or HolidayHour(day=day)
                h.is_closed = _b(f, "is_closed")
                h.open_min = _hm(f.get("open"))
                h.close_min = _hm(f.get("close"))
                h.label = _s(f, "label")
                db.session.add(h)
                db.session.commit()
                flash(f"Saved: {day}")
        return redirect(url_for("admin.schedule"))

    hours = {h.weekday: h for h in OpeningHour.query.all()}
    return render_template(
        "admin/schedule.html", active="schedule", hours=hours, hhmm=hhmm,
        holidays=HolidayHour.query.filter(HolidayHour.day >= date.today())
        .order_by(HolidayHour.day).all())


def _hm(value):
    """'09:30' -> 570. Blank or malformed -> None."""
    if not value:
        return None
    try:
        h, m = str(value).split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------- delivery

@bp.route("/delivery", methods=["GET", "POST"])
def delivery():
    if request.method == "POST":
        f = request.form
        zid = _i(f, "id")
        z = _get_or_404(DeliveryZone, zid) if zid else DeliveryZone(name_en="")
        z.name_en = _s(f, "name_en") or "Zone"
        z.name_idn = _s(f, "name_idn")
        z.fee_idr = to_int(_s(f, "fee_idr"))
        z.free_over_idr = to_int(_s(f, "free_over_idr"))
        z.sort_order = _i(f, "sort_order")
        z.is_active = _b(f, "is_active")
        if not zid:
            db.session.add(z)
        db.session.commit()
        flash(f"Saved: {z.name_en}")
        return redirect(url_for("admin.delivery"))
    edit_id = request.args.get("edit", type=int)
    return render_template(
        "admin/delivery.html", active="delivery",
        rows=DeliveryZone.query.order_by(DeliveryZone.sort_order).all(),
        edit=db.session.get(DeliveryZone, edit_id) if edit_id else None)


# ---------------------------------------------------------------- content

@bp.route("/pages", methods=["GET", "POST"])
def pages():
    if request.method == "POST":
        f = request.form
        pid = _i(f, "id")
        p = _get_or_404(Page, pid) if pid else Page(slug="", title_en="")
        old_slug = p.slug
        p.title_en = _s(f, "title_en") or "Page"
        p.title_idn = _s(f, "title_idn")
        p.slug = seo_service.unique_slug(Page, _s(f, "slug") or p.title_en,
                                         ignore_id=p.id)
        p.body_en = f.get("body_en", "")
        p.body_idn = f.get("body_idn", "")
        p.seo_title = _s(f, "seo_title")
        p.seo_desc = _s(f, "seo_desc")
        p.is_visible = _b(f, "is_visible")
        p.show_in_menu = _b(f, "show_in_menu")
        p.sort_order = _i(f, "sort_order")
        if not pid:
            db.session.add(p)
        db.session.flush()
        if old_slug and old_slug != p.slug:
            seo_service.record_redirect(f"/p/{old_slug}", f"/p/{p.slug}")
        db.session.commit()
        flash(f"Saved: {p.title_en}")
        return redirect(url_for("admin.pages"))
    edit_id = request.args.get("edit", type=int)
    return render_template("admin/pages.html", active="pages",
                           rows=Page.query.order_by(Page.sort_order,
                                                    Page.id).all(),
                           edit=db.session.get(Page, edit_id) if edit_id else None)


@bp.route("/menu", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        f = request.form
        mid = _i(f, "id")
        m = _get_or_404(MenuItem, mid) if mid else MenuItem(label_en="", url="/")
        m.label_en = _s(f, "label_en") or "Link"
        m.label_idn = _s(f, "label_idn")
        m.url = _s(f, "url") or "/"
        m.icon = _s(f, "icon")
        m.style = "cta" if _s(f, "style") == "cta" else "normal"
        m.sort_order = _i(f, "sort_order")
        m.is_visible = _b(f, "is_visible")
        if not mid:
            db.session.add(m)
        db.session.commit()
        flash("Menu saved")
        return redirect(url_for("admin.menu"))
    edit_id = request.args.get("edit", type=int)
    return render_template("admin/menu.html", active="menu",
                           rows=MenuItem.query.order_by(MenuItem.sort_order,
                                                        MenuItem.id).all(),
                           edit=db.session.get(MenuItem, edit_id) if edit_id else None)


@bp.route("/menu/<int:mid>/delete", methods=["POST"])
def menu_delete(mid):
    db.session.delete(_get_or_404(MenuItem, mid))
    db.session.commit()
    return redirect(url_for("admin.menu"))


@bp.route("/faq", methods=["GET", "POST"])
def faq():
    if request.method == "POST":
        f = request.form
        fid = _i(f, "id")
        item = _get_or_404(FaqItem, fid) if fid else FaqItem()
        item.question_en = _s(f, "question_en")
        item.question_idn = _s(f, "question_idn")
        item.answer_en = f.get("answer_en", "")
        item.answer_idn = f.get("answer_idn", "")
        item.sort_order = _i(f, "sort_order")
        item.is_visible = _b(f, "is_visible")
        if not fid:
            db.session.add(item)
        db.session.commit()
        flash("FAQ saved")
        return redirect(url_for("admin.faq"))
    edit_id = request.args.get("edit", type=int)
    return render_template("admin/faq.html", active="faq",
                           rows=FaqItem.query.order_by(FaqItem.sort_order,
                                                       FaqItem.id).all(),
                           edit=db.session.get(FaqItem, edit_id) if edit_id else None)


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # Only touch keys the form actually submitted. A partial POST should
        # never blank the rest of the site's copy.
        for key in SETTING_KEYS:
            if key in request.form:
                SiteSetting.put(key, request.form.get(key, ""))
        _log("save", "settings", "site settings")
        db.session.commit()
        flash("Settings saved")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", active="settings",
                           keys=SETTING_KEYS, cfg=SiteSetting.all_dict())


@bp.route("/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        m = _get_or_404(ContactMessage, _i(request.form, "id"))
        m.is_read = True
        db.session.commit()
        return redirect(url_for("admin.messages"))
    return render_template(
        "admin/messages.html", active="messages",
        rows=ContactMessage.query.order_by(ContactMessage.created_at.desc())
        .limit(200).all())


# ---------------------------------------------------------------- media

@bp.route("/media", methods=["GET", "POST"])
def media():
    if request.method == "POST":
        entity_type = _s(request.form, "entity_type")
        # Site-wide collections (hero, gallery) hang off id 0, so an id of
        # zero is valid here and only a missing type is rejected.
        entity_id = _i(request.form, "entity_id")
        files = request.files.getlist("photos")
        saved = 0
        for fs in files:
            if fs and fs.filename and entity_type:
                if media_service.save_upload(fs, entity_type, entity_id,
                                             alt_en=_s(request.form, "alt_en")):
                    saved += 1
        flash(f"{saved} image(s) uploaded")
        return redirect(url_for("admin.media", entity_type=entity_type,
                                entity_id=entity_id))

    entity_type = request.args.get("entity_type", "product")
    entity_id = request.args.get("entity_id", type=int)
    rows = (media_service.gallery(entity_type, entity_id)
            if entity_id is not None and entity_type
            else MediaImage.query.order_by(MediaImage.id.desc()).limit(60).all())
    return render_template(
        "admin/media.html", active="media", rows=rows,
        entity_type=entity_type, entity_id=entity_id,
        products=Product.query.order_by(Product.sort_order).all(),
        treatments=Treatment.query.order_by(Treatment.sort_order).all(),
        therapists=Therapist.query.order_by(Therapist.sort_order).all())


@bp.route("/media/<int:mid>/delete", methods=["POST"])
def media_delete(mid):
    img = _get_or_404(MediaImage, mid)
    entity_type, entity_id = img.entity_type, img.entity_id
    media_service.delete_image(img)
    return redirect(url_for("admin.media", entity_type=entity_type,
                            entity_id=entity_id))


@bp.route("/media/<int:mid>/cover", methods=["POST"])
def media_cover(mid):
    img = _get_or_404(MediaImage, mid)
    media_service.set_cover(img)
    target = (Product if img.entity_type == "product" else
              Treatment if img.entity_type == "treatment" else None)
    if target:
        row = db.session.get(target, img.entity_id)
        if row:
            row.image_url = img.url
            db.session.commit()
    return redirect(url_for("admin.media", entity_type=img.entity_type,
                            entity_id=img.entity_id))


# ---------------------------------------------------------------- reviews

@bp.route("/reviews", methods=["GET", "POST"])
def reviews():
    if request.method == "POST":
        r = _get_or_404(Review, _i(request.form, "id"))
        if request.form.get("action") == "delete":
            db.session.delete(r)
        else:
            r.is_approved = not r.is_approved
            r.reply = _s(request.form, "reply") or r.reply
        db.session.commit()
        return redirect(url_for("admin.reviews"))
    return render_template(
        "admin/reviews.html", active="reviews",
        rows=Review.query.order_by(Review.created_at.desc()).limit(200).all())


# ---------------------------------------------------------------- account

@bp.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if len(pw) < 8:
            flash("Password must be at least 8 characters")
        else:
            current_user.set_password(pw)
            db.session.commit()
            flash("Password changed")
        return redirect(url_for("admin.account"))
    return render_template("admin/account.html", active="account",
                           users=User.query.order_by(User.id).all())
