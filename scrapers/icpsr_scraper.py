"""
scrapers/icpsr_scraper.py
-------------------------
Scrapes ICPSR by parsing HTML search result pages.
download_method = SCRAPING

Most ICPSR file downloads require institutional login.
Files that cannot be downloaded are recorded as FAILED_LOGIN_REQUIRED.
Metadata is always captured regardless.
"""

import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (
    insert_project, insert_file, insert_keyword,
    insert_person, insert_license, project_exists,
)
from pipeline.downloader import download_file, make_session

REPO_ID       = 2
REPO_NAME     = "icpsr"
REPO_BASE_URL = "https://www.icpsr.umich.edu"
SEARCH_URL    = f"{REPO_BASE_URL}/web/ICPSR/search/studies"
DATA_ROOT     = Path(__file__).parent.parent / "data"
DELAY         = 2.0

QUERIES = [
    "interview qualitative",
    "qualitative research interview transcripts",
    "focus group qualitative",
    "ethnographic interview qualitative",
    "grounded theory qualitative",
    "thematic analysis interview",
    "qualitative longitudinal study",
    "qdpx qualitative data analysis",
]


def _get(session, url, params=None) -> BeautifulSoup:
    time.sleep(DELAY)
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _text(soup, selector):
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""


def _extract_study_ids(soup: BeautifulSoup) -> list:
    ids = []
    for a in soup.select("a[href*='/studies/']"):
        m = re.search(r"/studies/(\d+)", a.get("href", ""))
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def _parse_study_page(soup, study_id, url) -> dict:
    title = (
        _text(soup, "h1.study-title") or
        _text(soup, "h1") or
        f"ICPSR Study {study_id}"
    )
    description = (
        _text(soup, ".study-description") or
        _text(soup, ".abstract") or
        "No description available."
    )

    authors = []
    for el in soup.select(".pi-name, .principal-investigator"):
        n = el.get_text(strip=True)
        if n and len(n) < 100:
            authors.append(n)

    keywords = []
    for el in soup.select(".subject"):
        k = el.get_text(strip=True)
        if k and len(k) < 200:
            keywords.append(k)

    doi_url = None
    for a in soup.select("a[href*='doi.org']"):
        doi_url = a.get("href")
        break

    upload_date = None
    for el in soup.select("time, [class*='date']"):
        t = el.get_text(strip=True)
        m = re.search(r"(\d{4}-\d{2}-\d{2})", t)
        if m:
            upload_date = m.group(1)
            break
        m2 = re.search(r"(\d{4})", t)
        if m2:
            upload_date = m2.group(1)
            break

    file_links = []
    for a in soup.select("a[href*='download'], a[href*='/files/']"):
        href = a.get("href", "")
        if href:
            file_links.append(urljoin(url, href))

    return {
        "study_id":    study_id,
        "url":         url,
        "title":       title,
        "description": description,
        "authors":     list(dict.fromkeys(authors)),
        "keywords":    list(dict.fromkeys(keywords)),
        "doi":         doi_url,
        "upload_date": upload_date,
        "file_links":  file_links,
    }


def _process_study(session, meta, query):
    study_id    = meta["study_id"]
    project_url = meta["url"]

    if project_exists(project_url):
        print(f"    [skip] {study_id}")
        return

    project_folder = f"study_{study_id}"
    project_id = insert_project(
        query_string               = query,
        repository_id              = REPO_ID,
        repository_url             = REPO_BASE_URL,
        project_url                = project_url,
        title                      = meta["title"],
        description                = meta["description"],
        download_repository_folder = REPO_NAME,
        download_project_folder    = project_folder,
        download_method            = "SCRAPING",
        doi                        = meta.get("doi"),
        upload_date                = meta.get("upload_date"),
    )
    print(f"    [+] Study {study_id} → project_id={project_id}: {meta['title'][:60]}")

    insert_license(project_id, "UNKNOWN")

    for kw in meta.get("keywords", []):
        insert_keyword(project_id, kw)

    for name in meta.get("authors", []):
        insert_person(project_id, name, "AUTHOR")

    dest_dir = DATA_ROOT / REPO_NAME / project_folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_links = meta.get("file_links", [])
    if not file_links:
        # Most ICPSR studies require login — record honestly
        insert_file(
            project_id,
            f"study_{study_id}_files.zip",
            "zip",
            "FAILED_LOGIN_REQUIRED",
        )
        print(f"      [login-required] No public files for {study_id}")
        return

    for link in file_links[:20]:
        file_name = Path(link.split("?")[0]).name or f"study_{study_id}_file"
        ext       = Path(file_name).suffix.lstrip(".").lower() or "bin"
        dest_path = dest_dir / file_name
        status    = download_file(link, dest_path, session)
        insert_file(project_id, file_name, ext, status)
        icon = "✓" if status == "SUCCEEDED" else "✗"
        print(f"      {icon} {file_name} [{status}]")


def scrape_icpsr():
    session  = make_session()
    seen_ids = set()

    for query in QUERIES:
        print(f"\n[ICPSR] Query: '{query}'")
        for start in range(0, 200, 25):
            try:
                soup = _get(session, SEARCH_URL,
                            params={"q": query, "start": start})
            except Exception as e:
                print(f"  [!] Search error: {e}")
                break

            ids = _extract_study_ids(soup)
            print(f"  start={start}: {len(ids)} study IDs found")
            if not ids:
                break

            for sid in ids:
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                url = f"{REPO_BASE_URL}/web/ICPSR/studies/{sid}"
                try:
                    study_soup = _get(session, url)
                    meta = _parse_study_page(study_soup, sid, url)
                    _process_study(session, meta, query)
                except Exception as e:
                    print(f"      [!] Failed {sid}: {e}")

    print(f"\n[ICPSR] Done — {len(seen_ids)} unique studies.")


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    scrape_icpsr()
