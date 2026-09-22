# -*- coding: utf-8 -*-
"""Treatment menu and booking.

One page per treatment, one per category: real URLs a search engine can rank
for "Balinese massage Seminyak price", which a tabbed single page cannot do.
"""
from datetime import date, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)

from ...extensions import db
from ...i18n import lang, loc, t
from ...models.site import SiteSetting
from ...models.spa import (Booking, ServiceArea, Therapist, Treatment,
                           TreatmentCategory, TreatmentOption)
from ...services import booking_service, media_service, pricing_service
from ...services import seo_service
from ...services import notify_service
from ...services.notify_service import notify_booking

bp = Blueprint("spa", __name__)

BOOKING_DAYS_AHEAD = 30


def _areas():
    return (ServiceArea.query.filter_by(is_active=True)
            .order_by(ServiceArea.sort_order, ServiceArea.id).all())


@bp.route("/treatments")
@bp.route("/treatments/<cat_slug>")
def index(cat_slug=None):
    site = SiteSetting.all_dict()
    # Only groups that actually hold a treatment. An empty one used to render
    # a page reading "Nothing found", which looks broken to a guest; it comes
    # back by itself as soon as a treatment is put in it.
    cats = [c for c in
            TreatmentCategory.query.filter_by(is_active=True)
            .order_by(TreatmentCategory.sort_order, TreatmentCategory.id).all()
            if any(t.is_active for t in c.treatments)]
    cat = None
    if cat_slug:
        cat = next((c for c in cats if c.slug == cat_slug), None)
        if not cat:
            abort(404)

    q = Treatment.query.filter_by(is_active=True)
    if cat:
        q = q.filter_by(category_id=cat.id)
    rows = q.order_by(Treatment.sort_order, Treatment.id).all()

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
        cats=cats, cat=cat, treatments=rows, areas=_areas(),
        covers=media_service.covers_for("treatment", [x.id for x in rows]),
        jsonld_crumbs=seo_service.jsonld_breadcrumbs(crumbs))


