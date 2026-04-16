#!/usr/bin/env python3
"""
main.py  –  SQ26 Seeding QDArchive, Part 1 pipeline entry point.

Usage
-----
  python main.py              # run QDR + ICPSR, then export CSV
  python main.py --qdr        # QDR only
  python main.py --icpsr      # ICPSR only
  python main.py --stats      # print DB stats only
  python main.py --export     # export DB to CSV only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.database import init_db, get_stats


def _banner(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def run_qdr():
    _banner("SCRAPER: QDR — Qualitative Data Repository (Syracuse)")
    from scrapers.qdr_scraper import scrape_qdr
    scrape_qdr()


def run_icpsr():
    _banner("SCRAPER: ICPSR")
    from scrapers.icpsr_scraper import scrape_icpsr
    scrape_icpsr()


def run_export():
    from export.export_csv import export_all
    _banner("EXPORT: CSV")
    export_all()


def print_stats():
    s = get_stats()
    print("\n── Database Stats ─────────────────────────────────────")
    for k, v in s.items():
        print(f"  {k:<15} {v}")
    print("────────────────────────────────────────────────────────")


def main():
    parser = argparse.ArgumentParser(description="SQ26 QDArchive Part-1 Pipeline")
    parser.add_argument("--qdr",    action="store_true")
    parser.add_argument("--icpsr",  action="store_true")
    parser.add_argument("--stats",  action="store_true")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()

    # Always init DB first (safe to call multiple times)
    init_db()

    if args.stats:
        print_stats()
        return

    if args.export:
        run_export()
        return

    if args.qdr:
        run_qdr()
    elif args.icpsr:
        run_icpsr()
    else:
        run_qdr()
        run_icpsr()

    print_stats()
    run_export()

    print("\n✓  Pipeline complete.")
    print("   Next steps:")
    print("   1. git add 23123639-seeding.db")
    print("   2. git commit -m 'part-1-release: data acquisition complete'")
    print("   3. git tag part-1-release")
    print("   4. git push origin main --tags")


if __name__ == "__main__":
    main()
