# -*- coding: utf-8 -*-
"""Spa menu and treatment booking.

The menu is one page per category plus one page per treatment: real URLs a
search engine can rank for "Balinese massage Bali price", which a tabbed
single page cannot do.
"""
from datetime import date, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)

from ...extensions import db
from ...i18n import lang, loc, t
from ...models.site import SiteSetting
from ...models.spa import Booking, Therapist, Treatment, TreatmentCategory
from ...services import booking_service, media_service, pricing_service
from ...services import seo_service
from ...services.notify_service import notify_booking

bp = Blueprint("spa", __name__)

BOOKING_DAYS_AHEAD = 30


def _active_treatments(category=None):
    q = Treatment.query.filter_by(is_active=True)
    if category:
        q = q.filter_by(category_id=category.id)
    return q.order_by(Treatment.sort_order, Treatment.id).all()


@bp.route("/treatments")
@bp.route("/treatments/<cat_slug>")
def index(cat_slug=None):
    site = SiteSetting.all_dict()
    cats = (TreatmentCategory.query.filter_by(is_active=True)
            .order_by(TreatmentCategory.sort_order, TreatmentCategory.id).all())
    cat = None
    if cat_slug:
        cat = TreatmentCategory.query.filter_by(slug=cat_slug,
                                                is_active=True).first()
        if not cat:
            abort(404)
    rows = _active_treatments(cat)

    if cat:
        title, desc = seo_service.meta_for(
            "treatment", lang(), name=loc(cat, "name"),
            brand=site.get("company_name", "Taksu Nusa Spa"),
            city=site.get("city", "Bali"), seo_title=cat.seo_title,
            seo_desc=cat.seo_desc or loc(cat, "desc"))
    else:
        title, desc = seo_service.meta_for(
            "treatments", lang(),
            brand=site.get("company_name", "Taksu Nusa Spa"),
            city=site.get("city", "Bali"))

    base = current_app.config["SITE_URL"]
    crumbs = [(t()["home"], base + "/"), (t()["treatments"], base + "/treatments")]
    if cat:
        crumbs.append((loc(cat, "name"), None))

    return render_template(
        "spa/index.html", meta_title=title, meta_desc=desc,
        cats=cats, cat=cat, treatments=rows,
        covers=media_service.covers_for("treatment", [x.id for x in rows]),
        jsonld=seo_service.jsonld_breadcrumbs(crumbs))


@bp.route("/treatment/<slug>", methods=["GET"])
def detail(slug):
    tr = Treatment.query.filter_by(slug=slug, is_active=True).first()
    if not tr:
        abort(404)
    site = SiteSetting.all_dict()
    price = pricing_service.price_treatment(tr)

    day_str = request.args.get("day") or date.today().isoformat()
    try:
        day = date.fromisoformat(day_str)
    except ValueError:
        day = date.today()
    if day < date.today():
        day = date.today()

    therapist_id = request.args.get("therapist", type=int)
    days = [date.today() + timedelta(days=i) for i in range(BOOKING_DAYS_AHEAD)]
    step = int(site.get("slot_step_min") or 30)

    title, desc = seo_service.meta_for(
        "treatment", lang(), name=loc(tr, "name"),
        brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"), seo_title=tr.seo_title,
        seo_desc=tr.seo_desc)
    base = current_app.config["SITE_URL"]

    return render_template(
        "spa/detail.html", meta_title=title, meta_desc=desc, tr=tr, price=price,
        gallery=media_service.gallery("treatment", tr.id),
        therapists=Therapist.query.filter_by(is_active=True)
                   .order_by(Therapist.sort_order, Therapist.id).all(),
        therapist_id=therapist_id, day=day, days=days,
        slots=booking_service.slots_for(tr, day, therapist_id, step),
        jsonld=seo_service.jsonld_service(
            name=loc(tr, "name"), url=f"{base}/treatment/{tr.slug}",
            price_idr=price["final"], description=loc(tr, "desc"),
            duration_min=tr.duration_min,
            provider=site.get("company_name", "Taksu Nusa Spa")),
        jsonld_crumbs=seo_service.jsonld_breadcrumbs([
            (t()["home"], base + "/"),
            (t()["treatments"], base + "/treatments"),
            (loc(tr, "name"), None)]))


@bp.route("/treatment/<slug>/book", methods=["POST"])
def book(slug):
    tr = Treatment.query.filter_by(slug=slug, is_active=True).first()
    if not tr:
        abort(404)
    f = request.form
    phone = f.get("phone", "").strip()
    if not phone:
        flash(t()["phone"])
        return redirect(url_for("spa.detail", slug=slug))
    try:
        day = date.fromisoformat(f["day"])
        time_min = int(f["time_min"])
    except (KeyError, ValueError):
        abort(400)

    b, err = booking_service.book(
        tr, day, time_min, name=f.get("name", ""), phone=phone,
        email=f.get("email", ""), note=f.get("note", ""),
        guests=f.get("guests", type=int) or 1,
        therapist_id=f.get("therapist_id", type=int),
        lang=lang(), payment_method=f.get("payment_method", "pay_at_spa"))
    if err:
        flash(t().get(err, err))
        return redirect(url_for("spa.detail", slug=slug, day=day.isoformat()))

    notify_booking(b, current_app.config["SITE_URL"])
    return redirect(url_for("spa.booking_view", code=b.public_code))


@bp.route("/booking/<code>")
def booking_view(code):
    b = Booking.query.filter_by(public_code=code.upper()).first()
    if not b:
        abort(404)
    return render_template("spa/booking.html", b=b, meta_title="Booking "
                           f"{b.public_code}", meta_desc="", noindex=True)
