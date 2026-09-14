"""The English copy for the whole site, in one place.

Two things read this: scripts/seed.py, so a brand-new database starts with the
right wording, and scripts/apply_copy.py, which pushes the same wording onto a
database that is already live. Editing the text here and running apply_copy is
the whole workflow — there is no second copy of these sentences to forget.

The wording below is the owner's own, supplied verbatim. Rules it follows:
  * Taksu Nusa Spa is a home spa. The therapist comes to the guest.
  * The service covers eight named areas, not the island. Nothing may say
    "Bali-wide", "across Bali", "anywhere in Bali" or "wherever you are in
    Bali" — the phrase is "Serving selected areas of Bali."
  * There is no travel fee inside those areas. Never "free travel".
  * Couple Massage is priced per person, and that must be impossible to miss.
  * No medical claims, for treatments or for honey.
  * Nothing invented: no certifications, no reviews, no guest numbers, no
    services the spa does not offer.
"""

# The eight areas, in the owner's order. Everything that prints the areas
# builds its string from here, so the list cannot drift between pages.
AREAS = ["Seminyak", "Ubud", "Kuta", "Legian", "Sanur", "Nusa Dua",
         "Jimbaran", "Uluwatu"]
AREAS_LINE = " · ".join(AREAS)

OPENING_HOURS = "Daily · 09:00–23:00"
NO_TRAVEL_FEE = "No travel fee within our service areas."
NO_TRAVEL_FEE_SINGULAR = "No travel fee within our service area."
SELECTED_AREAS = "Serving selected areas of Bali."
WHATSAPP_DISPLAY = "+62 812-3672-9448"

POSITIONING = ("Professional Balinese home spa treatments delivered to your "
               "hotel, villa or home.")

OUTSIDE_AREAS = ("Staying outside our standard service areas? Contact us on "
                 "WhatsApp and we will check availability.")

# ---------------------------------------------------------------- settings

SETTINGS_EN = {
    # hero
    "hero_eyebrow_en": SELECTED_AREAS,
    "hero_line1_en": "Bali Premium",
    "hero_line2_en": "Home Spa",
    "tagline_en": (
        "Authentic Balinese massage and wellness treatments, delivered "
        "directly to your hotel, villa or home.\n\n"
        "Relax in complete privacy while our experienced therapists bring the "
        "spa experience directly to you."),

    # The rating line is only shown when the owner sets rating_value. It is
    # left empty because "4.9 · 1000+ happy guests" could not be evidenced.
    "rating_value": "",
    "rating_note_en": "",

    "about_en": (
        "Taksu Nusa Spa was created to make it easier for guests in Bali to "
        "enjoy a relaxing and authentic spa experience without leaving their "
        "accommodation. Instead of travelling to a spa, our therapists come "
        "directly to your hotel, villa, guesthouse or home."),

    "service_hours": OPENING_HOURS,
    "service_scope": SELECTED_AREAS,

    "treatments_eyebrow_en": "Traditional Techniques & Personalised Care",
    "treatments_intro_en": (
        "Authentic Balinese massage and wellness treatments, delivered "
        "directly to your hotel, villa or home."),

    "experience_eyebrow_en": "Why choose us",
    "experience_title_en": "Why Choose Us",

    "therapists_eyebrow_en": "Meet Our Therapists",
    "therapists_title_en": "Meet Our Therapists",
    "therapists_intro_en": (
        "Our therapists are experienced professionals who are passionate "
        "about providing a relaxing, comfortable and personalised Balinese "
        "spa experience. Our therapists come directly to your hotel, villa or "
        "home within our service areas."),

    "gallery_eyebrow_en": "A look inside",
    "products_eyebrow_en": "Take a Little Bali Home",

    "areas_note_en": (
        "No need to travel to a spa. Our therapists come directly to your "
        f"hotel, villa, guesthouse or home.\n{NO_TRAVEL_FEE}"),

    "reviews_eyebrow_en": "What guests say",
    "reviews_title_en": "Guest reviews",

    "cta_eyebrow_en": "Booking takes a minute",
    "cta_title_en": "Book Your Treatment",
    "cta_text_en": (
        "Choose your treatment and a time that suits you, and your therapist "
        "will arrive with everything needed."),

    "meta_desc": (
        f"{POSITIONING} {SELECTED_AREAS} Serving {AREAS_LINE}. Book online or "
        f"on WhatsApp."),

    "footer_note_en": POSITIONING,
}

# ------------------------------------------------------------- treatments

TREATMENT_GROUP_DESC_EN = {
    "massage": ("Traditional Balinese massage given in the comfort and "
                "privacy of your own accommodation."),
    "body-treatment": ("Scrubs, masks and flower baths made from island "
                       "ingredients."),
    "packages": "Longer combinations for couples and half-day escapes.",
}

