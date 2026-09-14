#!/usr/bin/env python3
"""Push the English copy in scripts/copy_en.py onto a database already in use.

Re-running the seed would do this too, but the seed also rewrites prices,
durations and stock back to their starting values, which on a live site means
losing real work. This touches English text only:

  * site settings listed in copy_en.SETTINGS_EN
  * treatment and treatment-group descriptions
  * product short lines and descriptions, and product-group descriptions
  * the "why guests choose us" tiles
  * the FAQ
  * the About and Delivery & Payment pages

It never writes a price, a duration, a slug, a photo, a stock level, or any
Indonesian field.

    python -m scripts.apply_copy            # show what would change
    python -m scripts.apply_copy --write    # change it
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.media import Review  # noqa: E402
from app.models.shop import Product, ProductGroup  # noqa: E402
from app.models.site import FaqItem, Page, SiteSetting  # noqa: E402
from app.models.spa import (Highlight, Treatment,  # noqa: E402
                            TreatmentCategory)

from . import copy_en  # noqa: E402

# Wording the owner has asked never to appear again. Checked at the end so a
# stale sentence somewhere is reported rather than quietly shipped.
BANNED = ["Bali-wide", "wherever you are in Bali", "anywhere in Bali",
          "across Bali", "seluruh Bali", "Free travel",
          "Write your story here", "Certified therapists", "Your healers",
          "Traditional & therapeutic", "Pick your area"]


def _set(row, field, value, changes, label):
    old = getattr(row, field, None) or ""
    if old.strip() == (value or "").strip():
        return
    changes.append((label, old, value))
    setattr(row, field, value)


def run(write: bool):
    app = create_app()
    changes = []

    with app.app_context():
        # ---- site settings
        for key, value in copy_en.SETTINGS_EN.items():
            row = SiteSetting.query.filter_by(key=key).first()
            if not row:
                row = SiteSetting(key=key, value="")
                db.session.add(row)
            _set(row, "value", value, changes, f"setting {key}")

        # ---- treatments and their groups
        for slug, text in copy_en.TREATMENT_GROUP_DESC_EN.items():
            row = TreatmentCategory.query.filter_by(slug=slug).first()
            if row:
                _set(row, "desc_en", text, changes, f"treatment group {slug}")
        for slug, text in copy_en.TREATMENT_DESC_EN.items():
            row = Treatment.query.filter_by(slug=slug).first()
            if row:
                _set(row, "desc_en", text, changes, f"treatment {slug}")

        # ---- products and their groups
        for slug, text in copy_en.PRODUCT_GROUP_DESC_EN.items():
            row = ProductGroup.query.filter_by(slug=slug).first()
            if row:
                _set(row, "desc_en", text, changes, f"product group {slug}")
        for slug, (short, desc) in copy_en.PRODUCT_COPY_EN.items():
            row = Product.query.filter_by(slug=slug).first()
            if row:
                _set(row, "short_en", short, changes, f"product {slug} (short)")
                _set(row, "desc_en", desc, changes, f"product {slug}")

        # ---- why guests choose us
        for old_title, icon, title, text in copy_en.HIGHLIGHTS_EN:
            row = (Highlight.query.filter_by(title_en=old_title).first()
                   or Highlight.query.filter_by(title_en=title).first())
            if row:
                _set(row, "icon", icon, changes, f"tile {title} (icon)")
                _set(row, "title_en", title, changes, f"tile {old_title}")
                _set(row, "text_en", text, changes, f"tile {title} (text)")

        # ---- FAQ. Entries keyed on a sentinel are new questions.
        for i, (old_q, question, answer) in enumerate(copy_en.FAQ_EN):
            row = (FaqItem.query.filter_by(question_en=old_q).first()
                   or FaqItem.query.filter_by(question_en=question).first())
            if not row:
                row = FaqItem(question_en=question, is_visible=True)
                db.session.add(row)
                changes.append((f"FAQ (new) {question}", "", answer))
            else:
                _set(row, "question_en", question, changes, f"FAQ {old_q}")
                _set(row, "answer_en", answer, changes, f"FAQ {question}")
            row.answer_en = answer
            row.question_en = question
            row.sort_order = i * 10

        # ---- sample reviews written during the build, never genuine. One
        # names Canggu, which is not a service area; another names a package
        # that is not on the menu. Only these exact rows are hidden, so a real
        # review entered in admin is never touched.
        for author, opening in copy_en.PLACEHOLDER_REVIEWS:
            for row in Review.query.filter_by(author_name=author).all():
                if opening.lower() in (row.text or "").lower() \
                        and row.is_approved:
                    row.is_approved = False
                    changes.append((f"review by {author} — hidden, not genuine",
                                    (row.text or "")[:80], "(not shown)"))

        # ---- pages
        for slug, (title, body) in copy_en.PAGES_EN.items():
            row = Page.query.filter_by(slug=slug).first()
            if not row:
                row = Page(slug=slug, title_en=title, is_visible=True,
                           show_in_menu=True)
                db.session.add(row)
                changes.append((f"page (new) {slug}", "", title))
            _set(row, "title_en", title, changes, f"page {slug} (title)")
            _set(row, "body_en", body, changes, f"page {slug}")

        # Scanned while the changes are still in the session, so a dry run
        # reports what would be left afterwards rather than what is there now.
        db.session.flush()
        leftovers = _scan_for_banned()

        if write:
            db.session.commit()
        else:
            db.session.rollback()

    for label, old, new in changes:
        print(f"  {label}")
        if old:
            print(f"      was: {old[:90]}")
        print(f"      now: {(new or '')[:90]}")
    print(f"\n{len(changes)} change(s) "
          + ("applied." if write else "would be applied. Re-run with --write."))

    if leftovers:
        print("\nWould still carry wording that should be gone:"
              if not write else "\nStill carrying wording that should be gone:")
        for where, phrase in leftovers:
            print(f"  {where}: “{phrase}”")
        print("These were typed by hand rather than seeded, so this script "
              "leaves them alone. Edit them in admin.")
    else:
        print("No retired wording anywhere in the English text.")


def _scan_for_banned():
    """English text in the database still using retired wording."""
    found = []
    for row in SiteSetting.query.all():
        if row.key.endswith("_idn"):
            continue
        for phrase in BANNED:
            if phrase.lower() in (row.value or "").lower():
                found.append((f"setting {row.key}", phrase))
    for model, fields, name in [
            (Treatment, ["desc_en", "name_en"], "treatment"),
            (TreatmentCategory, ["desc_en"], "treatment group"),
            (Product, ["short_en", "desc_en"], "product"),
            (ProductGroup, ["desc_en"], "product group"),
            (Page, ["body_en", "title_en"], "page"),
            (FaqItem, ["question_en", "answer_en"], "FAQ"),
            (Highlight, ["title_en", "text_en"], "tile")]:
        for row in model.query.all():
            for field in fields:
                text = (getattr(row, field, "") or "").lower()
                for phrase in BANNED:
                    if phrase.lower() in text:
                        ident = getattr(row, "slug", None) or \
                            getattr(row, "title_en", None) or row.id
                        found.append((f"{name} {ident} ({field})", phrase))
    return found


if __name__ == "__main__":
    run("--write" in sys.argv)
