# -*- coding: utf-8 -*-
"""Image upload, gallery and rating aggregation.

Uploads are re-encoded to WebP with a 480px thumbnail. Phone photos straight
from WhatsApp are several megabytes; serving those as product cards would
sink the page speed score the SEO work is meant to lift.
"""
import os
import secrets
from collections import defaultdict

from flask import current_app
from sqlalchemy import func

from ..extensions import db
from ..models.media import MediaImage, Review

ALLOWED = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_BYTES = 8 * 1024 * 1024
MAX_EDGE = 1920
THUMB_EDGE = 480
WEBP_QUALITY = 82


def upload_dir():
    d = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(d, exist_ok=True)
    return d


def _compress(stream, base):
    """(url, thumb_url, width, height, size_kb) or None when Pillow can't
    read the file — the caller then stores the original bytes."""
    try:
        from PIL import Image, ImageOps
        im = Image.open(stream)
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.thumbnail((MAX_EDGE, MAX_EDGE))
        main_path = os.path.join(upload_dir(), f"{base}.webp")
        im.save(main_path, "WEBP", quality=WEBP_QUALITY)
        th = im.copy()
        th.thumbnail((THUMB_EDGE, THUMB_EDGE))
        th.save(os.path.join(upload_dir(), f"{base}_t.webp"), "WEBP",
                quality=WEBP_QUALITY)
        kb = max(1, os.path.getsize(main_path) // 1024)
        return (f"/static/uploads/{base}.webp",
                f"/static/uploads/{base}_t.webp", im.width, im.height, kb)
    except Exception:
        return None


def save_upload(file_storage, entity_type: str, entity_id: int, caption="",
                alt_en="", alt_idn=""):
    name = (file_storage.filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ALLOWED:
        return None
    file_storage.stream.seek(0, os.SEEK_END)
    if file_storage.stream.tell() > MAX_BYTES:
        return None
    file_storage.stream.seek(0)

    base = secrets.token_hex(10)
    packed = _compress(file_storage.stream, base)
    if packed:
        url, thumb_url, width, height, size_kb = packed
    else:
        fname = f"{base}.{ext}"
        file_storage.stream.seek(0)
        file_storage.save(os.path.join(upload_dir(), fname))
        url, thumb_url = f"/static/uploads/{fname}", None
        width = height = size_kb = None

    first = not MediaImage.query.filter_by(entity_type=entity_type,
                                           entity_id=entity_id).first()
    img = MediaImage(entity_type=entity_type, entity_id=entity_id, url=url,
                     thumb_url=thumb_url, width=width, height=height,
                     size_kb=size_kb, alt_en=alt_en[:200], alt_idn=alt_idn[:200],
                     caption=caption[:160], is_cover=first)
    db.session.add(img)
    db.session.commit()
    return img


def delete_image(img: MediaImage):
    for url in (img.url, img.thumb_url):
        if not url:
            continue
        try:
            os.remove(os.path.join(current_app.root_path,
                                   *url.strip("/").split("/")))
        except OSError:
            pass
    db.session.delete(img)
    db.session.commit()


def set_cover(img: MediaImage):
    (MediaImage.query
     .filter_by(entity_type=img.entity_type, entity_id=img.entity_id)
     .update({"is_cover": False}))
    img.is_cover = True
    db.session.commit()


def gallery(entity_type: str, entity_id: int):
    return (MediaImage.query.filter_by(entity_type=entity_type,
                                       entity_id=entity_id)
            .order_by(MediaImage.is_cover.desc(), MediaImage.sort_order,
                      MediaImage.id).all())


def cover_url(entity_type: str, entity_id: int, fallback=None):
    img = (MediaImage.query.filter_by(entity_type=entity_type,
                                      entity_id=entity_id)
           .order_by(MediaImage.is_cover.desc(), MediaImage.sort_order,
                     MediaImage.id).first())
    if not img:
        return fallback
    return img.thumb_url or img.url


def covers_for(entity_type: str, ids):
    """One query for a whole product grid."""
    if not ids:
        return {}
    rows = (MediaImage.query
            .filter(MediaImage.entity_type == entity_type,
                    MediaImage.entity_id.in_(list(ids)))
            .order_by(MediaImage.is_cover.desc(), MediaImage.sort_order,
                      MediaImage.id).all())
    out = {}
    for r in rows:
        out.setdefault(r.entity_id, r.thumb_url or r.url)
    return out


# ---------- reviews ----------

def reviews_for(entity_type: str, entity_id: int, limit=20):
    return (Review.query.filter_by(entity_type=entity_type,
                                   entity_id=entity_id, is_approved=True)
            .order_by(Review.created_at.desc()).limit(limit).all())


def rating_of(entity_type: str, entity_id: int):
    """(average_1_to_5, count) — (None, 0) when nothing is approved yet."""
    row = (db.session.query(func.avg(Review.rating), func.count(Review.id))
           .filter(Review.entity_type == entity_type,
                   Review.entity_id == entity_id,
                   Review.is_approved.is_(True)).first())
    if not row or not row[1]:
        return None, 0
    return round(float(row[0]), 1), int(row[1])


def ratings_for(entity_type: str, ids):
    if not ids:
        return {}
    rows = (db.session.query(Review.entity_id, func.avg(Review.rating),
                             func.count(Review.id))
            .filter(Review.entity_type == entity_type,
                    Review.entity_id.in_(list(ids)),
                    Review.is_approved.is_(True))
            .group_by(Review.entity_id).all())
    out = defaultdict(lambda: (None, 0))
    for eid, avg, cnt in rows:
        out[eid] = (round(float(avg), 1), int(cnt))
    return out
