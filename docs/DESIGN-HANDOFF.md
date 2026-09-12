# Design handoff — bringing a Lovable (or any) design into this site

The site works and is deployable. The look is deliberately plain, because it
is being replaced. This file is what makes that swap quick instead of a
rewrite: it says what to ask the designer for, and where each piece lands.

---

## 1. Prompt to paste into Lovable

Lovable builds a React/Vite front end from a written brief. Paste this, then
refine in their chat:

> Design a website for **Taksu Nusa Spa**, a Balinese day spa in Mengwi,
> Badung, Bali, that also sells its own line of pure Bali honey online.
>
> Feel: warm, calm, natural, premium but not cold. Think teak, raw linen,
> frangipani, honey amber, deep jungle green. Generous whitespace, large soft
> photography, a serif display face for headings and a clean sans for body
> text. Rounded corners, gentle shadows. It must feel Balinese, not like a
> generic clinic.
>
> Two audiences on equal footing: tourists booking a massage, and locals
> ordering honey for delivery.
>
> Build these pages:
> 1. **Home** — full-bleed hero with the spa name, one line of promise and two
>    buttons (Book a treatment / Shop our products). Then: featured treatments
>    as cards, featured products as cards, an about band, opening hours next
>    to contact details, and an FAQ accordion.
> 2. **Spa menu** — page title, a pill-style sub-menu of treatment groups
>    (Massage, Body Treatments, Facials, Packages), then a grid of treatment
>    cards showing photo, name, duration, and price with a struck-through old
>    price and a red sale badge when discounted.
> 3. **Treatment detail** — photo, name, duration, price, description, then a
>    booking panel: a date selector, an optional therapist selector, a grid of
>    selectable time chips, name/phone/email/guests fields, and a big submit
>    button.
> 4. **Our Product Line** — like the spa menu, but a sub-menu of product
>    groups (Honey, Spa Products, Gift Sets) over a 4-up product grid.
> 5. **Product detail** — large image with thumbnails, name, size (250 ml /
>    500 ml), price with sale treatment, stock status, quantity, Add to cart
>    and Buy now buttons, a WhatsApp order link, long description, and a
>    related-products row.
> 6. **Cart** and **Checkout** — line items, promo code, delivery-zone select,
>    totals panel, and four radio payment options: cash on delivery, cash at
>    the spa, bank transfer, online payment.
> 7. **Order / booking confirmation** — a centred card with a green tick, a
>    reference code, a summary table and a WhatsApp button.
> 8. **Contact** — hours table, address, map link, message form.
>
> Every page needs a header with the logo, nav (Home, Treatments, Our Product
> Line, Contact), a cart icon with a count badge, a phone number and an EN/ID
> language switch; a footer with four columns; a floating WhatsApp button; and
> an optional full-width promo bar above the header for a running discount.
>
> Design for mobile first — most visitors are on a phone.
>
> **Define every colour, font, radius and shadow as a CSS custom property on
> `:root`. Do not hardcode colours inside components.**

That last line matters most. This site is styled by tokens in
`app/static/css/app.css`, so a token-driven design drops straight in.

---

## 2. What to send back

Any one of these works. In order of how fast I can apply it:

1. **The Lovable GitHub repo link** (Lovable can push to GitHub) — best. I can
   read the components and port the design faithfully.
2. **A zip of the Lovable project**, or its `src/` folder.
3. **Per page: the rendered HTML plus the CSS.** Fine too, just slower.
4. **Screenshots only.** I can rebuild from these, but colours and spacing
   will be approximations.

Also send, if you have them: the logo (SVG preferred), the brand colours, the
font names, and the real photos of the spa and the honey bottles.

---

## 3. Where the design lands

Nothing about the database, prices, discounts, bookings or admin changes. The
swap touches presentation only:

| Design piece | File in this repo |
|---|---|
| Colours, fonts, radii, shadows | `app/static/css/app.css` — the `:root` block |
| All component styling | the rest of `app/static/css/app.css` |
| Header, footer, promo bar, WhatsApp button | `app/templates/base.html` |
| Product / treatment card, price + sale badge | `app/templates/_macros.html` |
| Home | `app/templates/home.html` |
| Spa menu, treatment page, booking confirmation | `app/templates/spa/` |
| Products, product page, cart, checkout, order | `app/templates/shop/` |
| Contact, CMS page, 404 | `app/templates/` |
| Admin panel | `app/templates/admin/` — leave as is unless you want it restyled |

**The one rule when editing templates:** keep the Jinja expressions
(`{{ ... }}` and `{% ... %}`) exactly as they are and change the HTML around
them. Those are what fill in real prices, discounts, stock and slots.

### Tokens the design should define

```css
:root{
  --green: …;      /* primary brand, buttons, footer   */
  --green-soft: …; /* focus rings, hovers              */
  --sand: …;       /* alternating section background   */
  --sand-2: …;     /* image placeholders, chips        */
  --gold: …;       /* accents, promo bar, cart badge   */
  --ink: …;        /* body text                        */
  --muted: …;      /* secondary text                   */
  --line: …;       /* borders                          */
  --danger: …;     /* sale badges, discounts           */
  --ok: …;         /* success states                   */
  --radius: …;     --shadow: …;     --maxw: …;
  --font-head: …;  --font-body: …;
}
```

Redefine those and most of the site re-skins itself before a single template
is touched — a useful first step to see the palette live.

---

## 4. Two things worth keeping

Whatever the new design does, these should survive:

- **The sale treatment.** Old price struck through, new price in the brand
  colour, a percentage badge on the card corner. It appears on products and
  treatments alike, and it is the main commercial lever in the admin panel.
- **Real URLs per item.** Each treatment, product and group has its own page
  for search engines. A design that collapses them into tabs or a lightbox
  would undo the SEO work.
