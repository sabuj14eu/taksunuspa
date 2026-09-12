# -*- coding: utf-8 -*-
"""Seed the site with Taksu Nusa Spa's content.

Treatments, prices, service areas and therapists come from the approved
redesign, which carried them over from the live site — so these are the real
menu, not placeholders. The honey products come from the producer's labels.

Safe to re-run: rows are matched on slug or key and updated, never duplicated.

    python -m scripts.seed
"""
import os
import secrets

from app import create_app
from app.extensions import db
from app.models.discount import Discount
from app.models.media import Review
from app.models.shop import DeliveryZone, Product, ProductGroup
from app.models.site import FaqItem, Page, SiteSetting
from app.models.spa import (Highlight, OpeningHour, ServiceArea, Therapist,
                            Treatment, TreatmentCategory, TreatmentOption)
from app.models.user import User

SETTINGS = {
    # identity
    "company_name": "Taksu Nusa Spa",
    "brand_short": "Taksu Nusa",
    "tagline_en": "Professional therapists come to your villa, hotel or home. "
                  "Authentic rituals, organic oils, and total relaxation — "
                  "wherever you are in Bali.",
    "tagline_idn": "Terapis profesional datang ke vila, hotel atau rumah Anda. "
                   "Ritual autentik, minyak organik, dan relaksasi total — "
                   "di mana pun Anda di Bali.",
    "about_en": "Taksu Nusa Spa brings the full Balinese spa experience to "
                "you. We carry the table, the towels, the music and the oils, "
                "and our therapists work the way they were trained on the "
                "island — unhurried, intuitive, and warm.",
    "about_idn": "Taksu Nusa Spa membawa pengalaman spa Bali lengkap kepada "
                 "Anda. Kami membawa meja, handuk, musik dan minyak, dan "
                 "terapis kami bekerja seperti yang mereka pelajari di pulau "
                 "ini — tenang, intuitif, dan hangat.",
    "nib": "9120014231404",

    # contact
    "phone": "+62 812-3672-9448",
    "whatsapp": "6281236729448",
    "email": "",
    "address": "Jalan Gatot Kaca No.5, Desa Kuwum, Mengwi",
    "city": "Bali",
    "postal_code": "80351",
    "service_hours": "Daily 09:00 – 23:00",
    "service_scope": "Bali-wide service",
    "price_range": "$$",

    # home page copy
    "hero_eyebrow_en": "Balinese wellness · at your door",
    "hero_eyebrow_idn": "Kesehatan Bali · di depan pintu Anda",
    "hero_line1_en": "Bali Premium",
    "hero_line1_idn": "Home Spa",
    "hero_line2_en": "Home Spa.",
    "hero_line2_idn": "Premium Bali.",
    "rating_value": "4.9",
    "rating_note_en": "rating · 1000+ happy guests",
    "rating_note_idn": "rating · 1000+ tamu puas",

    "treatments_eyebrow_en": "Traditional & therapeutic",
    "treatments_intro_en": "Each treatment uses Balinese techniques, warm oils, "
                           "and intuitive pressure to release tension and "
                           "restore balance.",
    "treatments_intro_idn": "Setiap perawatan memakai teknik Bali, minyak "
                            "hangat, dan tekanan intuitif untuk melepas "
                            "ketegangan dan memulihkan keseimbangan.",

    "experience_eyebrow_en": "The difference",
    "experience_title_en": "Why guests choose us",
    "experience_title_idn": "Mengapa tamu memilih kami",

    "therapists_eyebrow_en": "Your healers",
    "therapists_title_en": "Meet our therapists",
    "therapists_title_idn": "Kenali terapis kami",
    "therapists_intro_en": "Certified therapists with years of practice, who "
                           "come to you anywhere in Bali.",
    "therapists_intro_idn": "Terapis bersertifikat berpengalaman, datang ke "
                            "tempat Anda di seluruh Bali.",

    "gallery_eyebrow_en": "A glimpse of bliss",
    "products_eyebrow_en": "Take Bali home",

    "areas_note_en": "Free travel inside our service areas — hotel, villa, "
                     "guesthouse or private home.",
    "areas_note_idn": "Transport gratis di dalam area layanan kami — hotel, "
                      "vila, guesthouse atau rumah pribadi.",

    "reviews_eyebrow_en": "From stress to bliss",
    "reviews_title_en": "Guest reviews",
    "reviews_title_idn": "Ulasan tamu",

    "cta_eyebrow_en": "Ready in 60 seconds",
    "cta_title_en": "Your relaxation is one tap away",
    "cta_title_idn": "Relaksasi Anda tinggal satu ketukan",
    "cta_text_en": "Choose your treatment, pick a time, and we'll bring the "
                   "full spa experience to you.",
    "cta_text_idn": "Pilih perawatan, pilih jam, dan kami bawa pengalaman spa "
                    "lengkap ke tempat Anda.",

    # plumbing
    "meta_desc": "Professional Balinese therapists come to your villa, hotel "
                 "or home. Massage, couple rituals and natural body care "
                 "across Bali. Book online.",
    "bank_details": "Bank transfer details — set these in Admin → Site settings.",
    "slot_step_min": "30",
    "footer_note_en": "Premium Balinese home spa service across Bali.",
    "footer_note_idn": "Layanan home spa Bali premium di seluruh Bali.",
}

