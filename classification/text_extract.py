"""
classification/text_extract.py
-------------------------------
Best-effort plain-text extraction from a downloaded primary/QDA data file,
used as classifier input alongside project metadata (Part 2 spec: "Uses
both the base data (the file) and the metadata").

extract_text() never raises — any failure to parse a given file just means
no text signal is available for it, which the classifier treats as a
metadata-only fallback for that file.
"""

import re
import zipfile
from pathlib import Path

TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".tsv", ".tab", ".nt", ".rmd"}
HTML_EXTENSIONS = {".htm", ".html"}
ARCHIVE_EXTENSIONS = {".zip", ".qdpx"}


def _read_plain_text(path: Path, max_chars: int) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def _read_pdf(path: Path, max_chars: int) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks = []
    total = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        chunks.append(text)
        total += len(text)
        if total >= max_chars:
            break
    return "".join(chunks)[:max_chars]


def _read_xml_zip_member(path: Path, member_name: str, max_chars: int) -> str:
    with zipfile.ZipFile(path) as zf:
        raw = zf.read(member_name).decode("utf-8", errors="ignore")
    # ODT (and some DOCX) files front-load huge <style:.../> / font declarations
    # before the actual document text; skip straight to the body if present so
    # max_chars isn't spent on style metadata.
    body_start = raw.find("<office:body>")
    if body_start == -1:
        body_start = raw.find("<w:body>")
    if body_start != -1:
        raw = raw[body_start:]
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _read_docx(path: Path, max_chars: int) -> str:
    return _read_xml_zip_member(path, "word/document.xml", max_chars)


def _read_odt(path: Path, max_chars: int) -> str:
    return _read_xml_zip_member(path, "content.xml", max_chars)


def _read_html(path: Path, max_chars: int) -> str:
    from bs4 import BeautifulSoup

    raw = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(raw, "html.parser").get_text(" ")[:max_chars]


def _read_rtf(path: Path, max_chars: int) -> str:
    from striprtf.striprtf import rtf_to_text

    raw = path.read_text(encoding="utf-8", errors="ignore")
    return rtf_to_text(raw)[:max_chars]


def _read_archive(path: Path, max_chars: int) -> str:
    """QDA container (.qdpx) or generic .zip: concatenate text from any
    supported inner member, best-effort."""
    chunks = []
    total = 0
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir() or total >= max_chars:
                continue
            inner_ext = Path(info.filename).suffix.lower()
            if inner_ext not in TEXT_EXTENSIONS and inner_ext not in HTML_EXTENSIONS:
                continue
            try:
                raw = zf.read(info.filename).decode("utf-8", errors="ignore")
                if inner_ext in HTML_EXTENSIONS:
                    from bs4 import BeautifulSoup
                    raw = BeautifulSoup(raw, "html.parser").get_text(" ")
                chunks.append(raw)
                total += len(raw)
            except Exception:
                continue
    return "".join(chunks)[:max_chars]


def extract_text(path: Path, max_chars: int = 20000) -> str | None:
    """Return up to max_chars of extracted text, or None if the file type
    isn't supported / extraction failed (e.g. media, corrupt file)."""
    path = Path(path)
    if not path.is_file():
        return None

    ext = path.suffix.lower()
    try:
        if ext in TEXT_EXTENSIONS:
            return _read_plain_text(path, max_chars)
        if ext == ".pdf":
            return _read_pdf(path, max_chars)
        if ext == ".docx":
            return _read_docx(path, max_chars)
        if ext == ".odt":
            return _read_odt(path, max_chars)
        if ext in HTML_EXTENSIONS:
            return _read_html(path, max_chars)
        if ext == ".rtf":
            return _read_rtf(path, max_chars)
        if ext in ARCHIVE_EXTENSIONS:
            return _read_archive(path, max_chars)
    except Exception:
        return None

    return None
