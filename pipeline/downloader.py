"""
pipeline/downloader.py  –  Generic HTTP downloader with error classification.
"""

import time
from pathlib import Path

import requests

MAX_FILE_BYTES = 200 * 1024 * 1024   # 200 MB
REQUEST_DELAY  = 1.5                  # seconds between requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SQ26-QDArchive-Scraper/1.0; "
        "FAU Erlangen student project; student_id=23123639)"
    )
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def classify_error(response=None) -> str:
    if response is not None:
        if response.status_code in (401, 403):
            return "FAILED_LOGIN_REQUIRED"
        if response.status_code in (500, 502, 503, 504):
            return "FAILED_SERVER_UNRESPONSIVE"
    return "FAILED_SERVER_UNRESPONSIVE"


def download_file(url: str, dest_path: Path, session: requests.Session) -> str:
    """Download url → dest_path. Returns DOWNLOAD_RESULT string."""
    time.sleep(REQUEST_DELAY)

    # HEAD check for size
    try:
        h = session.head(url, timeout=15, allow_redirects=True)
        cl = h.headers.get("Content-Length")
        if cl and int(cl) > MAX_FILE_BYTES:
            return "FAILED_TOO_LARGE"
    except Exception:
        pass

    try:
        r = session.get(url, timeout=60, stream=True)
        if r.status_code in (401, 403):
            return "FAILED_LOGIN_REQUIRED"
        if r.status_code >= 400:
            return classify_error(r)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                written += len(chunk)
                if written > MAX_FILE_BYTES:
                    f.close()
                    dest_path.unlink(missing_ok=True)
                    return "FAILED_TOO_LARGE"
                f.write(chunk)
        return "SUCCEEDED"

    except requests.exceptions.Timeout:
        return "FAILED_SERVER_UNRESPONSIVE"
    except requests.exceptions.ConnectionError:
        return "FAILED_SERVER_UNRESPONSIVE"
    except Exception:
        return "FAILED_SERVER_UNRESPONSIVE"