# Daily 09:00 – 23:00.
HOURS = {wd: (9 * 60, 23 * 60) for wd in range(7)}

TREATMENT_CATEGORIES = [
    ("massage", "Massage", "Pijat", "💆", 10,
     "Traditional Balinese hands, warm oil, unhurried pressure — in your own "
     "room."),
    ("body-treatment", "Body Rituals", "Ritual Tubuh", "🌿", 20,
     "Scrubs, masks and flower baths made from island ingredients."),
    ("packages", "Packages", "Paket", "🎁", 30,
     "Longer combinations for couples and half-day escapes."),
]

# name, category, EN name, ID name, per_person, description,
# [(minutes, price), ...]
TREATMENTS = [
    ("balinese-massage", "massage", "Balinese Massage", "Pijat Bali", False,
     "Traditional full-body massage with aromatic oils to restore flow and "
     "calm. Long strokes, palm pressure and warm coconut oil, working the "
     "whole body from feet to shoulders.",
     [(60, 300000), (90, 400000), (120, 550000)]),
    ("deep-tissue-massage", "massage", "Deep Tissue Massage",
     "Pijat Deep Tissue", False,
     "Strong, focused pressure for muscle recovery and deep release. The one "
     "to book after surfing, training or a long flight.",
     [(60, 350000), (90, 450000)]),
    ("couple-massage", "massage", "Couple Massage", "Pijat Pasangan", True,
     "Two therapists, side by side, in your own room. Price is per person for "
     "a shared ritual.",
     [(60, 300000), (90, 400000)]),
    ("foot-massage", "massage", "Foot Massage", "Pijat Kaki", False,
     "Reflexology for tired feet using warming herbal oils. Pressure-point "
     "work on the feet and lower legs.",
     [(60, 250000)]),
]

THERAPISTS = [
    ("Nyoman Suriyani", "Senior therapist", "Terapis senior",
     "English, Indonesian", 10),
    ("Wayan Narti", "Wellness therapist", "Terapis wellness",
     "English, Indonesian", 20),
]

AREAS = ["Seminyak", "Ubud", "Kuta", "Legian", "Sanur", "Nusa Dua",
         "Jimbaran", "Uluwatu"]

HIGHLIGHTS = [
    ("🛡️", "Certified therapists", "Terapis bersertifikat",
     "Professionals with 5+ years of practice and formal spa training.",
     "Profesional dengan pengalaman 5+ tahun dan pelatihan spa formal."),
    ("🌿", "Organic botanicals", "Bahan organik",
     "Cold-pressed coconut oil and essential oils, made and sourced in Bali.",
     "Minyak kelapa cold-pressed dan minyak esensial, dibuat di Bali."),
    ("🏡", "Private & discreet", "Privat & diskret",
     "In-room hotel, villa, and home service with total discretion.",
     "Layanan di kamar hotel, vila dan rumah dengan diskresi penuh."),
    ("✨", "Full spa ritual", "Ritual spa lengkap",
     "We bring the table, towels, music, and oils — everything you need.",
     "Kami bawa meja, handuk, musik dan minyak — semua yang diperlukan."),
    ("💧", "Fresh linens", "Linen bersih",
     "Premium spa table with freshly laundered towels for every visit.",
     "Meja spa premium dengan handuk yang baru dicuci setiap kunjungan."),
    ("🧼", "Hygienic & safe", "Higienis & aman",
     "Sanitised equipment and strict hygiene protocols on every booking.",
     "Peralatan disanitasi dan protokol kebersihan ketat setiap pemesanan."),
]

