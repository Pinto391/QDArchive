"""
export/export_csv.py  –  Export all DB tables to CSV files.
Run:  python export/export_csv.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import get_db_path, get_connection

TABLES  = ["REPOSITORIES", "PROJECTS", "FILES", "KEYWORDS", "PERSON_ROLE", "LICENSES"]
OUT_DIR = Path(__file__).parent / "csv"


def export_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()

    for table in TABLES:
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
