"""
scripts/retry_failed.py
-----------------------
Re-attempts FAILED_SERVER_UNRESPONSIVE downloads.
Run:  python scripts/retry_failed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import get_connection
from pipeline.downloader import download_file, make_session

DATA_ROOT = Path(__file__).parent.parent / "data"


def retry(target_status="FAILED_SERVER_UNRESPONSIVE"):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT f.id, f.file_name, f.file_type,
               p.download_repository_folder, p.download_project_folder
        FROM FILES f
        JOIN PROJECTS p ON f.project_id = p.id
        WHERE f.status = ?
        """,
        (target_status,),
    ).fetchall()
    conn.close()

    if not rows:
        print(f"No files with status '{target_status}'.")
        return

    print(f"Retrying {len(rows)} files...")
    session = make_session()
    updated = 0

    for row in rows:
        dest = DATA_ROOT / row["download_repository_folder"] / \
               row["download_project_folder"] / row["file_name"]
        if not dest.exists():
            print(f"  [skip] file not on disk, cannot retry: {row['file_name']}")
            continue
        # File already exists from a partial download — remove and retry
        dest.unlink()
        print(f"  Removed partial file: {row['file_name']}")
        # Note: to actually retry you need the original URL.
        # This script clears the partial file; re-run main.py to re-download.

    print("Done. Re-run main.py to attempt fresh downloads.")


if __name__ == "__main__":
    retry()