REVIEWS = [
    ("Sarah", "Australia", 5,
     "Amazing Balinese massage in our Canggu villa. On time, professional, "
     "pure bliss. Booked twice more!"),
    ("Marco & Julia", "Italy", 5,
     "Honeymoon package with a flower bath on our terrace at sunset. The most "
     "romantic evening of our trip."),
    ("Tomasz", "Poland", 5,
     "Great value and totally professional. The booking took one minute and "
     "WhatsApp confirmation came instantly."),
]

PRODUCT_GROUPS = [
    ("honey", "Honey", "Madu", "🍯", 10,
     "Raw honey from stingless bees and wild hives in Bali, bottled by small "
     "producers. No added sugar, nothing heated."),
    ("spa-products", "Spa Products", "Produk Spa", "🧴", 20,
     "The oils, scrubs and balms we use in the treatment room."),
    ("gift-sets", "Gift Sets", "Paket Hadiah", "🎁", 30,
     "Honey and spa products boxed together, ready to give."),
]

# From the product labels: Sari Madu Sedana, produced by Yustika in Balangan.
# PLACEHOLDER prices — confirm these before going live.
PRODUCTS = [
    ("madu-kela-kela-250ml", "honey", "Madu Kela Kela 250 ml",
     "Madu Kela Kela 250 ml", "250 ml", 75000, 100,
     "Liquid Bali honey with a fresh sweet-sour finish.",
     "Madu cair khas Bali dengan rasa asam manis yang segar.",
     "Madu Kela Kela is the liquid honey in the Sari Madu Sedana range — "
     "harvested in Bali, thin enough to pour, with the sweet-sour taste that "
     "marks honey from stingless bees.\n\n"
     "100% pure honey. No added sugar, no heating, nothing else in the bottle.\n\n"
     "Use it in warm (not hot) water, over yoghurt, or by the spoon.",
     "Madu Kela Kela adalah madu cair dari rangkaian Sari Madu Sedana — "
     "dipanen di Bali, cair, dengan rasa asam manis khas madu kelulut.\n\n"
     "100% madu asli. Tanpa gula tambahan, tanpa pemanasan.\n\n"
     "Nikmati dengan air hangat, yoghurt, atau langsung satu sendok."),
    ("madu-kela-kela-500ml", "honey", "Madu Kela Kela 500 ml",
     "Madu Kela Kela 500 ml", "500 ml", 140000, 60,
     "The family-size bottle of our liquid Bali honey.",
     "Botol ukuran keluarga untuk madu cair Bali kami.",
     "The 500 ml bottle of Madu Kela Kela — the same liquid, sweet-sour Bali "
     "honey, in the size regular customers keep coming back for.\n\n"
     "100% pure honey, no added sugar.",
     "Botol 500 ml Madu Kela Kela — madu cair Bali dengan rasa asam manis yang "
     "sama, dalam ukuran favorit pelanggan tetap.\n\n"
     "100% madu asli, tanpa gula tambahan."),
    ("madu-nyawan-500ml", "honey", "Madu Nyawan 500 ml",
     "Madu Nyawan 500 ml", "500 ml", 160000, 40,
     "Thick honey with a dominant sweet taste.",
     "Madu kental dengan rasa dominan manis.",
     "Madu Nyawan is the thick honey in the Sari Madu Sedana range: dense, "
     "slow off the spoon, and clearly sweet rather than sour.\n\n"
     "100% pure honey. No added sugar.\n\n"
     "The one to choose if you find stingless-bee honey too sharp.",
     "Madu Nyawan adalah madu kental dari rangkaian Sari Madu Sedana: padat, "
     "lambat menetes, dan dominan manis.\n\n"
     "100% madu asli. Tanpa gula tambahan.\n\n"
     "Pilihan tepat bila madu kelulut terasa terlalu asam untuk Anda."),
]

PRODUCER = "Yustika — Sari Madu Sedana, Balangan"
PRODUCT_NIB = "9120014231404"

