"""Create any missing tables and columns.

`create_all` handles new tables. New columns on existing tables are added with
plain ALTER TABLE, which both SQLite and PostgreSQL accept — enough for this
site's shape of change, and it never drops anything.

    python -m scripts.migrate
"""
import sys

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db


def run():
    app = create_app()
    with app.app_context():
        db.create_all()
        insp = inspect(db.engine)
        existing = set(insp.get_table_names())
        added = 0

        for table in db.metadata.sorted_tables:
            if table.name not in existing:
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                col_type = col.type.compile(db.engine.dialect)
                sql = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}'
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"  + {table.name}.{col.name}")
                    added += 1
                except Exception as exc:                       # noqa: BLE001
                    db.session.rollback()
                    print(f"  ! {table.name}.{col.name}: {exc}", file=sys.stderr)

        print(f"Migration done. Tables ensured, {added} column(s) added.")


if __name__ == "__main__":
    run()
