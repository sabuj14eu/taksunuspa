# Taksu Nusa Spa — taksunusaspa.com

A Balinese **home spa**: therapists travel to the guest's villa, hotel or home
anywhere in Bali. The site takes bookings for that, sells the spa's own product
line (Bali honey) for delivery, runs one discount system across both, and hands
the owner an admin panel they can work without a developer.

Extracted from the SPA & Wellness vertical of `LokalnyDowoz-project` and rebuilt
for Bali: rupiah instead of złoty, English + Indonesian instead of Polish, one
travelling spa instead of a venue marketplace.

The look follows the approved Lovable redesign — Playfair Display over
Montserrat, deep botanical green, cream, sand and brass, with the same tokens
the design defined.

## What it does

**Public site**
- Home: hero, trust bar, treatment menu with duration pricing, "why guests
  choose us", therapists, gallery, product line, areas covered, guest reviews,
  booking CTA and FAQ
- `/treatments` — the menu, with a sub-menu across treatment groups
- `/treatment/<slug>` — one page per treatment: pick a duration, a day, a
  therapist and a time, then give the address we should come to
- `/therapists` — the team, with availability
- `/products` — Our Product Line, with a sub-menu across product groups
- `/product/<slug>` — one page per product, add to cart or order by WhatsApp
- `/cart`, `/checkout` — delivery address, promo code, four payment methods
- `/contact` — hours, service areas, map link, message form
- English and Indonesian throughout, switchable in the header

**Multi-duration pricing** — a treatment carries duration tiers (60 / 90 / 120
minutes), each with its own price, shown side by side the way the menu reads.
A discount on the treatment marks every tier at once.

**We come to you** — bookings capture a service area and a service address, and
the booking engine leaves a travel gap between a therapist's jobs so they can
actually get there. Areas can carry a travel fee; zero shows as free travel.

**Payments** — treatments: cash to the therapist, bank transfer or an online
link. Products: cash on delivery, cash on collection, transfer or online. Both
record the method and a separate payment status, so the owner can mark
something paid when the transfer lands.

**Admin** (`/admin`, sign in at `/login`)
- Products, product groups, stock, photos
- Treatments and their duration tiers, treatment groups
- Therapists — photo, role, languages, "available today", bookable or not
- Service areas with travel fees
- **Discounts** — one screen covering everything, one group, or a single item.
  Products *and* spa treatments. An automatic discount shows the old price
  struck through on every card, page and cart line; give it a code instead and
  it waits for the customer to type it at checkout.
- Orders with status and payment tracking, and an event history
- Bookings, service hours, holiday closures
- Delivery zones with a flat fee and a free-over threshold
- "Why guests choose us" tiles, pages, menu, FAQ, photo library (including the
  home hero and gallery), reviews, and all the home-page copy in site settings

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
    booking_service    service hours -> slots -> free therapist -> booking
    shop_service       cart, totals, order placement
    seo_service        slugs, meta, JSON-LD, 301s
    media_service      WebP uploads, galleries, ratings
    notify_service     Telegram alerts, WhatsApp links
  blueprints/          auth, public, spa, shop, admin, seo
  templates/           base + _macros + _icons + public pages + admin/
  static/css/app.css   the design system; every colour and font is a token
                       on :root, so a palette change is a few lines
scripts/
  seed.py              starting content and the first admin user
  migrate.py           create_all plus additive ALTER TABLE
```

## Notes before going live

- **Photos are not in the repository** — the redesign's images live in Lovable
  and never came across as files. Upload them in Admin → Photos: the home hero,
  the gallery row, therapist portraits, treatment and product shots. Until the
  hero is uploaded the home page falls back to a botanical gradient, which is
  presentable but not the intended look.
- **Treatment prices are the real menu** (Balinese 300/400/550k, Deep Tissue
  350/450k, Couple 300/400k per person, Foot 250k) carried over from the live
  site. **Product prices are placeholders** — confirm them in admin.
- **The launch discount is seeded switched off.** The redesign showed 250.000
  against a struck-through 300.000, which is a 50.000 rupiah offer on
  treatments. Turn it on in Admin → Discounts when the promo runs.
- **Two different phone numbers** are in play: the spa's WhatsApp
  (+62 812-3672-9448, from the redesign) is seeded as the site contact; the
  honey producer's number (+62 823-3956-6156) is not. Check which belongs where.
- **Set the bank transfer details** in Admin → Site settings; they appear at
  checkout and on the order confirmation.
- `SECRET_KEY` has no production fallback — the app refuses to start without
  it, on purpose. Generate one with `openssl rand -hex 32`.
- Change the seeded admin password immediately in Admin → My account.

Deployment and update commands: see [DEPLOY.md](DEPLOY.md).