DELIVERY_ZONES = [
    ("Seminyak / Kuta / Legian", "Seminyak / Kuta / Legian", 25000, 300000, 10),
    ("Denpasar & Badung", "Denpasar & Badung", 20000, 300000, 20),
    ("Canggu", "Canggu", 30000, 400000, 30),
    ("Ubud", "Ubud", 35000, 400000, 40),
    ("Rest of Bali", "Bali lainnya", 50000, 500000, 50),
]

FAQS = [
    ("Do you come to my hotel or villa?",
     "Apakah kalian datang ke hotel atau vila saya?",
     "Yes — that is the whole service. Our therapist brings the massage table, "
     "fresh towels, oils and music to your villa, hotel room, guesthouse or "
     "home anywhere in our service areas.",
     "Ya — itu inti layanan kami. Terapis membawa meja pijat, handuk bersih, "
     "minyak dan musik ke vila, kamar hotel, guesthouse atau rumah Anda di "
     "seluruh area layanan kami."),
    ("How do I pay?", "Bagaimana cara membayar?",
     "Cash to the therapist after the treatment, bank transfer, or an online "
     "payment link. For honey and products you can also pay cash on delivery.",
     "Tunai ke terapis setelah perawatan, transfer bank, atau tautan "
     "pembayaran online. Untuk madu dan produk bisa juga bayar di tempat."),
    ("How far ahead should I book?", "Berapa lama sebelumnya harus memesan?",
     "Booking online secures your time and therapist. We ask for at least two "
     "hours' notice so the therapist can travel to you; evenings and weekends "
     "fill up first.",
     "Pesan online memastikan jam dan terapis Anda. Mohon pesan minimal dua "
     "jam sebelumnya agar terapis sempat menuju lokasi; malam hari dan akhir "
     "pekan biasanya penuh lebih dulu."),
    ("Is the honey pure?", "Apakah madunya murni?",
     "Yes — 100% honey with no added sugar and no heating. It is produced by "
     "Yustika in Balangan under the Sari Madu Sedana label, business number "
     "9120014231404.",
     "Ya — 100% madu tanpa gula tambahan dan tanpa pemanasan. Diproduksi oleh "
     "Yustika di Balangan dengan merek Sari Madu Sedana, NIB 9120014231404."),
]

PAGES = [
    ("about", "About Us", "Tentang Kami",
     "Taksu Nusa Spa is a Balinese home spa service. Our therapists travel to "
     "you anywhere in Bali.\n\nWrite your story here from Admin → Pages.",
     "Taksu Nusa Spa adalah layanan home spa Bali. Terapis kami datang ke "
     "tempat Anda di seluruh Bali.\n\nTulis cerita Anda di Admin → Pages."),
    ("delivery-and-payment", "Delivery & Payment", "Pengiriman & Pembayaran",
     "Treatments: pay the therapist in cash after your treatment, by bank "
     "transfer, or with an online payment link.\n\n"
     "Products: we deliver across Bali. Pay cash on delivery, by transfer, or "
     "online. Orders placed before 15:00 usually go out the same day.",
     "Perawatan: bayar tunai ke terapis setelah perawatan, transfer bank, "
     "atau lewat tautan pembayaran online.\n\n"
     "Produk: kami kirim ke seluruh Bali. Bayar di tempat, transfer, atau "
     "online. Pesanan sebelum pukul 15.00 biasanya dikirim hari itu juga."),
]


