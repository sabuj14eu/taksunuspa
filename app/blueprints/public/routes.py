# -*- coding: utf-8 -*-
"""Home, CMS pages, contact."""
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)

from ...extensions import db
from ...i18n import lang, loc, t
from ...models.shop import Product
from ...models.site import ContactMessage, FaqItem, Page, SiteSetting
from ...models.spa import OpeningHour, Treatment
from ...services import media_service, seo_service
from ...services.booking_service import hhmm
from ...services.notify_service import telegram_admin

bp = Blueprint("public", __name__)

WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
           "Sunday"],
    "id": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
}
SCHEMA_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
               "Saturday", "Sunday"]


def opening_rows():
    """[(day name, "09:00 – 21:00" or None)] for the footer and contact page."""
    names = WEEKDAYS.get(lang(), WEEKDAYS["en"])
    rows = {h.weekday: h for h in OpeningHour.query.all()}
    out = []
    for wd in range(7):
        h = rows.get(wd)
        if h and not h.is_closed and h.open_min is not None:
            out.append((names[wd], f"{hhmm(h.open_min)} – {hhmm(h.close_min)}"))
        else:
            out.append((names[wd], None))
    return out


def opening_schema():
    """openingHoursSpecification for the DaySpa JSON-LD."""
    out = []
    for h in OpeningHour.query.order_by(OpeningHour.weekday).all():
        if h.is_closed or h.open_min is None:
            continue
        out.append({"@type": "OpeningHoursSpecification",
                    "dayOfWeek": SCHEMA_DAYS[h.weekday],
                    "opens": hhmm(h.open_min), "closes": hhmm(h.close_min)})
    return out


def spa_jsonld(site):
    return seo_service.jsonld_spa(
        name=site.get("company_name", "Taksu Nusa Spa"),
        url=current_app.config["SITE_URL"],
        image=(current_app.config["SITE_URL"] + site["og_image"]
               if site.get("og_image") else None),
        address=site.get("address"), city=site.get("city", "Bali"),
        postal=site.get("postal_code"), phone=site.get("phone"),
        lat=site.get("lat"), lng=site.get("lng"),
        price_range=site.get("price_range", "$$"),
        opening=opening_schema())


@bp.route("/")
def home():
    site = SiteSetting.all_dict()
    treatments = (Treatment.query.filter_by(is_active=True, is_featured=True)
                  .order_by(Treatment.sort_order, Treatment.id).limit(6).all())
    if not treatments:
        treatments = (Treatment.query.filter_by(is_active=True)
                      .order_by(Treatment.sort_order, Treatment.id)
                      .limit(6).all())
    products = (Product.query.filter_by(is_active=True, is_featured=True)
                .order_by(Product.sort_order, Product.id).limit(8).all())
    if not products:
        products = (Product.query.filter_by(is_active=True)
                    .order_by(Product.sort_order, Product.id).limit(8).all())

    title, desc = seo_service.meta_for(
        "home", lang(), brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"), seo_desc=site.get("meta_desc"))
    faqs = (FaqItem.query.filter_by(is_visible=True)
            .order_by(FaqItem.sort_order, FaqItem.id).all())
    return render_template(
        "home.html", meta_title=title, meta_desc=desc,
        treatments=treatments, products=products,
        product_covers=media_service.covers_for("product", [p.id for p in products]),
        treatment_covers=media_service.covers_for("treatment",
                                                  [x.id for x in treatments]),
        faqs=faqs, opening=opening_rows(),
        jsonld=spa_jsonld(site),
        jsonld_faq=seo_service.jsonld_faq(
            [(loc(f, "question"), loc(f, "answer")) for f in faqs]))


@bp.route("/p/<slug>")
def page(slug):
    p = Page.query.filter_by(slug=slug, is_visible=True).first()
    if not p:
        abort(404)
    title, desc = seo_service.meta_for(
        "page", lang(), name=loc(p, "title"), seo_title=p.seo_title,
        seo_desc=p.seo_desc)
    return render_template("page.html", p=p, meta_title=title, meta_desc=desc,
                           jsonld=seo_service.jsonld_breadcrumbs(
                               [("Home", current_app.config["SITE_URL"] + "/"),
                                (loc(p, "title"), None)]))


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    site = SiteSetting.all_dict()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        msg = request.form.get("message", "").strip()
        if not (phone and msg):
            flash("Please leave a phone number and a message."
                  if lang() == "en" else
                  "Mohon isi nomor telepon dan pesan Anda.")
            return redirect(url_for("public.contact"))
        db.session.add(ContactMessage(
            name=name[:80], phone=phone[:30],
            email=request.form.get("email", "")[:120], message=msg[:2000]))
        db.session.commit()
        telegram_admin(f"✉️ Message from {name or '-'} ({phone}): {msg[:200]}")
        flash(t()["message_sent"])
        return redirect(url_for("public.contact"))

    title, desc = seo_service.meta_for(
        "contact", lang(), brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"))
    return render_template("contact.html", meta_title=title, meta_desc=desc,
                           opening=opening_rows(), jsonld=spa_jsonld(site))
