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
        # "Free travel" read as a discount the owner might withdraw. The
        # service simply has no travel fee inside its areas — say that.
        "travel_fee": "Travel", "free_travel": "No travel fee",
        "no_travel_fee": "No travel fee within our service areas.",
        "per_person": "per person", "guests": "Guests",
        "we_come_to_you": "We come to you",
        "areas_we_cover": "Areas we cover",
        "service_areas": "Service areas",
        "massage_in": "Massage in",
        "area_intro": "Our therapists come directly to your hotel, villa, "
                      "guesthouse or home.",
        "areas_page_title": "Home Spa Service in Selected Areas of Bali",
        "areas_page_lead": "Enjoy a professional massage without leaving "
                           "your hotel, villa, guesthouse or home. Our "
                           "therapists travel directly to you and bring "
                           "everything needed for your treatment.",
        "our_service_areas": "Our Service Areas",
        "outside_areas": "Staying outside our standard service areas? "
                         "Contact us on WhatsApp and we will check "
                         "availability.",
        "no_travel_fee_area": "No travel fee within our service area.",
        "book_your_treatment": "Book Your Treatment",
        "whatsapp_us": "WhatsApp Us",
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
        "gallery_empty": "Our photo gallery is being put together. In the "
                         "meantime, message us on WhatsApp and we will "
                         "gladly answer any question about a treatment.",
        "try_another_day": "Please choose another day.",
        "use_your_link": "To change or cancel this booking, open the "
                         "link in the confirmation we sent you.",
        "booking_confirmed_now": "Your booking is confirmed. We have sent "
                                 "you a copy — keep this page bookmarked "
                                 "to change or cancel it at any time.",
        "manage_booking": "Manage your booking",
        "manage_intro": "Everything about this booking is handled here. You "
                        "never need to contact your therapist directly.",
        "booking_status": "Status",
        "change_booking": "Change your booking",
        "change_service": "Service",
        "change_time": "Date & time",
        "change_address": "Where we come",
        "save_changes": "Save changes",
        "cancel_booking": "Cancel this booking",
        "cancel_confirm": "Cancel this booking? This cannot be undone.",
        "booking_updated": "Your booking has been updated. We have sent you "
                           "a new confirmation.",
        "booking_cancelled": "Your booking has been cancelled.",
        "booking_not_changeable": "This booking can no longer be changed.",
        "booking_too_late": "This booking starts too soon to change online. "
                            "Please contact us and we will help.",
        "booking_is_cancelled": "This booking was cancelled.",
        "too_late_notice": "Changes and cancellations close 4 hours before "
                           "your treatment. Please contact us for anything "
                           "after that.",
        "keep_current_time": "Keep the current time",
        "current_booking": "Your booking",
        "book_on_whatsapp": "Book on WhatsApp",
        "whatsapp_intro": "The quickest way to book. Message us and we will "
                          "confirm your therapist and time straight away.",
        "message_us_now": "Message us now",
        "homemade": "Made at home in Bali",
        "homemade_note": "We make this ourselves — not bought in to resell.",
        "made_by": "Made by",
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
        "delivery_note": "We deliver throughout our service areas. Pay cash "
                         "on delivery, by bank transfer, or online.",
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
        "travel_fee": "Transport", "free_travel": "Tanpa biaya transport",
        "no_travel_fee": "Tanpa biaya transport di area layanan kami.",
        "per_person": "per orang", "guests": "Tamu",
        "we_come_to_you": "Kami datang ke tempat Anda",
        "areas_we_cover": "Area yang kami layani",
        "service_areas": "Area layanan",
        "massage_in": "Pijat panggilan di",
        "area_intro": "Terapis kami datang langsung ke hotel, vila, "
                      "guesthouse atau rumah Anda.",
        "areas_page_title": "Layanan Home Spa di Area Pilihan Bali",
        "areas_page_lead": "Nikmati pijat profesional tanpa meninggalkan "
                           "hotel, vila, guesthouse atau rumah Anda. "
                           "Terapis kami datang langsung dan membawa "
                           "semua yang diperlukan.",
        "our_service_areas": "Area Layanan Kami",
        "outside_areas": "Menginap di luar area layanan standar kami? "
                         "Hubungi kami di WhatsApp dan kami akan cek "
                         "ketersediaan.",
        "no_travel_fee_area": "Tanpa biaya transport di area layanan kami.",
        "book_your_treatment": "Pesan Perawatan Anda",
        "whatsapp_us": "Hubungi WhatsApp",
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
        "gallery_empty": "Galeri foto kami sedang disiapkan. Sementara "
                         "itu, hubungi kami di WhatsApp untuk pertanyaan "
                         "apa pun tentang perawatan.",
        "try_another_day": "Silakan pilih hari lain.",
        "use_your_link": "Untuk mengubah atau membatalkan pesanan ini, "
                         "buka tautan pada konfirmasi yang kami kirim.",
        "booking_confirmed_now": "Pesanan Anda dikonfirmasi. Salinannya "
                                 "sudah kami kirim — simpan halaman ini "
                                 "untuk mengubah atau membatalkan.",
        "manage_booking": "Kelola pesanan Anda",
        "manage_intro": "Semua hal tentang pesanan ini diatur di sini. Anda "
                        "tidak perlu menghubungi terapis secara langsung.",
        "booking_status": "Status",
        "change_booking": "Ubah pesanan Anda",
        "change_service": "Perawatan",
        "change_time": "Tanggal & jam",
        "change_address": "Kami datang ke mana",
        "save_changes": "Simpan perubahan",
        "cancel_booking": "Batalkan pesanan ini",
        "cancel_confirm": "Batalkan pesanan ini? Tindakan ini tidak dapat "
                          "dibatalkan.",
        "booking_updated": "Pesanan Anda telah diperbarui. Konfirmasi baru "
                           "sudah kami kirim.",
        "booking_cancelled": "Pesanan Anda telah dibatalkan.",
        "booking_not_changeable": "Pesanan ini tidak dapat diubah lagi.",
        "booking_too_late": "Pesanan ini terlalu dekat untuk diubah online. "
                            "Silakan hubungi kami dan kami akan membantu.",
        "booking_is_cancelled": "Pesanan ini telah dibatalkan.",
        "too_late_notice": "Perubahan dan pembatalan ditutup 4 jam sebelum "
                           "perawatan. Untuk setelah itu silakan hubungi kami.",
        "keep_current_time": "Tetap pada jam saat ini",
        "current_booking": "Pesanan Anda",
        "book_on_whatsapp": "Pesan lewat WhatsApp",
        "whatsapp_intro": "Cara tercepat untuk memesan. Kirim pesan dan kami "
                          "langsung konfirmasi terapis dan jam Anda.",
        "message_us_now": "Kirim pesan sekarang",
        "homemade": "Dibuat di rumah, di Bali",
        "homemade_note": "Kami buat sendiri — bukan barang jualan orang lain.",
        "made_by": "Dibuat oleh",
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
        "delivery_note": "Kami kirim ke seluruh area layanan kami. Bayar "
                         "tunai saat pengiriman, transfer bank atau online.",
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