def upsert(model, match, **fields):
    row = model.query.filter_by(**match).first()
    if not row:
        row = model(**match)
        db.session.add(row)
    for k, v in fields.items():
        setattr(row, k, v)
    return row


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        for key, value in SETTINGS.items():
            SiteSetting.put(key, value)

        for wd, (open_min, close_min) in HOURS.items():
            upsert(OpeningHour, {"weekday": wd}, open_min=open_min,
                   close_min=close_min, is_closed=False)

        cats = {}
        for slug, en, idn, icon, order, desc in TREATMENT_CATEGORIES:
            cats[slug] = upsert(TreatmentCategory, {"slug": slug}, name_en=en,
                                name_idn=idn, icon=icon, sort_order=order,
                                desc_en=desc, is_active=True)
        db.session.flush()

        for i, row in enumerate(TREATMENTS):
            slug, cat, en, idn, per_person, desc, tiers = row
            tr = upsert(Treatment, {"slug": slug}, name_en=en, name_idn=idn,
                        category_id=cats[cat].id, desc_en=desc,
                        per_person=per_person,
                        duration_min=tiers[0][0], price_idr=tiers[0][1],
                        sort_order=i * 10, is_featured=True, is_active=True)
            db.session.flush()
            for j, (minutes, price) in enumerate(tiers):
                upsert(TreatmentOption,
                       {"treatment_id": tr.id, "duration_min": minutes},
                       price_idr=price, sort_order=j * 10, is_active=True)

        for name, role_en, role_idn, languages, order in THERAPISTS:
            upsert(Therapist, {"name": name}, role_en=role_en,
                   role_idn=role_idn, languages=languages, sort_order=order,
                   is_available_today=True, show_on_site=True, is_active=True)

        for i, name in enumerate(AREAS):
            upsert(ServiceArea, {"name": name},
                   slug=name.lower().replace(" ", "-"), travel_fee_idr=0,
                   sort_order=i * 10, is_active=True)

        for i, (icon, t_en, t_idn, x_en, x_idn) in enumerate(HIGHLIGHTS):
            upsert(Highlight, {"title_en": t_en}, icon=icon, title_idn=t_idn,
                   text_en=x_en, text_idn=x_idn, sort_order=i * 10,
                   is_visible=True)

        for author, location, rating, text in REVIEWS:
            upsert(Review, {"entity_type": "site", "author_name": author},
                   entity_id=0, rating=rating, text=text,
                   lang="en", is_approved=True)

        groups = {}
        for slug, en, idn, icon, order, desc in PRODUCT_GROUPS:
            groups[slug] = upsert(ProductGroup, {"slug": slug}, name_en=en,
                                  name_idn=idn, icon=icon, sort_order=order,
                                  desc_en=desc, is_active=True)
        db.session.flush()

        for i, row in enumerate(PRODUCTS):
            (slug, group, en, idn, size, price, stock,
             short_en, short_idn, desc_en, desc_idn) = row
            upsert(Product, {"slug": slug}, name_en=en, name_idn=idn,
                   group_id=groups[group].id, size_label=size, price_idr=price,
                   stock=stock, track_stock=True, short_en=short_en,
                   short_idn=short_idn, desc_en=desc_en, desc_idn=desc_idn,
                   producer=PRODUCER, nib=PRODUCT_NIB, sort_order=i * 10,
                   is_featured=True, is_active=True)

        for en, idn, fee, free_over, order in DELIVERY_ZONES:
            upsert(DeliveryZone, {"name_en": en}, name_idn=idn, fee_idr=fee,
                   free_over_idr=free_over, sort_order=order, is_active=True)

        for i, (q_en, q_idn, a_en, a_idn) in enumerate(FAQS):
            upsert(FaqItem, {"question_en": q_en}, question_idn=q_idn,
                   answer_en=a_en, answer_idn=a_idn, sort_order=i * 10,
                   is_visible=True)

        for i, (slug, t_en, t_idn, b_en, b_idn) in enumerate(PAGES):
            upsert(Page, {"slug": slug}, title_en=t_en, title_idn=t_idn,
                   body_en=b_en, body_idn=b_idn, is_visible=True,
                   show_in_menu=True, sort_order=i * 10)

        # The promotional pricing the redesign showed (300.000 struck through,
        # 250.000 charged) is a 50.000 rupiah launch discount on treatments.
        # Seeded switched off — turn it on in admin when the promo runs.
        if not Discount.query.first():
            db.session.add(Discount(
                label_en="Launch offer", label_idn="Promo peluncuran",
                scope="treatments", kind="amount", value=50000,
                is_active=False))

        admin = User.query.filter_by(phone=SETTINGS["whatsapp"]).first()
        password = None
        if not admin:
            password = os.getenv("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
            admin = User(role="admin", name="Owner",
                         phone=SETTINGS["whatsapp"], is_active_flag=True)
            admin.set_password(password)
            db.session.add(admin)

        db.session.commit()

        print("Seed complete.")
        if password:
            print("\n  Admin sign-in at /login")
            print(f"  phone:    {SETTINGS['whatsapp']}")
            print(f"  password: {password}")
            print("\n  Change it straight away in Admin -> My account.\n")
        print("Treatment prices are the real menu. Product prices are "
              "placeholders — confirm them in the admin panel.")
        print("Upload the hero, gallery, therapist and product photos in "
              "Admin -> Photos.")


if __name__ == "__main__":
    run()
