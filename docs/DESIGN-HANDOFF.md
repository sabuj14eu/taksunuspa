# Design — where it came from and how to change it

The approved Lovable redesign (`sabuj14eu/eye-catching-site-makeover`) has been
applied. This file records what was taken from it, what could not be taken, and
how to change the look again later.

---

## What was applied

**Tokens, verbatim.** The design's colours are oklch values on `:root` in
`app/static/css/app.css`, copied exactly so the palette matches:

| Token | Role |
|---|---|
| `--primary` | deep botanical green — buttons, headings accent, dark bands |
| `--forest` | darker green — the "areas we cover" band, admin sidebar |
| `--background` / `--ivory` | warm cream page and header |
| `--sand` / `--secondary` | alternating sections, duration chips |
| `--clay` | the letterspaced eyebrow labels |
| `--brass` | stars, promo bar, accents on dark |
| `--destructive` | sale badges and struck-through savings |

Type is Playfair Display (display) over Montserrat (body), the pairing the
design specified, loaded from Google Fonts.

**Components**, ported from the Tailwind classes to plain CSS: the sticky
translucent header with the TN mark and letterspaced nav, the eyebrow-with-rule
label, pill buttons in five variants, the hero with its double gradient wash,
the trust bar, treatment rows with duration chips, the dark-green tile grid,
therapist cards, the gallery, area pills, review cards, the CTA band with its
blurred brass orbs, and the four-column footer.

**Structure.** The design's single landing page became the home page, and its
sections are now real data: treatments and their duration tiers, therapists,
service areas, "why guests choose us" tiles, gallery images and reviews all come
from the database and are editable in admin.

**The business model.** The redesign made clear this is a travelling home spa,
not a venue. That shaped the schema: bookings capture a service address and an
area, the slot engine leaves a travel gap between a therapist's jobs, and the
JSON-LD advertises `areaServed` rather than a single address.

## What could not be applied

**The photography.** The Lovable repo ships `.asset.json` pointers into their
preview host, not image files, so there is nothing to copy. Every image slot
falls back gracefully — the hero to a botanical gradient, cards to a tinted
placeholder — and the real photos go in through Admin → Photos:

| Upload as | Where it appears |
|---|---|
| Home page hero | behind the home headline |
| Home page gallery | the three-up row |
| Treatments section image | beside the home treatment list |
| A therapist | that therapist's card |
| A treatment / a product | that item's page and cards |

To get the originals: open the Lovable preview, right-click each image and save
it, then upload. Or use the spa's own photos, which will suit better anyway.

**The React app itself.** Lovable builds React + Vite + Tailwind + shadcn/ui;
this site is Flask with Jinja templates and a real database behind it. Keeping
their front end would have meant rebuilding the booking engine, the shop and the
admin panel as an API plus a separate client. Porting the design instead kept
every working part and cost only the templates.

---

## Changing the look again

**A palette or type change** is the `:root` block in `app/static/css/app.css`
and nothing else. Redefine the tokens and the whole site follows.

**A layout change** is the templates:

| Piece | File |
|---|---|
| Header, footer, promo bar, mobile menu | `app/templates/base.html` |
| Icons | `app/templates/_icons.html` |
| Price rendering, sale badges, cards, duration chips | `app/templates/_macros.html` |
| Home page sections | `app/templates/home.html` |
| Treatment menu, treatment page, booking confirmation | `app/templates/spa/` |
| Products, product page, cart, checkout, order | `app/templates/shop/` |
| Therapists, contact, CMS page, 404 | `app/templates/` |
| Admin | `app/templates/admin/` |

**The one rule:** keep the Jinja expressions (`{{ ... }}`, `{% ... %}`) and
change the HTML around them. Those are what fill in live prices, discounts,
stock, slots and translations.

**Copy** does not need a developer at all. Every headline, eyebrow label and
intro paragraph on the home page is in Admin → Site settings, in both languages.

## Two things worth keeping

Whatever changes next, these earn their place:

- **The sale treatment.** Old price struck through, new price in the brand
  colour, a percentage badge on the corner — identical on a jar of honey and on
  a 90-minute massage. It is the main commercial lever in the admin panel, and
  it only works because one function prices everything.
- **A real URL per item.** Each treatment, product and group has its own page.
  A design that collapsed them into tabs or a lightbox would quietly undo the
  SEO work.
