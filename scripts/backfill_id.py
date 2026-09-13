#!/usr/bin/env python3
"""Fill in missing Indonesian text on a database that is already live.

The seed sets both languages now, but re-running the seed would overwrite
whatever has since been edited in admin. This script only ever writes into a
field that is empty, so anything typed by hand is safe. Run it once after
deploying, then never again unless a report below says something is missing.

    python scripts/backfill_id.py            # show what is missing
    python scripts/backfill_id.py --write    # fill the blanks
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.spa import Treatment, TreatmentCategory  # noqa: E402

# Keyed by slug so a renamed treatment is skipped rather than mistranslated.
CATEGORY_DESC = {
    "massage":
        "Sentuhan tradisional Bali, minyak hangat, tekanan tanpa terburu-buru "
        "— di kamar Anda sendiri.",
    "body-treatment":
        "Lulur, masker dan mandi bunga dari bahan-bahan alami Bali.",
    "packages":
        "Kombinasi lebih panjang untuk pasangan dan liburan setengah hari.",
}

TREATMENT_DESC = {
    "balinese-massage":
        "Pijat seluruh tubuh tradisional dengan minyak aromatik untuk "
        "melancarkan aliran energi dan menenangkan. Usapan panjang, tekanan "
        "telapak tangan dan minyak kelapa hangat, dari telapak kaki hingga "
        "bahu.",
    "deep-tissue-massage":
        "Tekanan kuat dan terarah untuk pemulihan otot dan pelepasan "
        "mendalam. Pilihan tepat setelah berselancar, berlatih atau "
        "penerbangan panjang.",
    "couple-massage":
        "Dua terapis, berdampingan, di kamar Anda sendiri. Harga per orang "
        "untuk ritual berdua.",
    "foot-massage":
        "Refleksi untuk kaki yang lelah dengan minyak herbal hangat. Pijat "
        "titik tekan pada telapak kaki dan betis.",
}


def run(write: bool):
    app = create_app()
    with app.app_context():
        filled, skipped, unknown = [], [], []

        for model, table in [(TreatmentCategory, CATEGORY_DESC),
                             (Treatment, TREATMENT_DESC)]:
            for row in model.query.all():
                if (row.desc_idn or "").strip():
                    continue                      # already written, leave it
                text = table.get(row.slug)
                if not text:
                    unknown.append(f"{model.__name__} '{row.slug}'")
                    continue
                if write:
                    row.desc_idn = text
                    filled.append(f"{model.__name__} '{row.slug}'")
                else:
                    skipped.append(f"{model.__name__} '{row.slug}'")

        if write:
            db.session.commit()

        # Anything still English-only after this needs a human.
        remaining = []
        for model, fields in [(Treatment, ["name", "desc"]),
                              (TreatmentCategory, ["name", "desc"])]:
            for row in model.query.all():
                for f in fields:
                    if getattr(row, f + "_en", None) and \
                            not (getattr(row, f + "_idn", None) or "").strip():
                        remaining.append(f"{model.__name__} '{row.slug}'.{f}")

    if write:
        print(f"Filled {len(filled)} field(s): {filled or '—'}")
    else:
        print(f"Would fill {len(skipped)} field(s): {skipped or '—'}")
        print("Re-run with --write to apply.")
    if unknown:
        print(f"\nNo Indonesian text on file for: {unknown}\n"
              "  These were added or renamed after this script was written — "
              "translate them in Admin -> Treatments.")
    if remaining:
        print(f"\nStill English-only: {remaining}")
    else:
        print("\nEvery treatment and group has Indonesian text.")


if __name__ == "__main__":
    run("--write" in sys.argv)