TREATMENT_DESC_EN = {
    "balinese-massage":
        "A traditional full-body massage combining flowing strokes, palm "
        "pressure and aromatic oils. Designed to ease everyday muscle "
        "tension, calm the mind and promote deep relaxation.",

    "deep-tissue-massage":
        "A firm and focused massage designed to target areas of muscle "
        "tension and stiffness. A great choice after surfing, exercise, long "
        "walks or a long journey.",

    "couple-massage":
        "Enjoy a relaxing massage together in the privacy of your hotel room, "
        "villa or home. Two therapists provide the treatment at the same time "
        "so you can relax together.\n\n"
        "Important: price is per person.",

    "foot-massage":
        "A relaxing treatment focusing on the feet and lower legs using "
        "gentle pressure-point techniques and soothing oils. Perfect for "
        "tired feet after a day of walking or exploring Bali.",
}

# --------------------------------------------------------------- products

PRODUCT_GROUP_DESC_EN = {
    "honey": ("Discover our selection of locally produced Bali honey and "
              "wellness products. Perfect for enjoying at home or taking a "
              "little taste of Bali with you."),
    "spa-products": "The oils and balms we use during our treatments.",
    "gift-sets": "Honey and wellness products boxed together, ready to give.",
}

# slug -> (short line under the name, full description)
PRODUCT_COPY_EN = {
    "madu-kela-kela-250ml": (
        "Raw liquid Bali honey with a light, sweet-sour taste. 250 ml.",
        "Madu Kela Kela is the liquid honey in our Sari Madu Sedana range, "
        "produced locally here in Bali from stingless bees. It pours easily "
        "and has a light, sweet-sour taste that is distinctive of "
        "stingless-bee honey.\n\n"
        "Raw and unheated, with no added sugar and nothing else in the "
        "bottle.\n\n"
        "Enjoy it straight from the spoon, stirred into warm water, or over "
        "yoghurt and fruit."),

    "madu-kela-kela-500ml": (
        "The larger bottle of our raw liquid Bali honey. 500 ml.",
        "The 500 ml bottle of Madu Kela Kela — the same raw liquid honey with "
        "the same light, sweet-sour taste, in the size our regular customers "
        "return for.\n\n"
        "Raw and unheated, with no added sugar.\n\n"
        "Store it in a cupboard rather than the fridge, and use a dry spoon."),

    "madu-nyawan-500ml": (
        "Thick, richly sweet Bali honey. 500 ml.",
        "Madu Nyawan is the thick honey in our Sari Madu Sedana range: dense, "
        "slow off the spoon, and noticeably sweet rather than sour.\n\n"
        "Raw and unheated, with no added sugar.\n\n"
        "A good choice if you find stingless-bee honey a little sharp. Lovely "
        "on warm toast or stirred into tea."),
}

# ------------------------------------------------------------- highlights

# (match on the existing English title, new icon, new title, new text)
HIGHLIGHTS_EN = [
    ("Certified therapists", "🌿", "Experienced Professional Therapists",
     "Our experienced therapists provide professional and personalised "
     "massage treatments with care, respect and attention to your comfort."),
    ("Organic botanicals", "👥", "Female & Male Therapists",
     "Choose a female or male therapist according to your preference and "
     "availability."),
    ("Private & discreet", "🏡", "Hotel & Villa Service",
     "Enjoy your treatment in the comfort and privacy of your hotel room, "
     "villa, guesthouse or home."),
    ("Full spa ritual", "✨", "Traditional Balinese Techniques",
     "Experience traditional Balinese massage techniques designed to help you "
     "relax, release everyday tension and feel refreshed."),
    ("Fresh linens", "💧", "Quality Massage Oils",
     "We use carefully selected massage oils to create a comfortable and "
     "relaxing treatment experience."),
    ("Hygienic & safe", "💳", "Flexible Payment",
     "Payment is available by cash after the treatment, bank transfer or "
     "online payment."),
]

# ----------------------------------------------------------- how it works

HOW_IT_WORKS_EN = [
    ("Book Your Treatment",
     "Choose your treatment, preferred date and time."),
    ("Your Therapist Arrives",
     "We bring the massage table, fresh towels, oils and everything needed "
     "for your treatment."),
    ("Relax & Enjoy",
     "Enjoy your treatment in the comfort and privacy of your own space. "
     "Payment can be made after the treatment."),
]

# -------------------------------------------------------------------- FAQ