@bp.route("/treatment/<slug>")
def detail(slug):
    tr = Treatment.query.filter_by(slug=slug, is_active=True).first()
    if not tr:
        abort(404)
    site = SiteSetting.all_dict()

    options = tr.active_options
    option = None
    wanted = request.args.get("option", type=int)
    if wanted:
        option = next((o for o in options if o.id == wanted), None)
    if option is None and options:
        option = options[0]
    price = pricing_service.price_of("treatment", option or tr)

    therapist_id = request.args.get("therapist", type=int)
    days = [date.today() + timedelta(days=i) for i in range(BOOKING_DAYS_AHEAD)]
    step = int(site.get("slot_step_min") or 30)

    # Land the guest on a day they can actually book. Asked for a specific
    # day we show that day, empty or not; arriving with no day at all, we
    # open on the first one with a free time rather than on a today that
    # closed hours ago.
    requested = request.args.get("day")
    day = None
    if requested:
        try:
            day = date.fromisoformat(requested)
        except ValueError:
            day = None
        if day and day < date.today():
            day = None
    if day is None:
        day = (booking_service.next_available_day(
            tr, therapist_id=therapist_id, option=option, step_min=step,
            days=BOOKING_DAYS_AHEAD) or date.today())

    slots = booking_service.slots_for(tr, day, therapist_id, option, step)
    # Nothing free on the chosen day: point at the next one that is, so the
    # guest has somewhere to go instead of a dead end.
    next_free = None
    if not slots:
        next_free = booking_service.next_available_day(
            tr, from_day=day + timedelta(days=1), therapist_id=therapist_id,
            option=option, step_min=step, days=BOOKING_DAYS_AHEAD)

    title, desc = seo_service.meta_for(
        "treatment", lang(), name=loc(tr, "name"),
        brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"), seo_title=tr.seo_title,
        seo_desc=tr.seo_desc)
    base = current_app.config["SITE_URL"]

    return render_template(
        "spa/detail.html", meta_title=title, meta_desc=desc, tr=tr,
        options=options, option=option, price=price, areas=_areas(),
        gallery=media_service.gallery("treatment", tr.id),
        therapists=(Therapist.query.filter_by(is_active=True)
                    .order_by(Therapist.sort_order, Therapist.id).all()),
        therapist_id=therapist_id, day=day, days=days,
        slots=slots, next_free=next_free,
        jsonld=seo_service.jsonld_service(
            name=loc(tr, "name"), url=f"{base}/treatment/{tr.slug}",
            price_idr=price["final"], description=loc(tr, "desc"),
            duration_min=booking_service.duration_of(tr, option),
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

    option = None
    option_id = f.get("option_id", type=int)
    if option_id:
        option = db.session.get(TreatmentOption, option_id)
        # Never price a booking from an option belonging to another treatment.
        if not option or option.treatment_id != tr.id or not option.is_active:
            abort(400)

    b, err = booking_service.book(
        tr, day, time_min, option=option, name=f.get("name", ""), phone=phone,
        email=f.get("email", ""), note=f.get("note", ""),
        guests=f.get("guests", type=int) or 1,
        therapist_id=f.get("therapist_id", type=int),
        area_id=f.get("area_id", type=int),
        service_address=f.get("service_address", ""),
        lang=lang(), payment_method=f.get("payment_method", "cash"))
    if err:
        flash(t().get(err, err))
        return redirect(url_for("spa.detail", slug=slug, day=day.isoformat(),
                                option=option.id if option else None))

    # Messaging is deliberately after the commit and cannot raise: the
    # booking exists and the guest sees it whatever the gateways do.
    notify_booking(b, current_app.config["SITE_URL"])
    # Straight to the manage link, so the guest lands on the page that
    # lets them change or cancel without contacting anyone.
    return redirect(b.manage_path() + "?new=1")


@bp.route("/booking/<code>")
def booking_view(code):
    """The short code, kept for links already sent.

    It is only eight hex characters, so it is guessable in a way the
    manage token is not. This page therefore shows the booking without
    the address or the therapist, and everything else lives behind the
    token link the guest received.
    """
    b = Booking.query.filter_by(public_code=code.upper()).first()
    if not b:
        abort(404)
    return render_template("spa/booking.html", b=b, noindex=True,
                           meta_title=f"Booking {b.public_code}", meta_desc="")


# --------------------------------------------------------- manage a booking

def _by_token(token):
    """The booking behind a manage link, or 404.

    An empty token must never be looked up: bookings created before the
    column existed are backfilled by the migration, but a blank string here
    would otherwise match whichever row happened to be blank.
    """
    token = (token or "").strip()
    if len(token) < 20:
        abort(404)
    b = Booking.query.filter_by(manage_token=token).first()
    if not b:
        abort(404)
    return b


def _manage_page(b, **extra):
    """The manage screen, with everything it needs to offer a change."""
    treatments = (Treatment.query.filter_by(is_active=True)
                  .order_by(Treatment.sort_order, Treatment.id).all())
    day = b.starts_at.date()
    raw = request.args.get("day")
    if raw:
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            pass
    step = int(SiteSetting.all_dict().get("slot_step_min") or 30)
    slots = booking_service.slots_for(b.treatment, day, option=b.option,
                                      step_min=step, exclude_id=b.id)
    return render_template(
        "spa/manage.html", b=b, treatments=treatments, slots=slots,
        day=day, noindex=True,
        areas=(ServiceArea.query.filter_by(is_active=True)
               .order_by(ServiceArea.sort_order, ServiceArea.name).all()),
        today=date.today().isoformat(),
        max_day=(date.today() + timedelta(days=BOOKING_DAYS_AHEAD)).isoformat(),
        meta_title=f"Booking {b.public_code}", meta_desc="", **extra)


@bp.route("/b/<token>")
def booking_manage(token):
    return _manage_page(_by_token(token))


@bp.route("/b/<token>/change", methods=["POST"])
def booking_change(token):
    """Service, duration, time, address and area — the things a guest may
    change themselves. Everything is re-checked server-side; the form is a
    convenience, not the rule."""
    b = _by_token(token)
    f = request.form

    treatment = b.treatment
    if f.get("treatment_id", type=int):
        treatment = db.session.get(Treatment, f.get("treatment_id", type=int))
        if not treatment or not treatment.is_active:
            abort(400)

    option = None
    if f.get("option_id", type=int):
        option = db.session.get(TreatmentOption, f.get("option_id", type=int))
        if not option or not option.is_active:
            abort(400)
        # Changing treatment and keeping the old treatment's option would
        # price the new service from the wrong menu row.
        if option.treatment_id != treatment.id:
            abort(400)

    day = time_min = None
    if f.get("day") and f.get("time_min"):
        try:
            day = date.fromisoformat(f["day"])
            time_min = int(f["time_min"])
        except (ValueError, KeyError):
            abort(400)

    updated, err = booking_service.amend(
        b, treatment=treatment, option=option, day=day, time_min=time_min,
        service_address=f.get("service_address"),
        area_id=f.get("area_id", type=int) if "area_id" in f else None,
        note=f.get("note"), by="customer")

    if err:
        flash(t().get(err, err))
        return redirect(b.manage_path())

    notify_service.notify_customer(updated, current_app.config["SITE_URL"],
                                   event="changed")
    notify_service.notify_admin(
        "✏️ Booking changed by the guest\n"
        + notify_service.booking_text(updated,
                                      current_app.config["SITE_URL"]),
        purpose="booking_changed")
    if updated.therapist:
        notify_service.notify_therapist(updated,
                                        current_app.config["SITE_URL"])
    flash(t()["booking_updated"])
    return redirect(updated.manage_path())


@bp.route("/b/<token>/cancel", methods=["POST"])
def booking_cancel(token):
    b = _by_token(token)
    updated, err = booking_service.cancel(b, by="customer")
    if err:
        flash(t().get(err, err))
        return redirect(b.manage_path())

    notify_service.notify_customer(updated, current_app.config["SITE_URL"],
                                   event="cancelled")
    notify_service.notify_admin(
        "❌ Booking cancelled by the guest\n"
        + notify_service.booking_text(updated,
                                      current_app.config["SITE_URL"]),
        purpose="booking_cancelled")
    if updated.therapist:
        notify_service.notify_therapist(updated,
                                        current_app.config["SITE_URL"])
    flash(t()["booking_cancelled"])
    return redirect(updated.manage_path())
