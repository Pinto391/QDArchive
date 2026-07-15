"""
classification/report.py
-------------------------
Part 2, Step 4: Report statistics — how much qualitative data was found,
and the distribution of ISIC sections/divisions, at both project and
individual-file level.

Usage:
    python classification/report.py path/to/db.db
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_report(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    lines = []
    lines.append("=" * 64)
    lines.append("  SQ26 PART 2 -- CLASSIFICATION STATISTICS REPORT")
    lines.append("=" * 64)

    # ── Overall volume ────────────────────────────────────────────────────
    n_projects = conn.execute("SELECT COUNT(*) FROM PROJECTS").fetchone()[0]
    n_files    = conn.execute("SELECT COUNT(*) FROM FILES").fetchone()[0]
    n_success  = conn.execute("SELECT COUNT(*) FROM FILES WHERE status='SUCCEEDED'").fetchone()[0]
    n_repos    = conn.execute("SELECT COUNT(*) FROM REPOSITORIES").fetchone()[0]

    lines.append("\n-- Overall Volume --")
    lines.append(f"  Repositories covered:          {n_repos}")
    lines.append(f"  Total projects found:          {n_projects}")
    lines.append(f"  Total files recorded:          {n_files}")
    lines.append(f"  Files successfully downloaded: {n_success} ({(n_success/n_files*100 if n_files else 0):.1f}%)")

    # ── Project classification coverage ──────────────────────────────────
    n_classified = conn.execute(
        "SELECT COUNT(*) FROM CLASSIFICATIONS WHERE isic_section != 'UNCLASSIFIED'"
    ).fetchone()[0]
    n_unclassified = conn.execute(
        "SELECT COUNT(*) FROM CLASSIFICATIONS WHERE isic_section = 'UNCLASSIFIED'"
    ).fetchone()[0]
    n_total_classified_rows = conn.execute("SELECT COUNT(*) FROM CLASSIFICATIONS").fetchone()[0]

    lines.append("\n-- Project Classification Coverage --")
    lines.append(f"  Projects classified:           {n_classified} "
                 f"({(n_classified/n_total_classified_rows*100 if n_total_classified_rows else 0):.1f}%)")
    lines.append(f"  Projects unclassified:         {n_unclassified} "
                 f"({(n_unclassified/n_total_classified_rows*100 if n_total_classified_rows else 0):.1f}%)")

    # ── Distribution by ISIC Section (projects) ──────────────────────────
    lines.append("\n-- Project Distribution by ISIC Rev. 5 Section --")
    section_rows = conn.execute(
        """
        SELECT isic_section, section_name, COUNT(*) as cnt
        FROM CLASSIFICATIONS
        GROUP BY isic_section, section_name
        ORDER BY cnt DESC
        """
    ).fetchall()
    for row in section_rows:
        pct = (row["cnt"] / n_total_classified_rows * 100) if n_total_classified_rows else 0
        lines.append(f"  [{row['isic_section']:>2}] {row['section_name']:<55} {row['cnt']:>4} ({pct:5.1f}%)")

    # ── Distribution by ISIC Division (projects) ─────────────────────────
    lines.append("\n-- Project Distribution by ISIC Rev. 5 Division --")
    division_rows = conn.execute(
        """
        SELECT isic_division, division_name, isic_section, COUNT(*) as cnt,
               AVG(confidence) as avg_conf
        FROM CLASSIFICATIONS
        GROUP BY isic_division, division_name, isic_section
        ORDER BY cnt DESC
        """
    ).fetchall()
    for row in division_rows:
        pct = (row["cnt"] / n_total_classified_rows * 100) if n_total_classified_rows else 0
        lines.append(
            f"  [{row['isic_section']}/{row['isic_division']}] "
            f"{row['division_name']:<60} {row['cnt']:>4} ({pct:5.1f}%)  "
            f"avg_confidence={row['avg_conf']:.2f}"
        )

    # ── File-level classification coverage ───────────────────────────────
    has_file_classifications = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='FILE_CLASSIFICATIONS'"
    ).fetchone()

    if has_file_classifications:
        n_file_rows = conn.execute("SELECT COUNT(*) FROM FILE_CLASSIFICATIONS").fetchone()[0]
        n_from_content = conn.execute(
            "SELECT COUNT(*) FROM FILE_CLASSIFICATIONS WHERE method='RULE_BASED_KEYWORDS'"
        ).fetchone()[0]
        n_inherited = conn.execute(
            "SELECT COUNT(*) FROM FILE_CLASSIFICATIONS WHERE method='NO_TEXT_CONTENT'"
        ).fetchone()[0]

        lines.append("\n-- File-Level Classification Coverage --")
        lines.append(f"  Files classified (each downloaded file has its own class): {n_file_rows}")
        lines.append(f"  Classified directly from file content:  {n_from_content} "
                     f"({(n_from_content/n_file_rows*100 if n_file_rows else 0):.1f}%)")
        lines.append(f"  Inherited from parent project (no extractable text, "
                     f"e.g. media/binary files): {n_inherited} "
                     f"({(n_inherited/n_file_rows*100 if n_file_rows else 0):.1f}%)")

        lines.append("\n-- File Distribution by ISIC Rev. 5 Division --")
        file_division_rows = conn.execute(
            """
            SELECT isic_division, division_name, isic_section, COUNT(*) as cnt
            FROM FILE_CLASSIFICATIONS
            GROUP BY isic_division, division_name, isic_section
            ORDER BY cnt DESC
            """
        ).fetchall()
        for row in file_division_rows:
            pct = (row["cnt"] / n_file_rows * 100) if n_file_rows else 0
            lines.append(
                f"  [{row['isic_section']}/{row['isic_division']}] "
                f"{row['division_name']:<60} {row['cnt']:>4} ({pct:5.1f}%)"
            )

    # ── Top tags ──────────────────────────────────────────────────────────
    lines.append("\n-- Top 20 Tags (for searching) --")
    tag_rows = conn.execute(
        """
        SELECT tag, COUNT(*) as cnt
        FROM TAGS
        GROUP BY tag
        ORDER BY cnt DESC
        LIMIT 20
        """
    ).fetchall()
    for row in tag_rows:
        lines.append(f"  {row['tag']:<40} {row['cnt']:>4}")

    # ── License distribution ─────────────────────────────────────────────
    lines.append("\n-- License Distribution --")
    lic_rows = conn.execute(
        "SELECT license, COUNT(*) as cnt FROM LICENSES GROUP BY license ORDER BY cnt DESC"
    ).fetchall()
    for row in lic_rows:
        lines.append(f"  {row['license']:<20} {row['cnt']:>4}")

    # ── Download method distribution ─────────────────────────────────────
    lines.append("\n-- Download Method Distribution --")
    method_rows = conn.execute(
        "SELECT download_method, COUNT(*) as cnt FROM PROJECTS GROUP BY download_method"
    ).fetchall()
    for row in method_rows:
        lines.append(f"  {row['download_method']:<15} {row['cnt']:>4}")

    lines.append("\n" + "=" * 64)

    conn.close()
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to classified database")
    parser.add_argument("--out", default=None, help="Optional path to write report to a file")
    args = parser.parse_args()

    report = generate_report(args.db_path)
    print(report)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\n[Report written to {args.out}]")
