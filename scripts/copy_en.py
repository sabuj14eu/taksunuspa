"""The English copy for the whole site, in one place.

Two things read this: scripts/seed.py, so a brand-new database starts with the
right wording, and scripts/apply_copy.py, which pushes the same wording onto a
database that is already live. Editing the text here and running apply_copy is
the whole workflow — there is no second copy of these sentences to forget.

Rules this copy follows, set by the owner:
  * Taksu Nusa Spa is a home spa. Therapists travel to the guest.
  * The service covers eight named areas, not the whole island. Nothing may
    say "Bali-wide", "across Bali" or "wherever you are in Bali".
  * There is no travel fee inside those areas — say that, do not say "free".
  * Couple Massage is priced per person, and that must be impossible to miss.
  * No medical or health claims, for treatments or for honey.
"""

# The eight areas, in the order the owner lists them. Everything that prints
# the areas builds the string from here, so they cannot drift apart.
AREAS = ["Seminyak", "Ubud", "Kuta", "Legian", "Sanur", "Nusa Dua",
         "Jimbaran", "Uluwatu"]
AREAS_LINE = " · ".join(AREAS)

OPENING_HOURS = "Daily 09:00 – 23:00"
NO_TRAVEL_FEE = "No travel fee within our service areas."

POSITIONING = ("Professional Balinese home spa treatments delivered to your "
               "hotel, villa or home.")

# ---------------------------------------------------------------- settings

SETTINGS_EN = {
    "tagline_en": POSITIONING,

    "about_en": (
        "Taksu Nusa Spa is a home spa service. Rather than asking you to "
        "travel, our therapists come to you, bringing the massage table, "
        "fresh linen, warm oils and music, and setting up in your own room."),

    "service_hours": OPENING_HOURS,
    "service_scope": f"Service areas: {AREAS_LINE}",

    # hero
    "hero_eyebrow_en": "Balinese home spa · we come to you",
    "hero_line1_en": "The Spa",
    "hero_line2_en": "Comes to You.",

    "treatments_eyebrow_en": "Traditional Balinese treatments",
    "treatments_intro_en": (
        "Every treatment is given in your own room, using traditional "
        "Balinese technique, warm oils and steady, unhurried pressure."),

    "experience_eyebrow_en": "Why book with us",
    "experience_title_en": "Why guests choose us",

    "therapists_eyebrow_en": "Meet Our Therapists",
    "therapists_title_en": "Meet Our Therapists",
    "therapists_intro_en": (
        "Experienced professional therapists, trained in Bali, who come to "
        "your hotel, villa or home."),

    "gallery_eyebrow_en": "A look inside",
    "products_eyebrow_en": "Take Bali home",

    "areas_note_en": (
        f"{NO_TRAVEL_FEE} We come to your hotel, villa, guesthouse or home in "
        f"{AREAS_LINE}."),

    "reviews_eyebrow_en": "What guests say",
    "reviews_title_en": "Guest reviews",

    "cta_eyebrow_en": "Booking takes a minute",
    "cta_title_en": "Book your treatment",
    "cta_text_en": (
        "Choose your treatment and a time that suits you, and your therapist "
        "will arrive ready to set up."),

    "meta_desc": (
        f"{POSITIONING} Massage for one or two guests in {AREAS_LINE}. "
        f"Book online or on WhatsApp."),

    "footer_note_en": POSITIONING,
}

# ------------------------------------------------------------- treatments

TREATMENT_GROUP_DESC_EN = {
    "massage": ("Traditional Balinese massage given in your own room, with "
                "warm oil and unhurried pressure."),
    "body-treatment": ("Scrubs, masks and flower baths made from island "
                       "ingredients."),
    "packages": ("Longer combinations for couples and half-day escapes."),
}

