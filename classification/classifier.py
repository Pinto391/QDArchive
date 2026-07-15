"""
classification/classifier.py
-----------------------------
Part 2, Step 2 & 3: Develop and run a classifier over the acquired data,
at both project and individual-file granularity.

Per the professor's spec:
  - Uses both the base data (the file) and the metadata
  - Uses ISIC Rev. 5, going down two levels (division, not just section)
  - Also creates tags for searching
Per Dirk's meeting notes (2026-04-17):
  - Each QDA_PROJECT should have a class, AND each primary data file inside
    a project should also have a class.

Approach — rule-based keyword matching (transparent, reproducible, no
external ML dependency, and auditable by the professor):

  1. Project level: build a text blob per project from title + description +
     keywords + file extensions + a sample of extracted text from that
     project's successfully downloaded files (via classification.text_extract).
  2. File level: build a text blob per successfully downloaded file from its
     own extracted text; files with no extractable text (media/binary, or
     failed downloads) fall back to the parent project's classification.
  3. Score a blob against every division's keyword-hint list (substring
     matching). Assign the division with the highest score; below a minimum
     threshold, mark "UNCLASSIFIED".
  4. Confidence = matched_keyword_count / total_keywords_for_that_division
     (capped at 1.0).
  5. Every matched keyword across ALL divisions (not just the winning one)
     is also stored as a searchable TAG.

This is intentionally simple and transparent rather than a black-box ML
model, matching the seminar's emphasis on auditable, reproducible pipelines.
"""

import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.isic_taxonomy import all_divisions
from classification.text_extract import extract_text

MIN_SCORE_THRESHOLD = 1  # at least 1 keyword hit required to classify

DATA_ROOT = Path(__file__).parent.parent / "data"

# Budget for project-level file-content sampling: read at most this many
# files per project, this many characters each, to bound classification time
# across a corpus with hundreds of PDFs.
PROJECT_SAMPLE_FILES = 3
PROJECT_SAMPLE_CHARS_PER_FILE = 4000

# Budget for direct per-file classification.
FILE_SAMPLE_CHARS = 8000


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())


def _build_metadata_blob(title, description, keywords, file_types) -> str:
    parts = [title or "", description or ""]
    parts.extend(keywords or [])
    parts.extend(file_types or [])
    return " ".join(parts)


def resolve_file_path(project_row, file_row) -> Path:
    """Reconstruct the on-disk path for a FILES row, matching the layout the
    scrapers write to: data/<repository_folder>/<project_folder>/<file_name>
    (download_version_folder exists in the schema but isn't used by either
    scraper's download path today)."""
    return (
        DATA_ROOT
        / project_row["download_repository_folder"]
        / project_row["download_project_folder"]
        / file_row["file_name"]
    )


def classify_text(blob: str):
    """
    Score blob against every division's keyword hints.
    Returns (section, division, section_name, division_name, confidence,
             matched_tags:set).
    """
    blob = _normalise(blob)
    best = None
    all_matched_tags = set()

    for sec_code, sec_name, div_code, div_name, keywords in all_divisions():
        if not keywords:
            continue
        matches = [kw for kw in keywords if kw in blob]
        if matches:
            all_matched_tags.update(matches)
        score = len(matches)
        if score >= MIN_SCORE_THRESHOLD:
            confidence = min(score / max(len(keywords), 1), 1.0)
            if best is None or score > best[0]:
                best = (score, sec_code, div_code, sec_name, div_name, confidence)

    if best is None:
        return ("UNCLASSIFIED", "00", "Unclassified", "Unclassified", 0.0, all_matched_tags)

    _, sec_code, div_code, sec_name, div_name, confidence = best
    return (sec_code, div_code, sec_name, div_name, confidence, all_matched_tags)


def _sample_project_file_text(conn, project_id: int, project_row) -> str:
    file_rows = conn.execute(
        "SELECT * FROM FILES WHERE project_id=? AND status='SUCCEEDED' LIMIT ?",
        (project_id, PROJECT_SAMPLE_FILES),
    ).fetchall()

    chunks = []
    for file_row in file_rows:
        path = resolve_file_path(project_row, file_row)
        text = extract_text(path, max_chars=PROJECT_SAMPLE_CHARS_PER_FILE)
        if text:
            chunks.append(text)
    return " ".join(chunks)


def _apply_schema_part2(conn):
    schema_part2 = Path(__file__).parent.parent / "db" / "schema_part2.sql"
    conn.executescript(schema_part2.read_text(encoding="utf-8"))
    conn.commit()


