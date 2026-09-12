# -*- coding: utf-8 -*-
"""SEO layer: slugs, meta titles, JSON-LD, 301s.

Search engines are the whole reason the product pages exist as real URLs
instead of a lightbox, so every listable thing gets its own path, its own
title and description, and structured data Google can lift into a rich
result — Product with an Offer and a price, DaySpa with an address.
"""
import json
import re
import unicodedata
from datetime import date


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-") or "item"


def unique_slug(model, text: str, ignore_id=None) -> str:
    """Append -2, -3 ... until the slug is free."""
    base = slugify(text)
    slug, n = base, 1
    while True:
        row = model.query.filter_by(slug=slug).first()
        if not row or (ignore_id and row.id == ignore_id):
            return slug
        n += 1
        slug = f"{base}-{n}"


def record_redirect(old_path: str, new_path: str):
    from ..extensions import db
    from ..models.shared import Redirect
    if not old_path or old_path == new_path:
        return
    r = Redirect.query.filter_by(old_path=old_path).first()
    if r:
        r.new_path = new_path
    else:
        db.session.add(Redirect(old_path=old_path, new_path=new_path))
    # A chain that pointed at the old path now points at the new one.
    Redirect.query.filter_by(new_path=old_path).update({"new_path": new_path})


# ---------- meta ----------

def meta_for(kind: str, lang="en", **kw):
    """(title, description). An admin-set seo_title always wins."""
    if kw.get("seo_title"):
        return kw["seo_title"], (kw.get("seo_desc") or "")[:160]

    year = date.today().year
    name = kw.get("name", "")
    brand = kw.get("brand", "Taksu Nusa Spa")
    group = kw.get("group", "")
    price = kw.get("price", "")
    city = kw.get("city", "Bali")

    if lang == "id":
        titles = {
            "home": f"{brand} — Spa & Pijat di {city} | Booking Online",
            "treatments": f"Menu Spa & Harga Pijat {city} {year} | {brand}",
            "treatment": f"{name} — Pijat & Spa {city} | {brand}",
            "products": f"Produk Kami — Madu Asli Bali & Produk Spa | {brand}",
            "product_group": f"{name} — Produk Alami Bali | {brand}",
            "product": f"{name} {price} — Kirim ke Seluruh {city} | {brand}",
            "contact": f"Kontak & Lokasi — {brand}, {city}",
        }
        default_desc = {
            "product": f"{name} asli, tanpa gula tambahan. Pesan online, "
                       f"bayar tunai saat pengiriman atau transfer.",
            "treatment": f"{name} di {brand}. Booking online, terapis "
                         f"berpengalaman, harga jelas.",
        }
    else:
        titles = {
            "home": f"{brand} — Balinese Spa & Massage in {city} | Book Online",
            "treatments": f"Spa Menu & Massage Prices {city} {year} | {brand}",
            "treatment": f"{name} — Massage & Spa in {city} | {brand}",
            "products": f"Our Product Line — Pure Bali Honey & Spa Products | {brand}",
            "product_group": f"{name} — Natural Bali Products | {brand}",
            "product": f"{name} {price} — Delivered Across {city} | {brand}",
            "contact": f"Contact & Location — {brand}, {city}",
        }
        default_desc = {
            "product": f"{name} — 100% natural, no added sugar. Order online, "
                       f"pay cash on delivery or by transfer. Delivery across {city}.",
            "treatment": f"Book {name} at {brand}. Online booking, experienced "
                         f"therapists, clear pricing.",
        }

    title = titles.get(kind) or (f"{name} | {brand}" if name else brand)
    desc = kw.get("seo_desc") or kw.get("short") or default_desc.get(kind, "")
    if group and desc and len(desc) < 110:
        desc = f"{desc} {group}."
    return title[:180], (desc or "")[:160]


# ---------- JSON-LD ----------

def jsonld_spa(*, name, url, image=None, address=None, city="Bali",
               postal=None, phone=None, lat=None, lng=None, price_range=None,
               opening=None, rating=None, review_count=0):
    data = {"@context": "https://schema.org", "@type": "DaySpa",
            "name": name, "url": url}
    if image:
        data["image"] = image
    if address or city:
        data["address"] = {"@type": "PostalAddress",
                           "streetAddress": address or "",
                           "addressLocality": city or "",
                           "postalCode": postal or "",
                           "addressCountry": "ID"}
    if lat and lng:
        data["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}
    if phone:
        data["telephone"] = phone
    if price_range:
        data["priceRange"] = price_range
    if opening:
        data["openingHoursSpecification"] = opening
    # Only with real reviews — Google penalises invented ratings.
    if rating and review_count >= 1:
        data["aggregateRating"] = {"@type": "AggregateRating",
                                   "ratingValue": rating, "bestRating": 5,
                                   "reviewCount": review_count}
    return json.dumps(data, ensure_ascii=False)


def jsonld_product(*, name, url, price_idr, image=None, description=None,
                   sku=None, brand=None, in_stock=True):
    data = {"@context": "https://schema.org", "@type": "Product",
            "name": name, "url": url,
            "offers": {"@type": "Offer", "price": str(int(price_idr or 0)),
                       "priceCurrency": "IDR", "url": url,
                       "availability": "https://schema.org/InStock" if in_stock
                       else "https://schema.org/OutOfStock"}}
    if image:
        data["image"] = image
    if description:
        data["description"] = description[:400]
    if sku:
        data["sku"] = sku
    if brand:
        data["brand"] = {"@type": "Brand", "name": brand}
    return json.dumps(data, ensure_ascii=False)


def jsonld_service(*, name, url, price_idr, provider, description=None,
                   duration_min=None):
    data = {"@context": "https://schema.org", "@type": "Service",
            "name": name, "url": url,
            "provider": {"@type": "DaySpa", "name": provider},
            "offers": {"@type": "Offer", "price": str(int(price_idr or 0)),
                       "priceCurrency": "IDR", "url": url}}
    if description:
        data["description"] = description[:400]
    if duration_min:
        data["termsOfService"] = f"{duration_min} minutes"
    return json.dumps(data, ensure_ascii=False)


def jsonld_breadcrumbs(items):
    """items: [(name, url), ...]"""
    return json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             **({"item": u} if u else {})}
            for i, (n, u) in enumerate(items)]}, ensure_ascii=False)


def jsonld_faq(pairs):
    pairs = [(q, a) for q, a in pairs if q and a]
    if not pairs:
        return ""
    return json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in pairs]}, ensure_ascii=False)
