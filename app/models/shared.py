"""SEO plumbing and the admin audit trail."""
from datetime import datetime
from ..extensions import db


class Redirect(db.Model):
    """Slug changed in admin -> 301, so ranked URLs never 404."""
    __tablename__ = "redirects"
    id = db.Column(db.Integer, primary_key=True)
    old_path = db.Column(db.String(300), unique=True, nullable=False)
    new_path = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PageView(db.Model):
    """First-party daily counter — no third-party script, no cookie banner."""
    __tablename__ = "page_views"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(300), nullable=False)
    day = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=0)
    __table_args__ = (db.Index("ix_pv_path_day", "path", "day"),)


class SeoPageMeta(db.Model):
    """Admin-set title/description for a fixed route such as / or /products."""
    __tablename__ = "seo_page_meta"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(200), unique=True, nullable=False)
    title_en = db.Column(db.String(200))
    title_idn = db.Column(db.String(200))
    desc_en = db.Column(db.String(320))
    desc_idn = db.Column(db.String(320))
    noindex = db.Column(db.Boolean, default=False)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(80))
    action = db.Column(db.String(40))
    entity = db.Column(db.String(60))
    detail = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
