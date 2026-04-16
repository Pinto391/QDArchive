"""
scrapers/qdr_scraper.py
-----------------------
Scrapes QDR (Syracuse) using the public Dataverse JSON API.
download_method = API-CALL
"""

import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (
    insert_project, insert_file, insert_keyword,
    insert_person, insert_license, project_exists,
)
from pipeline.downloader import download_file, make_session

REPO_ID       = 1
REPO_NAME     = "qdr"
REPO_BASE_URL = "https://data.qdr.syr.edu"
API_SEARCH    = f"{REPO_BASE_URL}/api/search"
DOWNLOAD_BASE = f"{REPO_BASE_URL}/api/access/datafile"
DATA_ROOT     = Path(__file__).parent.parent / "data"
DELAY         = 1.5
PER_PAGE      = 25
MAX_PAGES     = 8

QUERIES = [
    "qdpx",
    "qualitative research interview",
    "interview transcripts qualitative",
    "nvivo qualitative data",
    "atlas.ti qualitative",
    "mx24 qualitative",
    "refi-qda",
    "qualitative data analysis",
]


def _api_get(session, url, params=None):
    time.sleep(DELAY)
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _parse_date(s):
    if not s:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(s))
    return m.group(1) if m else str(s)[:4]


def _parse_license(raw):
    if not raw:
        return "UNKNOWN"
    low = str(raw).lower()
    if "cc0" in low or "public domain" in low:
        return "CC0"
    if "by-nc-nd" in low: return "CC BY-NC-ND"
    if "by-nc-sa" in low: return "CC BY-NC-SA"
    if "by-nc"    in low: return "CC BY-NC"
    if "by-nd"    in low: return "CC BY-ND"
    if "by-sa"    in low: return "CC BY-SA"
    if "by"       in low: return "CC BY"
    return str(raw)


def _doi_slug(doi: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", doi)[:80]


def _process_dataset(session, item, doi, project_url, query):
    # Fetch full metadata
    citation = []
    try:
        full = _api_get(
            session,
            f"{REPO_BASE_URL}/api/datasets/:persistentId/versions/:latest",
            params={"persistentId": doi},
        )
        blocks = full.get("data", {}).get("metadataBlocks", {})
        citation = blocks.get("citation", {}).get("fields", [])
    except Exception as e:
        print(f"      [!] Metadata fetch failed: {e}")

    def field(name):
        for f in citation:
            if f.get("typeName") == name:
                v = f.get("value")
                if isinstance(v, str):
                    return v
                if isinstance(v, list) and v:
                    first = v[0]
                    if isinstance(first, str):
                        return first
                    if isinstance(first, dict):
                        return "; ".join(
                            sub.get("value", "")
                            for sub in first.values()
                            if isinstance(sub, dict)
                        )
        return None

    title       = item.get("name") or field("title") or doi
    description = item.get("description") or field("dsDescriptionValue") or "No description available."
    language    = field("language")
    upload_date = _parse_date(item.get("published_at") or item.get("updatedAt") or field("productionDate"))

    raw_lic = item.get("license", {})
    if isinstance(raw_lic, dict):
        raw_lic = raw_lic.get("name", "") or raw_lic.get("uri", "")
    license_str = _parse_license(raw_lic or "")

    doi_url        = f"https://doi.org/{doi.replace('doi:', '')}" if doi.startswith("doi:") else None
    project_folder = _doi_slug(doi)

    project_id = insert_project(
        query_string               = query,
        repository_id              = REPO_ID,
        repository_url             = REPO_BASE_URL,
        project_url                = project_url,
        title                      = title,
        description                = description,
        download_repository_folder = REPO_NAME,
        download_project_folder    = project_folder,
        download_method            = "API-CALL",
        language                   = language,
        doi                        = doi_url,
        upload_date                = upload_date,
    )
    print(f"    [+] Project #{project_id}: {title[:70]}")

    insert_license(project_id, license_str)

    # Keywords
    for f in citation:
        if f.get("typeName") == "keyword":
            for kw in (f.get("value") or []):
                if isinstance(kw, dict):
                    kv = kw.get("keywordValue", {})
                    insert_keyword(project_id, kv.get("value", "") if isinstance(kv, dict) else str(kv))
                elif isinstance(kw, str):
                    insert_keyword(project_id, kw)

    # Authors
    for f in citation:
        if f.get("typeName") == "author":
            for a in (f.get("value") or []):
                if isinstance(a, dict):
                    nf = a.get("authorName", {})
                    name = nf.get("value", "") if isinstance(nf, dict) else str(nf)
                    if name:
                        insert_person(project_id, name, "AUTHOR")

    for c in (item.get("contacts") or []):
        n = c.get("name", "")
        if n:
            insert_person(project_id, n, "UPLOADER")

    # Files
    dest_dir = DATA_ROOT / REPO_NAME / project_folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        fd = _api_get(
            session,
            f"{REPO_BASE_URL}/api/datasets/:persistentId/versions/:latest/files",
            params={"persistentId": doi},
        )
        file_list = fd.get("data", [])
    except Exception as e:
        print(f"      [!] File listing failed: {e}")
        file_list = []

    for fe in file_list:
        df        = fe.get("dataFile", {})
        file_id   = df.get("id")
        file_name = df.get("filename", f"file_{file_id}")
        ext       = Path(file_name).suffix.lstrip(".").lower() or "bin"
        dest_path = dest_dir / file_name

        if not file_id:
            insert_file(project_id, file_name, ext, "FAILED_SERVER_UNRESPONSIVE")
            continue

        if fe.get("restricted") or df.get("restricted"):
            insert_file(project_id, file_name, ext, "FAILED_LOGIN_REQUIRED")
            print(f"      [restricted] {file_name}")
            continue

        status = download_file(f"{DOWNLOAD_BASE}/{file_id}", dest_path, session)
        insert_file(project_id, file_name, ext, status)
        icon = "✓" if status == "SUCCEEDED" else "✗"
        print(f"      {icon} {file_name} [{status}]")


def scrape_qdr():
    session  = make_session()
    seen     = set()

    for query in QUERIES:
        print(f"\n[QDR] Query: '{query}'")
        for page in range(MAX_PAGES):
            start = page * PER_PAGE
            try:
                data  = _api_get(session, API_SEARCH, params={
                    "q": query, "type": "dataset",
                    "start": start, "per_page": PER_PAGE,
                })
            except Exception as e:
                print(f"  [!] Search error: {e}")
                break

            items = data.get("data", {}).get("items", [])
            total = data.get("data", {}).get("total_count", 0)
            print(f"  Page {page+1}: {len(items)} results (total={total})")

            if not items:
                break

            for item in items:
                doi = item.get("global_id") or item.get("identifier")
                if not doi or doi in seen:
                    continue
                seen.add(doi)
                project_url = item.get("url") or \
                    f"{REPO_BASE_URL}/dataset.xhtml?persistentId={doi}"
                if project_exists(project_url):
                    print(f"    [skip] {doi}")
                    continue
                _process_dataset(session, item, doi, project_url, query)

            if start + len(items) >= total:
                break

    print(f"\n[QDR] Done — {len(seen)} unique datasets.")


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    scrape_qdr()