TREATMENT_DESC_EN = {
    "balinese-massage":
        "The classic Balinese full-body massage, and the one most guests "
        "book first. Your therapist works from the feet up to the shoulders "
        "with long, flowing strokes, gentle stretching and warm coconut oil, "
        "at a pace that is calming rather than brisk. A good choice after "
        "travelling, or on a slow afternoon at the villa.",

    "deep-tissue-massage":
        "A firmer massage for guests who prefer strong pressure. Your "
        "therapist works slowly through the shoulders, back and legs, "
        "spending time on the areas that feel tight. Popular after surfing, "
        "training or a long flight. Tell your therapist how much pressure "
        "you like — they will adjust as they go.",

    "couple-massage":
        "Two therapists, two tables, side by side in your own room, so you "
        "and your partner are massaged at the same time. A relaxed, "
        "unhurried treatment to share — a favourite for honeymoons, "
        "anniversaries and first nights in Bali.\n\n"
        "Please note: the price shown is per person.",

    "foot-massage":
        "A focused treatment for tired feet and lower legs, using warm "
        "herbal oil and firm thumb pressure through the soles, ankles and "
        "calves. Deeply relaxing after a day of walking, and easy to enjoy "
        "sitting comfortably in your own room.",
}

# --------------------------------------------------------------- products

PRODUCT_GROUP_DESC_EN = {
    "honey": ("Our own honey, made at home here in Bali — raw, from "
              "stingless bees and wild hives. No added sugar, nothing "
              "heated, nothing bought in to resell."),
    "spa-products": "The oils, scrubs and balms we use in the treatment room.",
    "gift-sets": "Honey and spa products boxed together, ready to give.",
}

# slug -> (short line under the name, full description)
PRODUCT_COPY_EN = {
    "madu-kela-kela-250ml": (
        "Raw liquid honey with a bright sweet-sour taste. 250 ml.",
        "Madu Kela Kela is the liquid honey in our Sari Madu Sedana range, "
        "gathered from stingless bees here in Bali. It pours easily and has "
        "the fresh sweet-sour character that sets stingless-bee honey apart "
        "from ordinary table honey.\n\n"
        "Raw and unheated, with no added sugar and nothing else in the "
        "bottle.\n\n"
        "Enjoy it by the spoon, stirred into warm water, or over yoghurt "
        "and fruit."),

    "madu-kela-kela-500ml": (
        "The family-size bottle of our raw liquid honey. 500 ml.",
        "The 500 ml bottle of Madu Kela Kela — the same raw liquid honey, "
        "with the same bright sweet-sour taste, in the size our regular "
        "customers come back for.\n\n"
        "Raw and unheated, with no added sugar.\n\n"
        "Keep it in the cupboard rather than the fridge, and use a dry spoon."),

    "madu-nyawan-500ml": (
        "Thick, richly sweet honey. 500 ml.",
        "Madu Nyawan is the thick honey in our Sari Madu Sedana range: "
        "dense, slow off the spoon, and clearly sweet rather than sour.\n\n"
        "Raw and unheated, with no added sugar.\n\n"
        "The one to choose if you find stingless-bee honey a little sharp. "
        "Lovely on warm toast or stirred into tea."),
}

# ------------------------------------------------------------- highlights

# (match on the existing English title, new icon, new title, new text)
HIGHLIGHTS_EN = [
    ("Certified therapists", "🌿", "Experienced therapists",
     "Professional therapists trained in Bali, with years of practice behind "
     "them."),
    ("Organic botanicals", "🥥", "Natural oils",
     "Cold-pressed coconut oil and essential oils, sourced here in Bali."),
    ("Private & discreet", "🏡", "Private and discreet",
     "Your treatment takes place in your own hotel room, villa or home."),
    ("Full spa ritual", "✨", "Everything included",
     "We bring the table, linen, oils and music — you need only be there."),
    ("Fresh linens", "💧", "Fresh linen every time",
     "Clean, freshly laundered towels and linen for every single booking."),
    ("Hygienic & safe", "🧼", "Clean and careful",
     "Equipment is sanitised between guests, every time."),
]

# -------------------------------------------------------------------- FAQ

