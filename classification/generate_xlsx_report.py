"""
classification/generate_xlsx_report.py
----------------------------------------
Generates the "Project classification table" XLSX for Part 2 submission —
one row per acquired project, matching the reference format:

    repository_id | project_type | project_title | primary_class |
    secondary_class | no_project_files

where primary_class / secondary_class are formatted as
"<ISIC section><division> <division name>" (e.g. "R87 Residential care
activities"), and secondary_class is the runner-up division for projects
that plausibly touch a second ISIC domain (blank if none qualified).

Usage:
    python classification/generate_xlsx_report.py working.db --out 23123639_SQ26_Part2_Classification.xlsx
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT_NAME = "Calibri"
HEADER_FILL = PatternFill("solid", fgColor="1F1F33")
HEADER_FONT = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
BODY_FONT = Font(name=FONT_NAME, size=11)


def _class_label(section, division, division_name):
    if not section or section == "UNCLASSIFIED":
        return "UNCLASSIFIED"
    return f"{section}{division} {division_name}"


def _fetch_rows(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT p.id AS project_id, p.repository_id, p.title AS project_title,
               c.isic_section, c.isic_division, c.division_name,
               c.secondary_isic_section, c.secondary_isic_division, c.secondary_division_name,
               c.project_type,
               (SELECT COUNT(*) FROM FILES f WHERE f.project_id = p.id) AS no_project_files
        FROM PROJECTS p
        LEFT JOIN CLASSIFICATIONS c ON c.project_id = p.id
        ORDER BY p.id
        """
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def build_workbook(db_path: str, out_path: str):
    rows = _fetch_rows(db_path)

    wb = Workbook()
    ws = wb.active
    ws.title = "classification"

    headers = [
        "repository_id", "project_type", "project_title",
        "primary_class", "secondary_class", "no_project_files",
    ]
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r, row in enumerate(rows, start=2):
        primary_class = _class_label(row["isic_section"], row["isic_division"], row["division_name"])
        secondary_class = (
            _class_label(row["secondary_isic_section"], row["secondary_isic_division"],
                         row["secondary_division_name"])
            if row["secondary_isic_division"] else ""
        )

        values = [
            row["repository_id"], row["project_type"] or "NOT_A_PROJECT", row["project_title"],
            primary_class, secondary_class, row["no_project_files"],
        ]
        for c, value in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.font = BODY_FONT
            if c in (1, 6):
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 13
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 55
    ws.column_dimensions["D"].width = 50
    ws.column_dimensions["E"].width = 50
    ws.column_dimensions["F"].width = 16
    ws.freeze_panes = "A2"

    last_row = len(rows) + 1
    last_col = get_column_letter(len(headers))
    tbl = Table(displayName="classification", ref=f"A1:{last_col}{last_row}")
    tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tbl)

    wb.save(out_path)
    print(f"[XLSX] Workbook written to {out_path} ({len(rows)} projects)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to the classified database")
    parser.add_argument("--out", default="23123639_SQ26_Part2_Classification.xlsx")
    args = parser.parse_args()
    build_workbook(args.db_path, args.out)
