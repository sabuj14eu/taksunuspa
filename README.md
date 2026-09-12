# Taksu Nusa Spa — taksunusaspa.com

The spa's own website: treatment menu with online booking, a product line
(Bali honey) that customers can order and have delivered, one discount system
covering both, and an admin panel the owner runs without a developer.

Extracted from the SPA & Wellness vertical of `LokalnyDowoz-project` and
rebuilt as a single-venue Bali site: Indonesian rupiah instead of złoty,
English + Indonesian instead of Polish, one spa instead of a marketplace.

## What it does

**Public site**
- Home with featured treatments, featured products, opening hours and FAQ
- `/treatments` — spa menu with a sub-menu across treatment groups
- `/treatment/<slug>` — one page per treatment, with date/therapist/time booking
- `/products` — Our Product Line, with a sub-menu across product groups
- `/product/<slug>` — one page per product, add to cart or order by WhatsApp
- `/cart`, `/checkout` — delivery address, promo code, four payment methods
- `/contact` — hours, map link, message form
- English and Indonesian throughout, switchable in the header

**Payments** — cash on delivery, cash at the spa, bank transfer, or an online
payment link. The order records the method and a separate payment status, so
the owner can mark an order paid when the transfer lands.

**Admin** (`/admin`, sign in at `/login`)
- Products, product groups, stock, photos
- Treatments, treatment groups, duration, prices
- **Discounts** — one screen covering everything, one group, or a single item.
  Products *and* spa treatments. An automatic discount shows the old price
  struck through on every card, page and cart line; give it a code instead and
  it waits for the customer to type it at checkout.
- Orders with status and payment tracking, and an event history
- Bookings, opening hours, holiday closures, therapists
- Delivery zones with a flat fee and a free-over threshold
- Pages, menu, FAQ, photo library, reviews, site settings

**SEO**
- A real URL per treatment, product and group — the thing a tabbed single page
  cannot give you
- `sitemap.xml` and `robots.txt` generated from what is actually published
- Per-item SEO title and description, auto-generated when left blank
- JSON-LD: DaySpa with address and opening hours, Product with price and
  availability, Service per treatment, breadcrumbs, FAQ
- Canonical and hreflang tags, Open Graph, first-party pageview counter
- Renaming anything in admin leaves a 301 behind, so ranked URLs never 404
- Uploads are converted to WebP with thumbnails, which keeps the page-speed
  score that the rest of this work depends on

## Run it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then edit: SECRET_KEY at minimum
export FLASK_DEBUG=1 SESSION_COOKIE_SECURE=false

python -m scripts.seed        # tables + starting content; prints the admin password
python run.py                 # http://127.0.0.1:5200
```

`scripts/seed.py` is safe to re-run — it matches rows on slug and updates them
rather than creating duplicates.

## Layout

```
app/
  __init__.py          app factory, context processor, SEO middleware
  config.py            environment configuration
  i18n.py              English/Indonesian UI strings, loc() helper
  money.py             rupiah formatting and parsing
  models/              user, site, spa, shop, discount, media, shared
  services/
    pricing_service    the one place that decides what anything costs
    booking_service    opening hours -> slots -> therapist -> booking
    shop_service       cart, totals, order placement
    seo_service        slugs, meta, JSON-LD, 301s
    media_service      WebP uploads, galleries, ratings
    notify_service     Telegram alerts, WhatsApp links
  blueprints/          auth, public, spa, shop, admin, seo
  templates/           base + public pages + admin/
  static/css/app.css   interim stylesheet, all tokens in :root
scripts/
  seed.py              starting content and the first admin user
  migrate.py           create_all plus additive ALTER TABLE
```

## Notes before going live

- **Prices in the seed are placeholders.** Set the real treatment and product
  prices in admin.
- **Upload the real product photos** in Admin → Photos. The honey bottle shots
  are not in the repository.
- **Set the bank transfer details** in Admin → Site settings; they appear at
  checkout and on the order confirmation.
- `SECRET_KEY` has no production fallback — the app refuses to start without
  it, on purpose. Generate one with `openssl rand -hex 32`.
- Change the seeded admin password immediately in Admin → My account.

Deployment and update commands: see [DEPLOY.md](DEPLOY.md).
