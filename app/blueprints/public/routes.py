# -*- coding: utf-8 -*-
"""Home, therapists, CMS pages, contact."""
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)

from ...extensions import db
from ...i18n import lang, loc, t
from ...models.media import MediaImage, Review
from ...models.shop import Product
from ...models.site import ContactMessage, FaqItem, Page, SiteSetting
from ...models.spa import (Highlight, OpeningHour, ServiceArea, Therapist,
                           Treatment)
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

TRUST_ITEMS = {
    "en": [("shield", "Certified therapists"),
           ("users", "Female & male therapists"),
           ("map-pin", "Hotel & villa service"),
           ("card", "Cash & online payment")],
    "id": [("shield", "Terapis bersertifikat"),
           ("users", "Terapis pria & wanita"),
           ("map-pin", "Layanan hotel & vila"),
           ("card", "Bayar tunai & online")],
}


def opening_rows():
    """[(day name, "09:00 – 23:00" or None)] for the footer and contact page."""
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
    out = []
    for h in OpeningHour.query.order_by(OpeningHour.weekday).all():
        if h.is_closed or h.open_min is None:
            continue
        out.append({"@type": "OpeningHoursSpecification",
                    "dayOfWeek": SCHEMA_DAYS[h.weekday],
                    "opens": hhmm(h.open_min), "closes": hhmm(h.close_min)})
    return out


def spa_jsonld(site):
    """DaySpa, with the areas served — the search signal that matters most
    for a business that travels to the guest rather than the other way round."""
    rating, count = media_service.rating_of("site", 0)
    areas = [a.name for a in ServiceArea.query.filter_by(is_active=True)
             .order_by(ServiceArea.sort_order).all()]
    extra = {}
    if areas:
        extra["areaServed"] = [{"@type": "Place", "name": n} for n in areas]
    return seo_service.jsonld_spa(
        name=site.get("company_name", "Taksu Nusa Spa"),
        url=current_app.config["SITE_URL"],
        image=(current_app.config["SITE_URL"] + site["og_image"]
               if site.get("og_image") else None),
        address=site.get("address"), city=site.get("city", "Bali"),
        postal=site.get("postal_code"), phone=site.get("phone"),
        lat=site.get("lat"), lng=site.get("lng"),
        price_range=site.get("price_range", "$$"),
        opening=opening_schema(), rating=rating, review_count=count,
        extra=extra)


@bp.route("/")
def home():
    site = SiteSetting.all_dict()

    treatments = (Treatment.query.filter_by(is_active=True, is_featured=True)
                  .order_by(Treatment.sort_order, Treatment.id).limit(4).all())
    if not treatments:
        treatments = (Treatment.query.filter_by(is_active=True)
                      .order_by(Treatment.sort_order, Treatment.id)
                      .limit(4).all())

    products = (Product.query.filter_by(is_active=True, is_featured=True)
                .order_by(Product.sort_order, Product.id).limit(4).all())
    if not products:
        products = (Product.query.filter_by(is_active=True)
                    .order_by(Product.sort_order, Product.id).limit(4).all())

    faqs = (FaqItem.query.filter_by(is_visible=True)
            .order_by(FaqItem.sort_order, FaqItem.id).all())

    title, desc = seo_service.meta_for(
        "home", lang(), brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"), seo_desc=site.get("meta_desc"))

    return render_template(
        "home.html", meta_title=title, meta_desc=desc,
        hero_image=site.get("hero_image") or media_service.cover_url("hero", 0),
        treatment_hero=media_service.cover_url("treatment_hero", 0),
        treatments=treatments, products=products,
        product_covers=media_service.covers_for("product",
                                                [p.id for p in products]),
        highlights=(Highlight.query.filter_by(is_visible=True)
                    .order_by(Highlight.sort_order, Highlight.id).all()),
        therapists=(Therapist.query.filter_by(is_active=True, show_on_site=True)
                    .order_by(Therapist.sort_order, Therapist.id).limit(2).all()),
        gallery_images=(MediaImage.query.filter_by(entity_type="gallery")
                        .order_by(MediaImage.sort_order, MediaImage.id)
                        .limit(6).all()),
        areas=(ServiceArea.query.filter_by(is_active=True)
               .order_by(ServiceArea.sort_order, ServiceArea.id).all()),
        reviews=(Review.query.filter_by(is_approved=True)
                 .order_by(Review.created_at.desc()).limit(3).all()),
        faqs=faqs, trust_items=TRUST_ITEMS.get(lang(), TRUST_ITEMS["en"]),
        jsonld=spa_jsonld(site),
        jsonld_faq=seo_service.jsonld_faq(
            [(loc(f, "question"), loc(f, "answer")) for f in faqs]))


@bp.route("/therapists")
def therapists():
    site = SiteSetting.all_dict()
    rows = (Therapist.query.filter_by(is_active=True, show_on_site=True)
            .order_by(Therapist.sort_order, Therapist.id).all())
    base = current_app.config["SITE_URL"]
    title, desc = seo_service.meta_for(
        "therapists", lang(), brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"))
    return render_template(
        "therapists.html", meta_title=title, meta_desc=desc, rows=rows,
        jsonld_crumbs=seo_service.jsonld_breadcrumbs(
            [(t()["home"], base + "/"), (t()["therapists"], None)]))


@bp.route("/gallery")
def gallery():
    """A real page, not an anchor. The home page only renders its gallery band
    when photos exist, so a "#gallery" link led nowhere on an empty site."""
    site = SiteSetting.all_dict()
    base = current_app.config["SITE_URL"]
    rows = (MediaImage.query.filter_by(entity_type="gallery")
            .order_by(MediaImage.sort_order, MediaImage.id).all())
    title, desc = seo_service.meta_for(
        "gallery", lang(), brand=site.get("company_name", "Taksu Nusa Spa"),
        city=site.get("city", "Bali"))
    return render_template(
        "gallery.html", meta_title=title, meta_desc=desc, rows=rows,
        jsonld_crumbs=seo_service.jsonld_breadcrumbs(
            [(t()["home"], base + "/"), (t()["gallery"], None)]))


@bp.route("/p/<slug>")
def page(slug):
    p = Page.query.filter_by(slug=slug, is_visible=True).first()
    if not p:
        abort(404)
    title, desc = seo_service.meta_for(
        "page", lang(), name=loc(p, "title"), seo_title=p.seo_title,
        seo_desc=p.seo_desc)
    return render_template("page.html", p=p, meta_title=title, meta_desc=desc,
                           jsonld_crumbs=seo_service.jsonld_breadcrumbs(
                               [(t()["home"], current_app.config["SITE_URL"] + "/"),
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
    return render_template(
        "contact.html", meta_title=title, meta_desc=desc,
        opening=opening_rows(), jsonld=spa_jsonld(site),
        areas=(ServiceArea.query.filter_by(is_active=True)
               .order_by(ServiceArea.sort_order).all()))
