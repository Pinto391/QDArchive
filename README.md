# SQ26 — Seeding QDArchive: Part 1 Data Acquisition

**Student ID:** 23123639  
**GitHub:** https://github.com/Pinto391/QDArchive  
**Course:** Applied Software Engineering Seminar / Project — FAU Erlangen  
**Supervisor:** Prof. Dirk Riehle

---

## Project Overview

This pipeline discovers, downloads, and catalogues open-access qualitative research
projects (QDA files, interview transcripts, and related data) from two assigned
repositories, storing structured metadata in a SQLite database.

| Repo ID | Name  | URL |
|---------|-------|-----|
| 1       | QDR   | https://data.qdr.syr.edu |
| 2       | ICPSR | https://www.icpsr.umich.edu |

---

## Folder Structure

```
QDArchive/
├── 23123639-seeding.db       ← SQLite database (submission artefact)
├── main.py                   ← Pipeline entry point
├── requirements.txt
├── .gitignore
├── README.md
│
├── db/
│   ├── schema.sql            ← Table definitions
│   └── database.py           ← DB helpers
│
├── pipeline/
│   └── downloader.py         ← HTTP downloader + error classifier
│
├── scrapers/
│   ├── qdr_scraper.py        ← QDR via Dataverse API  (API-CALL)
│   └── icpsr_scraper.py      ← ICPSR via HTML scraping (SCRAPING)
│
├── export/
│   └── export_csv.py         ← Export all tables to CSV
│
├── scripts/
│   └── retry_failed.py       ← Helper for failed downloads
│
└── data/                     ← Downloaded files (NOT in git, upload separately)
    ├── qdr/
    └── icpsr/
```

---

## Setup

```powershell
# 1. Clone
git clone https://github.com/Pinto391/QDArchive.git
cd QDArchive

# 2. Virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

```powershell
# Run everything (QDR + ICPSR) then export CSV
python main.py

# Run one repo at a time
python main.py --qdr
python main.py --icpsr

# Check what was collected
python main.py --stats

# Export tables to CSV
python main.py --export
```

---

## Database Schema

| Table         | Description                              |
|---------------|------------------------------------------|
| REPOSITORIES  | Seed list of assigned repos              |
| PROJECTS      | One row per research project             |
| FILES         | One row per file with download status    |
| KEYWORDS      | Keywords per project                     |
| PERSON_ROLE   | Authors / uploaders per project          |
| LICENSES      | License(s) per project                   |

**Enum values:**

- `FILES.status`: `SUCCEEDED` · `FAILED_LOGIN_REQUIRED` · `FAILED_SERVER_UNRESPONSIVE` · `FAILED_TOO_LARGE`
- `PERSON_ROLE.role`: `AUTHOR` · `UPLOADER` · `OWNER` · `OTHER` · `UNKNOWN`
- `PROJECTS.download_method`: `API-CALL` (QDR) · `SCRAPING` (ICPSR)

---

## Download Methods

**QDR → `API-CALL`**  
QDR runs on Dataverse. We use the public JSON Search API (no auth required for open datasets):
```
GET https://data.qdr.syr.edu/api/search?q=<query>&type=dataset
GET https://data.qdr.syr.edu/api/datasets/:persistentId/versions/:latest/files
GET https://data.qdr.syr.edu/api/access/datafile/<file_id>
```

**ICPSR → `SCRAPING`**  
ICPSR has no public REST API. We parse HTML search result pages and study pages.
Most file downloads require institutional login and are recorded as `FAILED_LOGIN_REQUIRED`.

---

## File Storage

The `data/` folder is excluded from git (too large). Upload it separately to FAUbox/Google Drive.

```
data/
  qdr/
    doi_10_xxxxx/
      main.qdpx
      interview1.pdf
  icpsr/
    study_12345/
      transcript_01.docx
```

---

## Submission Checklist

- [x] `23123639-seeding.db` in repo root
- [x] Git tag `part-1-release`
- [ ] `data/` folder uploaded to FAUbox / Google Drive
- [ ] Professor's submission form filled in

```powershell
git add 23123639-seeding.db
git commit -m "part-1-release: data acquisition complete"
git tag part-1-release
git push origin main --tags
```

---

## Technical Challenges (Data, not Programming)

### 1. ICPSR: Most qualitative datasets are login-gated
The majority of ICPSR studies require institutional login to download even when
metadata is publicly visible. Only openICPSR (self-published) studies are freely
accessible. All gated files are recorded as `FAILED_LOGIN_REQUIRED`.

### 2. QDR: Restricted files within open projects
Some individual files inside otherwise public QDR datasets are marked
`restricted=true` in the API response. These are recorded as `FAILED_LOGIN_REQUIRED`.

### 3. Compound keyword strings
Keywords like `"interlanguage pragmatics, EFL learners, scoping review"` are stored
as-is per the professor's primary rule (do not change downloaded data). Splitting
and normalisation is deferred to Part 2.

### 4. Ambiguous person roles
Neither QDR nor ICPSR consistently distinguishes Uploader, Author, and Owner.
Ambiguous cases are recorded as `UNKNOWN`.

### 5. Inconsistent date formats
Upload dates appear as ISO 8601, year-only, or US-format strings. Original strings
are preserved; only unambiguous dates are normalised to `YYYY-MM-DD`.

### 6. Multiple licenses per project
Some projects specify multiple licenses. Each is stored as a separate row in
`LICENSES` linked to the same `project_id`.

### 7. Version history
The pipeline downloads `versions/:latest` only. Version strings are stored in the
`version` field where available from the API.