# Matched on the old question so an existing row is updated rather than
# duplicated. (old question, new question, new answer)
FAQ_EN = [
    ("Do you come to my hotel or villa?",
     "Do you come to my hotel or villa?",
     "Yes — that is our whole service. Your therapist brings the massage "
     "table, fresh linen, oils and music to your hotel room, villa, "
     "guesthouse or home, and sets everything up for you."),

    ("__areas__",
     "Which areas do you cover?",
     f"We currently serve {AREAS_LINE}. {NO_TRAVEL_FEE} If you are staying "
     f"just outside these areas, message us on WhatsApp and we will let you "
     f"know if we can reach you."),

    ("How do I pay?", "How do I pay?",
     "For treatments: cash to your therapist after the treatment, bank "
     "transfer, or an online payment link. For honey and other products: "
     "cash on delivery, bank transfer, or online payment."),

    ("How far ahead should I book?", "How far ahead should I book?",
     "Booking in advance is recommended, as it secures both your time and "
     "your therapist. Please allow at least two hours so your therapist can "
     "travel to you. Evenings and weekends fill up first."),

    ("__gender__",
     "Can I request a female or male therapist?",
     "Yes, you are welcome to request a female or male therapist when you "
     "book. Requests are subject to availability, so please let us know as "
     "early as you can."),

    ("__couple__",
     "How is Couple Massage priced?",
     "The price shown for Couple Massage is per person. Two therapists work "
     "side by side so you and your partner are massaged at the same time."),

    ("__hours__",
     "What are your opening hours?",
     f"{OPENING_HOURS}. The last booking of the evening should start early "
     f"enough for your chosen treatment to finish by 23:00."),

    ("Is the honey pure?", "Is the honey pure?",
     "Yes — raw honey with no added sugar and nothing heated. It is made by "
     "Yustika under the Sari Madu Sedana label, business number "
     "9120014231404."),
]

# ------------------------------------------------------------------ pages

PAGES_EN = {
    "about": (
        "About Us",
        "Taksu Nusa Spa is a Balinese home spa. Rather than asking you to "
        "travel to a salon, we come to you.\n\n"
        "Your therapist arrives with everything needed for a full "
        "treatment — a proper massage table, freshly laundered linen, warm "
        "oils and music — and sets up quietly in your hotel room, villa or "
        "home. All you have to do is be there.\n\n"
        "Our therapists are experienced professionals trained here in Bali, "
        "and they work the way they were taught: unhurried, attentive, and "
        "guided by what your body needs on the day.\n\n"
        f"We currently serve {AREAS_LINE}. {NO_TRAVEL_FEE}\n\n"
        f"We are open {OPENING_HOURS.lower()}. The quickest way to book is "
        f"on WhatsApp."),

    "delivery-and-payment": (
        "Delivery & Payment",
        "TREATMENTS\n\n"
        "Your therapist comes to your hotel, villa, guesthouse or home. "
        f"{NO_TRAVEL_FEE}\n\n"
        "You can pay by:\n"
        "• Cash to your therapist after the treatment\n"
        "• Bank transfer\n"
        "• Online payment\n\n"
        "No deposit is required to book.\n\n"
        "PRODUCTS\n\n"
        f"We deliver honey and spa products throughout our service areas "
        f"({AREAS_LINE}).\n\n"
        "You can pay by:\n"
        "• Cash on delivery\n"
        "• Bank transfer\n"
        "• Online payment\n\n"
        "Orders placed before 15:00 usually go out the same day."),
}

# ---------------------------------------------------------------- contact

CONTACT_EN = {
    "intro": (
        "The quickest way to book is on WhatsApp — send us a message and we "
        "will confirm your therapist and time straight away. You can also "
        "book online, or use the form below."),
    "wa_label": "WhatsApp — fastest way to book",
    "areas_heading": "Service areas",
}

# ------------------------------------------------------------ trust badges

# Small reassurance line under the hero. No certification claim, no Bali-wide.
TRUST_EN = [
    ("shield", "Experienced professional therapists"),
    ("users", "Female & male therapists"),
    ("map-pin", "Hotel, villa & home service"),
    ("card", "Cash, transfer or online"),
]
