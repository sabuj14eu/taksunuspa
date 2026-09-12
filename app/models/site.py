from datetime import datetime
from ..extensions import db


class SiteSetting(db.Model):
    """Key-value store: phone, address, socials, hero texts, bank details.
    Injected into every template — change the phone once, it updates
    everywhere including the JSON-LD that Google reads."""
    __tablename__ = "site_settings"
    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.Text, default="")

    @staticmethod
    def all_dict():
        return {s.key: s.value for s in SiteSetting.query.all()}

    @staticmethod
    def put(key, value):
        row = db.session.get(SiteSetting, key)
        if row:
            row.value = value or ""
        else:
            db.session.add(SiteSetting(key=key, value=value or ""))


class Page(db.Model):
    """CMS page at /p/<slug> — About, Terms, Shipping, Privacy."""
    __tablename__ = "pages"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    title_en = db.Column(db.String(140), nullable=False)
    title_idn = db.Column(db.String(140))
    body_en = db.Column(db.Text, default="")
    body_idn = db.Column(db.Text, default="")
    seo_title = db.Column(db.String(180))
    seo_desc = db.Column(db.String(320))
    is_visible = db.Column(db.Boolean, default=True)
    show_in_menu = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)


class MenuItem(db.Model):
    """Head navigation, fully admin-managed."""
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    label_en = db.Column(db.String(60), nullable=False)
    label_idn = db.Column(db.String(60))
    url = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(8), default="")
    style = db.Column(db.String(10), default="normal")   # normal | cta
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class FaqItem(db.Model):
    __tablename__ = "faq_items"
    id = db.Column(db.Integer, primary_key=True)
    question_en = db.Column(db.String(240))
    question_idn = db.Column(db.String(240))
    answer_en = db.Column(db.Text, default="")
    answer_idn = db.Column(db.Text, default="")
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
