# -*- coding: utf-8 -*-
"""Seed the site with Taksu Nusa Spa's starting content.

Safe to re-run: every row is matched on its slug or key and updated rather
than duplicated. Prices marked PLACEHOLDER below are guesses — set the real
ones in the admin panel before going live.

    python -m scripts.seed
"""
import os
import secrets

from app import create_app
from app.extensions import db
from app.models.discount import Discount
from app.models.shop import DeliveryZone, Product, ProductGroup
from app.models.site import FaqItem, Page, SiteSetting
from app.models.spa import OpeningHour, Treatment, TreatmentCategory
from app.models.user import User

SETTINGS = {
    "company_name": "Taksu Nusa Spa",
    "tagline_en": "Balinese massage, natural treatments and pure Bali honey.",
    "tagline_idn": "Pijat Bali, perawatan alami, dan madu asli Bali.",
    "about_en": "Taksu Nusa Spa brings together traditional Balinese treatments "
                "and natural products made on the island. Every treatment uses "
                "our own oils and honey, sourced from small producers in Bali.",
    "about_idn": "Taksu Nusa Spa memadukan perawatan tradisional Bali dengan "
                 "produk alami buatan pulau ini. Setiap perawatan memakai minyak "
                 "dan madu kami sendiri dari produsen kecil di Bali.",
    "phone": "+62 823-3956-6156",
    "whatsapp": "6282339566156",
    "email": "",
    "address": "Jalan Gatot Kaca No.5, Desa Kuwum, Mengwi",
    "city": "Kabupaten Badung, Bali",
    "postal_code": "80351",
    "price_range": "$$",
    "meta_desc": "Balinese massage and spa treatments in Mengwi, Badung — plus "
                 "pure Bali honey delivered across the island. Book online.",
    "bank_details": "Bank transfer details — set these in Admin → Site settings.",
    "slot_step_min": "30",
    "footer_note_en": "Taksu Nusa Spa · Mengwi, Badung, Bali",
    "footer_note_idn": "Taksu Nusa Spa · Mengwi, Badung, Bali",
    "nib": "9120014231404",
}

# Opening hours: 09:00–21:00 every day (change in Admin → Hours).
HOURS = {wd: (9 * 60, 21 * 60) for wd in range(7)}

TREATMENT_CATEGORIES = [
    ("massage", "Massage", "Pijat", "💆", 10,
     "Traditional Balinese hands, warm oil, unhurried pressure."),
    ("body-treatment", "Body Treatments", "Perawatan Tubuh", "🌿", 20,
     "Scrubs, masks and boreh wraps made from island ingredients."),
    ("facial", "Facials", "Perawatan Wajah", "✨", 30,
     "Gentle facials using honey and natural botanicals."),
    ("packages", "Spa Packages", "Paket Spa", "🎁", 40,
     "Half-day and full-day combinations at a better price."),
]

# PLACEHOLDER prices — confirm with the owner, then edit in admin.
TREATMENTS = [
    ("balinese-massage", "massage", "Balinese Massage", "Pijat Bali", 60, 150000,
     "The classic full-body Balinese massage: long strokes, palm pressure and "
     "warm coconut oil, working the whole body from feet to shoulders."),
    ("aromatherapy-massage", "massage", "Aromatherapy Massage",
     "Pijat Aromaterapi", 60, 175000,
     "Slower and lighter than the Balinese, with an essential-oil blend chosen "
     "for you at the start of the treatment."),
    ("hot-stone-massage", "massage", "Hot Stone Massage", "Pijat Batu Panas",
     90, 250000,
     "Warmed volcanic stones rest along the spine while the therapist works "
     "the surrounding muscles — good for deep tension and cold weather."),
    ("foot-reflexology", "massage", "Foot Reflexology", "Refleksi Kaki", 45,
     100000,
     "Pressure-point work on the feet and lower legs. The usual first booking "
     "for guests who have been walking all day."),
    ("balinese-boreh", "body-treatment", "Balinese Boreh Body Wrap",
     "Boreh Bali", 60, 200000,
     "The warming spice wrap Balinese farmers have used for generations — "
     "ginger, clove and rice powder, applied warm."),
    ("honey-body-scrub", "body-treatment", "Honey & Sea Salt Scrub",
     "Lulur Madu & Garam Laut", 45, 175000,
     "Our own Bali honey blended with sea salt, then rinsed and finished with "
     "coconut oil."),
    ("honey-facial", "facial", "Pure Honey Facial", "Facial Madu Murni", 60,
     185000,
     "A calming facial built around raw Bali honey: cleanse, gentle exfoliation, "
     "honey mask and a face and shoulder massage."),
    ("half-day-retreat", "packages", "Half-Day Retreat", "Paket Setengah Hari",
     180, 500000,
     "Balinese massage, honey and sea salt scrub, and a pure honey facial, with "
     "herbal tea between treatments."),
]