def run_classifier(db_path: str):
    """Project-level classification: reads PROJECTS (+ KEYWORDS + FILES,
    including a sample of actual file content) from db_path, classifies each
    project, and writes results into CLASSIFICATIONS + TAGS."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    _apply_schema_part2(conn)
    conn.execute("DELETE FROM CLASSIFICATIONS")
    conn.execute("DELETE FROM TAGS")
    conn.commit()

    projects = conn.execute("SELECT * FROM PROJECTS").fetchall()
    print(f"[CLASSIFIER] {len(projects)} projects to classify...")

    now = datetime.now(timezone.utc).isoformat()
    classified_count = 0
    unclassified_count = 0

    for proj in projects:
        pid = proj["id"]

        kw_rows = conn.execute(
            "SELECT keyword FROM KEYWORDS WHERE project_id=?", (pid,)
        ).fetchall()
        keywords = [r["keyword"] for r in kw_rows]

        file_rows = conn.execute(
            "SELECT file_type FROM FILES WHERE project_id=?", (pid,)
        ).fetchall()
        file_types = [r["file_type"] for r in file_rows]

        metadata_blob = _build_metadata_blob(proj["title"], proj["description"], keywords, file_types)
        file_text = _sample_project_file_text(conn, pid, proj)
        blob = metadata_blob + " " + file_text

        sec, div, sec_name, div_name, confidence, tags = classify_text(blob)

        conn.execute(
            """
            INSERT INTO CLASSIFICATIONS (
                project_id, isic_section, isic_division,
                section_name, division_name, confidence, method, classified_date
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (pid, sec, div, sec_name, div_name, confidence, "RULE_BASED_KEYWORDS", now),
        )

        for tag in tags:
            conn.execute(
                "INSERT INTO TAGS (project_id, tag) VALUES (?,?)", (pid, tag)
            )

        if sec == "UNCLASSIFIED":
            unclassified_count += 1
        else:
            classified_count += 1

        if (classified_count + unclassified_count) % 25 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f"[CLASSIFIER] Projects done. Classified: {classified_count}, Unclassified: {unclassified_count}")
    return classified_count, unclassified_count


def run_file_classifier(db_path: str):
    """File-level classification: for every SUCCEEDED file on disk, extract
    its own text and classify it directly. Files with no extractable text
    (media/binary, or files never downloaded) inherit the parent project's
    classification instead, tagged with method='NO_TEXT_CONTENT' so the
    report can state file-type coverage honestly."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    _apply_schema_part2(conn)
    conn.execute("DELETE FROM FILE_CLASSIFICATIONS")
    conn.commit()

    files = conn.execute("SELECT * FROM FILES WHERE status='SUCCEEDED'").fetchall()
    print(f"[FILE CLASSIFIER] {len(files)} downloaded files to classify...")

    now = datetime.now(timezone.utc).isoformat()
    with_content = 0
    inherited = 0

    # Cache each project's own classification so "no text content" files can
    # inherit it without re-querying per file.
    project_classification_cache = {}

    for file_row in files:
        pid = file_row["project_id"]
        proj = conn.execute("SELECT * FROM PROJECTS WHERE id=?", (pid,)).fetchone()
        if proj is None:
            continue

        path = resolve_file_path(proj, file_row)
        text = extract_text(path, max_chars=FILE_SAMPLE_CHARS)

        if text:
            sec, div, sec_name, div_name, confidence, tags = classify_text(text)
            method = "RULE_BASED_KEYWORDS"
            with_content += 1
        else:
            if pid not in project_classification_cache:
                row = conn.execute(
                    "SELECT * FROM CLASSIFICATIONS WHERE project_id=? ORDER BY id DESC LIMIT 1",
                    (pid,),
                ).fetchone()
                project_classification_cache[pid] = row
            row = project_classification_cache[pid]
            if row:
                sec, div = row["isic_section"], row["isic_division"]
                sec_name, div_name, confidence = row["section_name"], row["division_name"], 0.0
            else:
                sec, div, sec_name, div_name, confidence = "UNCLASSIFIED", "00", "Unclassified", "Unclassified", 0.0
            method = "NO_TEXT_CONTENT"
            inherited += 1

        conn.execute(
            """
            INSERT INTO FILE_CLASSIFICATIONS (
                file_id, project_id, isic_section, isic_division,
                section_name, division_name, confidence, method, classified_date
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (file_row["id"], pid, sec, div, sec_name, div_name, confidence, method, now),
        )

        if (with_content + inherited) % 100 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f"[FILE CLASSIFIER] Done. Classified from content: {with_content}, inherited from project: {inherited}")
    return with_content, inherited


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to the (merged) database to classify")
    parser.add_argument("--files-only", action="store_true", help="Only run file-level classification")
    parser.add_argument("--projects-only", action="store_true", help="Only run project-level classification")
    args = parser.parse_args()

    if not args.files_only:
        run_classifier(args.db_path)
    if not args.projects_only:
        run_file_classifier(args.db_path)