# Matched on the old question so an existing row is updated rather than
# duplicated. (old question or sentinel, new question, new answer)
FAQ_EN = [
    ("Do you come to my hotel or villa?",
     "Do you come to my hotel or villa?",
     "Yes. Our therapists come directly to your hotel, villa, guesthouse or "
     "private home within our service areas."),

    ("__no_spa__",
     "Do I need to travel to a spa?",
     "No. Taksu Nusa Spa is a home spa service. We bring the spa experience "
     "directly to you."),

    ("__table__",
     "Do you provide the massage table?",
     "Yes. Our therapist brings the massage table and essential equipment."),

    ("How do I pay?", "How do I pay?",
     "You can pay in cash after your treatment, by bank transfer or through "
     "an online payment link."),

    ("How far ahead should I book?",
     "How far in advance should I book?",
     "We recommend booking at least two hours in advance. Evening, weekend "
     "and holiday bookings may fill up quickly."),

    ("__gender__",
     "Can I request a male or female therapist?",
     "Yes. Please tell us your preference when booking. Requests are subject "
     "to availability."),

    ("__specific__",
     "Can I request a specific therapist?",
     "Yes. You may request a preferred therapist, subject to availability."),

    ("__couple__",
     "Is the Couple Massage price for two people?",
     "No. The listed Couple Massage price is per person."),

    ("__areas__",
     "What areas do you serve?",
     f"{AREAS_LINE}.\n\nGuests outside these areas can contact us on WhatsApp "
     f"to check availability."),

    ("__hours__",
     "What time are you open?",
     OPENING_HOURS),

    ("Is the honey pure?", "Is the honey pure?",
     "Yes — raw honey with no added sugar and nothing heated. It is produced "
     "locally under the Sari Madu Sedana label, business number "
     "9120014231404."),
]

# ------------------------------------------------------------------ pages

PAGES_EN = {
    "about": (
        "About Taksu Nusa Spa",
        "## Bringing the Balinese Spa Experience to You\n"
        "Taksu Nusa Spa was created to make it easier for guests in Bali to "
        "enjoy a relaxing and authentic spa experience without leaving their "
        "accommodation.\n\n"
        "Instead of travelling to a spa, our therapists come directly to your "
        "hotel, villa, guesthouse or home.\n\n"

        "## Our Philosophy\n"
        "We believe relaxation should feel simple, comfortable and "
        "personal.\n\n"
        "Our treatments are inspired by traditional Balinese massage "
        "techniques and are designed to help you slow down, release everyday "
        "tension and enjoy a moment of calm during your stay in Bali.\n\n"

        "## Personalised Care\n"
        "Every guest is different. That is why our therapists adapt the "
        "pressure and pace of the treatment to your comfort and "
        "preference.\n\n"
        "Whether you are recovering after a long flight, relaxing after a day "
        "of sightseeing, unwinding after surfing or simply looking for a "
        "peaceful moment, we aim to make your experience comfortable from "
        "beginning to end.\n\n"

        "## Your Privacy Matters\n"
        "Your treatment takes place in the comfort of your own accommodation, "
        "giving you a private and relaxing experience without the crowds or "
        "distractions of a busy spa.\n\n"

        "## We Bring Everything to You\n"
        "Our therapists arrive with the essential equipment needed for your "
        "treatment, including the massage table, fresh towels and massage "
        "oils.\n\n"
        "All you need to do is relax.\n\n"

        "## Experience Bali, Your Way\n"
        "Whether you are travelling alone, enjoying a romantic holiday or "
        "spending time with family and friends, Taksu Nusa Spa brings a "
        "relaxing Balinese wellness experience directly to your door.\n\n"

        "## Our Service Areas\n"
        f"{AREAS_LINE}\n\n"
        f"{NO_TRAVEL_FEE} {OUTSIDE_AREAS}\n\n"
        f"Open {OPENING_HOURS}."),

    "delivery-and-payment": (
        "Delivery & Payment",
        "## Massage Treatments\n"
        "Your therapist comes to your hotel, villa, guesthouse or home. "
        f"{NO_TRAVEL_FEE}\n\n"
        "Payment can be made:\n"
        "• Cash after your treatment\n"
        "• Bank transfer\n"
        "• Online payment\n\n"
        "No deposit is required to book.\n\n"

        "## Product Orders\n"
        f"We deliver within our service areas: {AREAS_LINE}.\n\n"
        "Payment options:\n"
        "• Cash on delivery\n"
        "• Bank transfer\n"
        "• Online payment\n\n"
        "Orders placed before 15:00 usually go out the same day."),
}

# ------------------------------------------------------------ trust badges

# Small reassurance line under the hero. No certification claim.
TRUST_EN = [
    ("shield", "Experienced professional therapists"),
    ("users", "Female & male therapists"),
    ("map-pin", "Hotel, villa & home service"),
    ("card", "Cash, transfer or online"),
]

# --------------------------------------------------- reviews to take down

# Seeded during the build as sample text, never genuine. One names Canggu,
# which is not a service area; another names a honeymoon package that is not
# on the menu. apply_copy removes exactly these and nothing else, so a real
# review entered in admin is never touched.
PLACEHOLDER_REVIEWS = [
    ("Sarah", "Amazing Balinese massage in our Canggu villa"),
    ("Marco & Julia", "Honeymoon package with a flower bath"),
    ("Tomasz", "Great value and totally professional"),
]
