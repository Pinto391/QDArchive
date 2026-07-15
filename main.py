#!/usr/bin/env python3
"""
main.py  –  SQ26 Seeding QDArchive, Part 1 + Part 2 pipeline entry point.

Usage
-----
  # Part 1: Data Acquisition
  python main.py                    # run QDR + ICPSR, then export CSV
  python main.py --qdr              # QDR only
  python main.py --icpsr            # ICPSR only
  python main.py --stats            # print DB stats only
  python main.py --export           # export DB to CSV only

  # Part 2: Data Classification
  python main.py --merge a.db b.db --out working.db   # merge student DBs
  python main.py --classify                            # classify 23123639-seeding.db
  python main.py --classify --db working.db             # classify a specific DB
  python main.py --report                                # print classification stats
  python main.py --report --db working.db --report-out report.txt
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.database import init_db, get_stats, get_db_path


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


def run_export(db_path=None):
    from export.export_csv import export_all
    _banner("EXPORT: CSV")
    export_all(db_path)


def run_merge(dbs, out):
    from classification.merge_databases import merge_databases
    _banner("PART 2 — STEP 1: MERGE DATABASES")
    merge_databases(dbs, out)


def run_classify(db_path):
    from classification.classifier import run_classifier, run_file_classifier
    _banner("PART 2 — STEP 2/3: CLASSIFY PROJECTS + FILES (ISIC Rev. 5)")
    run_classifier(db_path)
    run_file_classifier(db_path)


def run_report(db_path, out=None):
    from classification.report import generate_report
    _banner("PART 2 — STEP 4: CLASSIFICATION STATISTICS REPORT")
    report = generate_report(db_path)
    print(report)
    if out:
        Path(out).write_text(report, encoding="utf-8")
        print(f"\n[Report written to {out}]")


def print_stats():
    s = get_stats()
    print("\n── Database Stats ─────────────────────────────────────")
    for k, v in s.items():
        print(f"  {k:<15} {v}")
    print("────────────────────────────────────────────────────────")


def main():
    parser = argparse.ArgumentParser(description="SQ26 QDArchive Pipeline — Part 1 + Part 2")

    # Part 1
    parser.add_argument("--qdr",    action="store_true", help="Run QDR scraper only")
    parser.add_argument("--icpsr",  action="store_true", help="Run ICPSR scraper only")
    parser.add_argument("--stats",  action="store_true", help="Print DB stats and exit")
    parser.add_argument("--export", action="store_true", help="Export DB to CSV and exit")

    # Part 2
    parser.add_argument("--merge", nargs="+", metavar="DB", help="Merge these .db files")
    parser.add_argument("--out", default="working.db", help="Output path for --merge")
    parser.add_argument("--classify", action="store_true", help="Run ISIC classifier (projects + files)")
    parser.add_argument("--report", action="store_true", help="Print classification stats report")
    parser.add_argument("--db", default=None, help="DB to use for --classify / --report / --export "
                                                     "(default: 23123639-seeding.db)")
    parser.add_argument("--report-out", default=None, help="Write report to this file")

    args = parser.parse_args()

    # ── Part 2 commands (don't need Part 1 DB init) ───────────────────────
    if args.merge:
        run_merge(args.merge, args.out)
        return

    if args.classify:
        db_path = args.db or str(get_db_path())
        run_classify(db_path)
        return

    if args.report:
        db_path = args.db or str(get_db_path())
        run_report(db_path, args.report_out)
        return

    # Always init DB first (safe to call multiple times)
    init_db()

    if args.stats:
        print_stats()
        return

    if args.export:
        run_export(args.db)
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
