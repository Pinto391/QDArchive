"""
export/export_csv.py  –  Export all DB tables (Part 1 + Part 2) to CSV files.
Run:  python export/export_csv.py
"""

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import get_db_path, get_connection

TABLES = [
    "REPOSITORIES", "PROJECTS", "FILES", "KEYWORDS", "PERSON_ROLE", "LICENSES",
    "CLASSIFICATIONS", "TAGS", "FILE_CLASSIFICATIONS",
]
OUT_DIR = Path(__file__).parent / "csv"


def export_all(db_path=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if db_path is None:
        conn = get_connection()
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

    existing_tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    for table in TABLES:
        if table not in existing_tables:
            print(f"  [skip] {table} — not present in this DB")
            continue
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  [skip] {table} — empty")
            continue
        out = OUT_DIR / f"{table.lower()}.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows([dict(r) for r in rows])
        print(f"  [csv] {table} → {out}  ({len(rows)} rows)")

    conn.close()
    print("Export complete.")


if __name__ == "__main__":
    export_all()
