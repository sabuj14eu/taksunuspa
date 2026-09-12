"""Photos and reviews.

entity_type: product | product_group | treatment | treatment_category | site
"""
from datetime import datetime
from ..extensions import db

ENTITY_TYPES = ["product", "product_group", "treatment", "treatment_category",
                "site"]


class MediaImage(db.Model):
    __tablename__ = "media_images"
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(24), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(400), nullable=False)      # /static/uploads/x.webp
    thumb_url = db.Column(db.String(400))                # 480px WebP
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    size_kb = db.Column(db.Integer)
    alt_en = db.Column(db.String(200))
    alt_idn = db.Column(db.String(200))
    caption = db.Column(db.String(160))
    is_cover = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.Index("ix_media_entity", "entity_type", "entity_id"),)


class Review(db.Model):
    """Left by someone holding a real booking or order code, then moderated."""
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(24), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    ref_code = db.Column(db.String(8))
    author_name = db.Column(db.String(80))
    rating = db.Column(db.Integer, nullable=False)       # 1..5
    text = db.Column(db.String(1000))
    reply = db.Column(db.String(1000))
    lang = db.Column(db.String(3), default="en")
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.Index("ix_review_entity", "entity_type", "entity_id"),)
