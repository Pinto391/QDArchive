"""
classification/merge_databases.py
----------------------------------
Part 2, Step 1: Merge all student databases into one working database,
identifying and removing duplicate projects.

Usage:
    python classification/merge_databases.py db1.db db2.db db3.db --out working.db

A project is considered a duplicate if it has the same project_url as
one already merged in (URLs are the natural unique key across student
databases, since everyone scraped independently from the same public
repositories).

If you only have your own database (23123639-seeding.db), you can still
run this to "self-merge" into working.db — it copies your data across
cleanly and de-duplicates anything you may have double-scraped. The
professor's slides explicitly allow this: "if you can't fill a particular
field, leave it empty" / classmates' databases can be merged in later once
shared.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _init_output_db(out_path: Path, schema_path: Path):
    conn = sqlite3.connect(out_path)
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def merge_databases(input_dbs: list, out_path: str):
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    out = Path(out_path)

    if out.exists():
        out.unlink()

    out_conn = _init_output_db(out, schema_path)
    out_conn.row_factory = sqlite3.Row

    seen_project_urls = set()
    # schema.sql seeds REPOSITORIES with the two assigned repos (qdr, icpsr) —
    # start from those instead of re-inserting duplicates for the same urls.
    repo_url_to_new_id = {
        row["url"]: row["id"]
        for row in out_conn.execute("SELECT id, url FROM REPOSITORIES").fetchall()
    }
    stats = {"projects_seen": 0, "projects_merged": 0, "duplicates_skipped": 0}

    for db_path in input_dbs:
        print(f"\n[MERGE] Reading {db_path} ...")
        src = sqlite3.connect(db_path)
        src.row_factory = sqlite3.Row

        # ── Repositories: merge by url, mapping old id -> new id ──────────
        old_repo_id_to_new = {}
        for repo in src.execute("SELECT * FROM REPOSITORIES").fetchall():
            if repo["url"] not in repo_url_to_new_id:
                cur = out_conn.execute(
                    "INSERT INTO REPOSITORIES (name, url) VALUES (?,?)",
                    (repo["name"], repo["url"]),
                )
                repo_url_to_new_id[repo["url"]] = cur.lastrowid
            old_repo_id_to_new[repo["id"]] = repo_url_to_new_id[repo["url"]]

        # ── Projects: merge by project_url, skip duplicates ───────────────
        old_project_id_to_new = {}
        for proj in src.execute("SELECT * FROM PROJECTS").fetchall():
            stats["projects_seen"] += 1
            if proj["project_url"] in seen_project_urls:
                stats["duplicates_skipped"] += 1
                continue
            seen_project_urls.add(proj["project_url"])

            new_repo_id = old_repo_id_to_new.get(proj["repository_id"])
            if new_repo_id is None:
                cur = out_conn.execute(
                    "INSERT INTO REPOSITORIES (name, url) VALUES (?,?)",
                    (proj["repository_url"], proj["repository_url"]),
                )
                new_repo_id = cur.lastrowid

            cur = out_conn.execute(
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
                    proj["query_string"], new_repo_id, proj["repository_url"], proj["project_url"],
                    proj["version"], proj["title"], proj["description"], proj["language"], proj["doi"],
                    proj["upload_date"], proj["download_date"],
                    proj["download_repository_folder"], proj["download_project_folder"],
                    proj["download_version_folder"], proj["download_method"],
                ),
            )
            new_project_id = cur.lastrowid
            old_project_id_to_new[proj["id"]] = new_project_id
            stats["projects_merged"] += 1

        # ── Child tables: FILES, KEYWORDS, PERSON_ROLE, LICENSES ──────────
        for table, cols in [
            ("FILES",       ["file_name", "file_type", "status"]),
            ("KEYWORDS",    ["keyword"]),
            ("PERSON_ROLE", ["name", "role"]),
            ("LICENSES",    ["license"]),
        ]:
            col_list = ", ".join(cols)
            placeholders = ", ".join(["?"] * (len(cols) + 1))
            for row in src.execute(f"SELECT * FROM {table}").fetchall():
                new_pid = old_project_id_to_new.get(row["project_id"])
                if new_pid is None:
                    continue  # belongs to a skipped duplicate project
                values = [new_pid] + [row[c] for c in cols]
                out_conn.execute(
                    f"INSERT INTO {table} (project_id, {col_list}) VALUES ({placeholders})",
                    values,
                )

        src.close()
        out_conn.commit()
        print(f"  {db_path}: merged (running total {stats['projects_merged']} unique projects)")

    out_conn.commit()
    out_conn.close()

    print("\n-- Merge Summary --")
    print(f"  Source databases:     {len(input_dbs)}")
    print(f"  Projects seen total:  {stats['projects_seen']}")
    print(f"  Duplicates skipped:   {stats['duplicates_skipped']}")
    print(f"  Unique projects kept: {stats['projects_merged']}")
    print(f"  Output database:      {out}")


def main():
    parser = argparse.ArgumentParser(description="Merge multiple student SQ26 databases")
    parser.add_argument("databases", nargs="+", help="Paths to .db files to merge")
    parser.add_argument("--out", default="working.db", help="Output merged database path")
    args = parser.parse_args()
    merge_databases(args.databases, args.out)


if __name__ == "__main__":
    main()
