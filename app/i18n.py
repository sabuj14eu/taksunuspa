# -*- coding: utf-8 -*-
"""Two-language UI strings: English (default, for guests) and Indonesian.

Content rows carry their own `*_en` / `*_idn` columns; this file only covers
chrome — buttons, labels, messages. `loc(obj, "name")` picks the right column
and falls back to English so a half-translated row never renders blank.

The Indonesian suffix is `_idn`, not `_id`: `category_id` is a foreign key, and
a `_id` suffix would make `loc(obj, "category")` return an integer.
"""
from flask import session
from .config import Config

T = {
    "en": {
        "book": "Book now", "book_now": "Book now",
        "book_treatment": "Book this treatment",
        "book_relaxation": "Book your relaxation",
        "treatments": "Treatments", "products": "Products", "shop": "Shop",
        "experience": "Experience", "therapists": "Therapists",
        "gallery": "Gallery", "areas": "Areas", "explore": "Explore",
        "rights": "All rights reserved.",
        "home": "Home", "about": "About", "contact": "Contact",
        "our_product_line": "Our Product Line",
        "spa_menu": "Treatment Menu", "all": "All",
        "service_address": "Where should we come?",
        "service_address_help":
            "Villa or hotel name, room number, and the address.",
        "area": "Area", "pick_area": "Choose your area",
        "travel_fee": "Travel", "free_travel": "Free travel",
        "per_person": "per person", "guests": "Guests",
        "we_come_to_you": "We come to you",
        "areas_we_cover": "Areas we cover",
        "service_areas": "Service areas",
        "massage_in": "Massage in",
        "area_intro": "Our therapists travel to your villa, hotel or home. "
                      "Pick your area to see the travel fee and book.",
        "how_it_works": "How it works",
        "step_book": "Book online",
        "step_book_text": "Choose your treatment, day and time. "
                          "It takes a minute — no deposit.",
        "step_arrive": "Your therapist arrives",
        "step_arrive_text": "We bring the table, fresh towels, oils and music "
                            "to your door, on time.",
        "step_enjoy": "Enjoy, then pay",
        "step_enjoy_text": "Relax in your own space. Pay cash or by transfer "
                           "when the treatment is finished.",
        "travel_included": "Travel included",
        "not_your_area": "Not on the list? Message us — we may still come.",
        "view_all_therapists": "View all therapists",
        "available_today": "Available today",
        "duration": "Duration", "min": "min", "price": "Price", "from": "from",
        "add_to_cart": "Add to cart", "cart": "Cart", "checkout": "Checkout",
        "empty_cart": "Your cart is empty.",
        "qty": "Qty", "subtotal": "Subtotal", "discount": "Discount",
        "delivery": "Delivery", "total": "Total", "remove": "Remove",
        "update": "Update", "continue_shopping": "Continue shopping",
        "your_details": "Your details", "name": "Full name", "phone": "Phone",
        "email": "E-mail", "address": "Delivery address", "note": "Notes",
        "payment": "Payment method", "place_order": "Place order",
        "order_received": "Thank you! Your order has been received.",
        "booking_received": "Thank you! Your booking request has been received.",
        "we_will_confirm": "We will confirm shortly by WhatsApp or phone.",
        "order_code": "Order code", "booking_code": "Booking code",
        "day": "Day", "time": "Time", "therapist": "Therapist",
        "any_therapist": "Any therapist", "no_slots": "No free times that day.",
        "slot_gone": "That time was just taken — please pick another.",
        "cart_empty_err": "Your cart is empty.",
        "out_of_stock": "Out of stock", "in_stock": "In stock",
        "save": "Save", "sale": "SALE", "off": "OFF",
        "opening_hours": "Opening hours", "closed": "Closed",
        "send": "Send", "message": "Message",
        "message_sent": "Thank you — your message has been sent.",
        "order_whatsapp": "Order via WhatsApp",
        "book_whatsapp": "Book via WhatsApp",
        "address_required": "Please give a delivery address, or choose "
                            "\u201cCash on collection\u201d if you are picking "
                            "the order up.",
        "delivery_note": "We deliver across Bali. Pay cash on delivery, "
                         "bank transfer or online.",
        "read_more": "Read more", "back": "Back",
        "search": "Search", "no_results": "Nothing found.",
    },
    "id": {
        "book": "Pesan sekarang", "book_now": "Pesan sekarang",
        "book_treatment": "Pesan perawatan ini",
        "book_relaxation": "Pesan relaksasi Anda",
        "treatments": "Perawatan", "products": "Produk", "shop": "Toko",
        "experience": "Pengalaman", "therapists": "Terapis",
        "gallery": "Galeri", "areas": "Area", "explore": "Jelajahi",
        "rights": "Hak cipta dilindungi.",
        "home": "Beranda", "about": "Tentang", "contact": "Kontak",
        "our_product_line": "Produk Kami",
        "spa_menu": "Menu Perawatan", "all": "Semua",
        "service_address": "Kami datang ke mana?",
        "service_address_help":
            "Nama vila atau hotel, nomor kamar, dan alamatnya.",
        "area": "Area", "pick_area": "Pilih area Anda",
        "travel_fee": "Transport", "free_travel": "Transport gratis",
        "per_person": "per orang", "guests": "Tamu",
        "we_come_to_you": "Kami datang ke tempat Anda",
        "areas_we_cover": "Area yang kami layani",
        "service_areas": "Area layanan",
        "massage_in": "Pijat panggilan di",
        "area_intro": "Terapis kami datang ke vila, hotel atau rumah Anda. "
                      "Pilih area Anda untuk melihat biaya transport dan memesan.",
        "how_it_works": "Cara pesan",
        "step_book": "Pesan online",
        "step_book_text": "Pilih perawatan, hari dan jam. "
                          "Hanya butuh satu menit — tanpa uang muka.",
        "step_arrive": "Terapis datang",
        "step_arrive_text": "Kami bawa meja, handuk bersih, minyak dan musik "
                            "ke tempat Anda, tepat waktu.",
        "step_enjoy": "Nikmati, lalu bayar",
        "step_enjoy_text": "Santai di tempat Anda sendiri. Bayar tunai atau "
                           "transfer setelah perawatan selesai.",
        "travel_included": "Transport termasuk",
        "not_your_area": "Area Anda tidak ada? Hubungi kami — mungkin kami "
                         "tetap bisa datang.",
        "view_all_therapists": "Lihat semua terapis",
        "available_today": "Tersedia hari ini",
        "duration": "Durasi", "min": "menit", "price": "Harga", "from": "mulai",
        "add_to_cart": "Tambah ke keranjang", "cart": "Keranjang",
        "checkout": "Pembayaran",
        "empty_cart": "Keranjang Anda kosong.",
        "qty": "Jml", "subtotal": "Subtotal", "discount": "Diskon",
        "delivery": "Pengiriman", "total": "Total", "remove": "Hapus",
        "update": "Perbarui", "continue_shopping": "Lanjut belanja",
        "your_details": "Data Anda", "name": "Nama lengkap", "phone": "Telepon",
        "email": "E-mail", "address": "Alamat pengiriman", "note": "Catatan",
        "payment": "Metode pembayaran", "place_order": "Kirim pesanan",
        "order_received": "Terima kasih! Pesanan Anda sudah kami terima.",
        "booking_received": "Terima kasih! Permintaan pesanan sudah kami terima.",
        "we_will_confirm": "Kami akan konfirmasi segera lewat WhatsApp atau telepon.",
        "order_code": "Kode pesanan", "booking_code": "Kode pesanan",
        "day": "Tanggal", "time": "Jam", "therapist": "Terapis",
        "any_therapist": "Terapis mana saja", "no_slots": "Tidak ada jam kosong.",
        "slot_gone": "Jam itu baru saja terisi — silakan pilih yang lain.",
        "cart_empty_err": "Keranjang Anda kosong.",
        "out_of_stock": "Stok habis", "in_stock": "Tersedia",
        "save": "Hemat", "sale": "DISKON", "off": "OFF",
        "opening_hours": "Jam buka", "closed": "Tutup",
        "send": "Kirim", "message": "Pesan",
        "message_sent": "Terima kasih — pesan Anda sudah terkirim.",
        "order_whatsapp": "Pesan lewat WhatsApp",
        "book_whatsapp": "Pesan lewat WhatsApp",
        "address_required": "Mohon isi alamat pengiriman, atau pilih "
                            "\u201cAmbil sendiri\u201d bila Anda mengambil "
                            "pesanan.",
        "delivery_note": "Kami kirim ke seluruh Bali. Bayar tunai saat "
                         "pengiriman, transfer bank atau online.",
        "read_more": "Selengkapnya", "back": "Kembali",
        "search": "Cari", "no_results": "Tidak ada hasil.",
    },
}


