"""
db/database.py  –  All database operations for SQ26 pipeline.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_NAME     = "23123639-seeding.db"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def get_db_path() -> Path:
    return Path(__file__).parent.parent / DB_NAME


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"[DB] Initialised: {get_db_path()}")


# ── INSERT helpers ────────────────────────────────────────────────────────────

def insert_project(
    query_string,
    repository_id,
    repository_url,
    project_url,
    title,
    description,
    download_repository_folder,
    download_project_folder,
    download_method,
    version=None,
    language=None,
    doi=None,
    upload_date=None,
    download_version_folder=None,
) -> int:
    download_date = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO PROJECTS (
            query_string, repository_id, repository_url, project_url,
            version, title, description, language, doi,
            upload_date, download_date,
            download_repository_folder, download_project_folder,
            download_version_folder, download_method
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            query_string, repository_id, repository_url, project_url,
            version, title, description, language, doi,
            upload_date, download_date,
            download_repository_folder, download_project_folder,
            download_version_folder, download_method,
        ),
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def insert_file(project_id: int, file_name: str, file_type: str, status: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO FILES (project_id, file_name, file_type, status) VALUES (?,?,?,?)",
        (project_id, file_name, file_type, status),
    )
    conn.commit()
    conn.close()


def insert_keyword(project_id: int, keyword: str):
    kw = keyword.strip()
    if not kw:
        return
    conn = get_connection()
    conn.execute(
        "INSERT INTO KEYWORDS (project_id, keyword) VALUES (?,?)",
        (project_id, kw),
    )
    conn.commit()
    conn.close()


def insert_person(project_id: int, name: str, role: str):
    valid = {"AUTHOR", "UPLOADER", "OWNER", "OTHER", "UNKNOWN"}
    if role not in valid:
        role = "UNKNOWN"
    conn = get_connection()
    conn.execute(
        "INSERT INTO PERSON_ROLE (project_id, name, role) VALUES (?,?,?)",
        (project_id, name.strip(), role),
    )
    conn.commit()
    conn.close()


def insert_license(project_id: int, license_str: str):
    _MAP = {
        "cc0":           "CC0",
        "cc by":         "CC BY",
        "cc-by":         "CC BY",
        "cc by 4.0":     "CC BY 4.0",
        "cc by-sa":      "CC BY-SA",
        "cc by-nc":      "CC BY-NC",
        "cc by-nd":      "CC BY-ND",
        "cc by-nc-nd":   "CC BY-NC-ND",
        "cc by-nc-sa":   "CC BY-NC-SA",
        "odbl":          "ODbL",
        "odbl-1.0":      "ODbL-1.0",
        "odc-by":        "ODC-By",
        "odc-by-1.0":    "ODC-By-1.0",
        "pddl":          "PDDL",
    }
    normalised = _MAP.get(license_str.strip().lower(), license_str.strip())
    if not normalised:
        normalised = "UNKNOWN"
    conn = get_connection()
    conn.execute(
        "INSERT INTO LICENSES (project_id, license) VALUES (?,?)",
        (project_id, normalised),
    )
    conn.commit()
    conn.close()


# ── QUERY helpers ─────────────────────────────────────────────────────────────

def project_exists(project_url: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM PROJECTS WHERE project_url=?", (project_url,)
    ).fetchone()
    conn.close()
    return row is not None


def get_stats() -> dict:
    conn = get_connection()
    stats = {
        "projects":  conn.execute("SELECT COUNT(*) FROM PROJECTS").fetchone()[0],
        "files":     conn.execute("SELECT COUNT(*) FROM FILES").fetchone()[0],
        "keywords":  conn.execute("SELECT COUNT(*) FROM KEYWORDS").fetchone()[0],
        "persons":   conn.execute("SELECT COUNT(*) FROM PERSON_ROLE").fetchone()[0],
        "licenses":  conn.execute("SELECT COUNT(*) FROM LICENSES").fetchone()[0],
        "succeeded": conn.execute("SELECT COUNT(*) FROM FILES WHERE status='SUCCEEDED'").fetchone()[0],
        "failed":    conn.execute("SELECT COUNT(*) FROM FILES WHERE status!='SUCCEEDED'").fetchone()[0],
    }
    conn.close()
    return stats