PRODUCT_GROUPS = [
    ("honey", "Honey", "Madu", "🍯", 10,
     "Raw honey from stingless bees and wild hives in Bali, bottled by small "
     "producers. No added sugar, nothing heated."),
    ("spa-products", "Spa Products", "Produk Spa", "🧴", 20,
     "The oils, scrubs and balms we use in the treatment rooms."),
    ("gift-sets", "Gift Sets", "Paket Hadiah", "🎁", 30,
     "Honey and spa products boxed together, ready to give."),
]

# From the product photos: Sari Madu Sedana, produced by Yustika in Balangan.
# PLACEHOLDER prices — confirm before going live.
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
     "Madu Kela Kela adalah madu cair dari rangkaian Sari Madu Sedana — dipanen "
     "di Bali, cair, dengan rasa asam manis khas madu kelulut.\n\n"
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
     "Madu Nyawan is the thick honey in the Sari Madu Sedana range: dense, slow "
     "off the spoon, and clearly sweet rather than sour.\n\n"
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
    ("Mengwi & Badung", "Mengwi & Badung", 15000, 300000, 10),
    ("Denpasar", "Denpasar", 25000, 300000, 20),
    ("Canggu / Seminyak / Kuta", "Canggu / Seminyak / Kuta", 30000, 400000, 30),
    ("Ubud", "Ubud", 35000, 400000, 40),
    ("Rest of Bali", "Bali lainnya", 50000, 500000, 50),
]

FAQS = [
    ("Do you deliver honey across Bali?",
     "Apakah madu dikirim ke seluruh Bali?",
     "Yes. We deliver across Bali. You can pay cash to the driver on delivery, "
     "by bank transfer, or with an online payment link — whichever suits you.",
     "Ya. Kami mengirim ke seluruh Bali. Anda bisa bayar tunai ke kurir saat "
     "barang tiba, transfer bank, atau lewat tautan pembayaran online."),
    ("Is the honey pure?", "Apakah madunya murni?",
     "Yes — 100% honey with no added sugar and no heating. It is produced by "
     "Yustika in Balangan under the Sari Madu Sedana label, business number "
     "9120014231404.",
     "Ya — 100% madu tanpa gula tambahan dan tanpa pemanasan. Diproduksi oleh "
     "Yustika di Balangan dengan merek Sari Madu Sedana, NIB 9120014231404."),
    ("Do I need to book a treatment in advance?",
     "Apakah perlu memesan perawatan sebelumnya?",
     "Booking online secures your time and therapist. Walk-ins are welcome when "
     "a room is free, but weekends fill up.",
     "Pesan online memastikan jam dan terapis Anda. Tanpa reservasi tetap kami "
     "layani bila ada ruangan kosong, tetapi akhir pekan biasanya penuh."),
]

PAGES = [
    ("about", "About Us", "Tentang Kami",
     "Taksu Nusa Spa is a small Balinese spa in Mengwi, Badung.\n\n"
     "Write your story here from Admin → Pages.",
     "Taksu Nusa Spa adalah spa Bali kecil di Mengwi, Badung.\n\n"
     "Tulis cerita Anda di Admin → Pages."),
    ("delivery-and-payment", "Delivery & Payment", "Pengiriman & Pembayaran",
     "We deliver across Bali.\n\n"
     "Payment options: cash on delivery, cash at the spa, bank transfer, or an "
     "online payment link.\n\n"
     "Orders placed before 15:00 usually go out the same day.",
     "Kami mengirim ke seluruh Bali.\n\n"
     "Pilihan pembayaran: bayar tunai saat pengiriman, tunai di spa, transfer "
     "bank, atau tautan pembayaran online.\n\n"
     "Pesanan sebelum pukul 15.00 biasanya dikirim hari itu juga."),
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

        for i, (slug, cat, en, idn, mins, price, desc) in enumerate(TREATMENTS):
            upsert(Treatment, {"slug": slug}, name_en=en, name_idn=idn,
                   category_id=cats[cat].id, duration_min=mins,
                   price_idr=price, desc_en=desc, sort_order=i * 10,
                   is_featured=i < 3, is_active=True)

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
                   sort_order=i * 10)

        # An example discount, switched off. Turn it on in admin and every
        # product card and treatment page picks it up at once.
        if not Discount.query.first():
            db.session.add(Discount(
                label_en="Grand opening", label_idn="Pembukaan",
                scope="all", kind="percent", value=10, is_active=False))

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
        print("Prices are placeholders — set the real ones in the admin panel.")


if __name__ == "__main__":
    run()