class Strings:
    """Attribute access for UI strings.

    A plain dict cannot back `{{ t.update }}` in a template: Jinja resolves
    attributes before keys, so it would hand back `dict.update` — the method —
    and render "<built-in method update of dict object ...>" on the page. This
    wrapper has no methods to collide with, so every key is reachable by name.
    """
    __slots__ = ("_d",)

    def __init__(self, data: dict):
        object.__setattr__(self, "_d", data)

    def __getattr__(self, name):
        try:
            return self._d[name]
        except KeyError:
            # Jinja renders an undefined as an empty string, which is a better
            # page than a stack trace or a stray key name in front of a guest.
            raise AttributeError(name) from None

    def __getitem__(self, name):
        return self._d[name]

    def __contains__(self, name):
        return name in self._d

    def get(self, name, default=""):
        return self._d.get(name, default)


def lang() -> str:
    code = session.get("lang")
    if code in Config.LANGUAGES:
        return code
    return Config.DEFAULT_LANG if Config.DEFAULT_LANG in Config.LANGUAGES else "en"


def t() -> Strings:
    return Strings(T.get(lang(), T["en"]))


def loc(obj, field: str) -> str:
    """Localised column with English fallback: loc(product, 'name')."""
    if obj is None:
        return ""
    if lang() == "id":
        return getattr(obj, f"{field}_idn", None) or getattr(obj, f"{field}_en", "") or ""
    return getattr(obj, f"{field}_en", "") or getattr(obj, f"{field}_idn", "") or ""
