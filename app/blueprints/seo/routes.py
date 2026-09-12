# -*- coding: utf-8 -*-
"""sitemap.xml and robots.txt, generated from what is actually published.

Both are built on request rather than kept as files, so a product added in
admin is in the sitemap the moment it goes live — no regeneration step to
forget.
"""
from datetime import date

from flask import Blueprint, Response, current_app

from ...models.shop import Product, ProductGroup
from ...models.site import Page
from ...models.spa import Treatment, TreatmentCategory

bp = Blueprint("seo", __name__)


def _url(loc, changefreq="weekly", priority="0.7", lastmod=None):
    parts = [f"<loc>{loc}</loc>"]
    if lastmod:
        parts.append(f"<lastmod>{lastmod}</lastmod>")
    parts.append(f"<changefreq>{changefreq}</changefreq>")
    parts.append(f"<priority>{priority}</priority>")
    return "<url>" + "".join(parts) + "</url>"


@bp.route("/sitemap.xml")
def sitemap():
    base = current_app.config["SITE_URL"]
    today = date.today().isoformat()
    out = [
        _url(f"{base}/", "daily", "1.0", today),
        _url(f"{base}/treatments", "weekly", "0.9", today),
        _url(f"{base}/products", "daily", "0.9", today),
        _url(f"{base}/therapists", "weekly", "0.6"),
        _url(f"{base}/contact", "monthly", "0.5"),
    ]
    for c in (TreatmentCategory.query.filter_by(is_active=True)
              .order_by(TreatmentCategory.sort_order).all()):
        out.append(_url(f"{base}/treatments/{c.slug}", "weekly", "0.8"))
    for tr in (Treatment.query.filter_by(is_active=True)
               .order_by(Treatment.sort_order).all()):
        out.append(_url(f"{base}/treatment/{tr.slug}", "weekly", "0.8"))
    for g in (ProductGroup.query.filter_by(is_active=True)
              .order_by(ProductGroup.sort_order).all()):
        out.append(_url(f"{base}/products/{g.slug}", "weekly", "0.8"))
    for p in (Product.query.filter_by(is_active=True)
              .order_by(Product.sort_order).all()):
        out.append(_url(f"{base}/product/{p.slug}", "weekly", "0.8"))
    for pg in Page.query.filter_by(is_visible=True).all():
        out.append(_url(f"{base}/p/{pg.slug}", "monthly", "0.4"))

    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + "".join(out) + "</urlset>")
    return Response(xml, mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    base = current_app.config["SITE_URL"]
    body = ("User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /cart\n"
            "Disallow: /checkout\n"
            "Disallow: /order/\n"
            "Disallow: /booking/\n"
            "Disallow: /login\n\n"
            f"Sitemap: {base}/sitemap.xml\n")
    return Response(body, mimetype="text/plain")
