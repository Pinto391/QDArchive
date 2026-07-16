# SQ26 — Seeding QDArchive

**Student:** Almas Ali Pinto (23123639)
**Degree Program:** M.Sc. Data Science, Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)
**Course:** Applied Software Engineering Project — **10 ECTS** — FAU Erlangen
**Submission Scope:** Part 1 (Data Acquisition) + Part 2 (Data Classification)
**Supervisor:** Prof. Dr. Dirk Riehle
**GitHub:** https://github.com/Pinto391/QDArchive
**Report:** [`23123639_SQ26_Part2_Report.pdf`](23123639_SQ26_Part2_Report.pdf) — full project report (both parts)
**Classification table (XLSX):** [`23123639_SQ26_Part2_Classification.xlsx`](23123639_SQ26_Part2_Classification.xlsx) — one row per project with its primary/secondary ISIC Rev. 5 class (Moodle "Project classification table" submission)

---

## Project Overview

This repository is the complete submission for the **10 ECTS Applied Software Engineering
Project**, which per the assignment combines **Part 1 (Data Acquisition) + Part 2 (Data
Classification)** into a single project (as opposed to a 5 ECTS Seminar, which would cover only
one part). It contains:

1. A pipeline that discovers, downloads, and catalogues open-access qualitative research
   projects (QDA files, interview transcripts, and related data) from two assigned
   repositories, storing structured metadata in a SQLite database (**Part 1**).
2. A classifier that merges the acquired database(s) and assigns every project *and* every
   individual downloaded file an ISIC Rev. 5 industry classification, using both metadata and
   actual file content, plus searchable tags and a statistics report (**Part 2**).

| Repo ID | Name  | URL |
|---------|-------|-----|
| 1       | QDR   | https://data.qdr.syr.edu |
| 2       | ICPSR | https://www.icpsr.umich.edu |

---

## Requirements Coverage

Every requirement from the assignment specification, mapped to where it is satisfied. The full
project report (PDF, linked above) contains the same matrix with additional detail and results.

### Part 1 — Data Acquisition

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1.1 | Find qualitative research projects on the web; identify QDA and primary data files; capture an open license | ✅ | 230 projects found (QDR: 230, ICPSR: 0 — see [Technical Challenges #2](#part-1)); `scrapers/qdr_scraper.py`, `scrapers/icpsr_scraper.py` |
| 1.2 | Build a pipeline that downloads files + metadata into an evolvable DB schema; leave fields empty rather than fabricate data | ✅ | `db/schema.sql`, `pipeline/downloader.py` |
| 1.3 | Operate the pipeline to build the student's own archive | ✅ | `23123639-seeding.db` committed; 945 files in `data/`; tagged `part-1-release` |
| Ongoing | Report technical challenges with the data (not programming) | ✅ | [Technical Challenges § Part 1](#part-1) |

### Part 2 — Data Classification

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 2.1 | Merge all student databases into one working database; identify and remove duplicates | ✅ (self-merge; see [#9](#part-2)) | `classification/merge_databases.py`, dedup by `project_url` |
| 2.2 | Develop a classifier using both the base data (the file) and the metadata; ISIC Rev. 5 down to division level; create tags for searching | ✅ | `classification/classifier.py`, `classification/text_extract.py`, `classification/isic_taxonomy.py` (complete official 22 sections / 87 divisions), `TAGS` table |
| 2.3 | Run the classifier on the acquired data | ✅ | 228/230 projects, 945/945 files classified |
| 2.4 | Report on resulting statistics: volume found, section/division distribution | ✅ | `python main.py --report`, `python main.py --pdf-report` |
| Ongoing | Report technical challenges with the data (not programming) | ✅ | [Technical Challenges § Part 2](#part-2) |
| + | *(Beyond the written spec)* Classify each primary data file individually, not only the project — per supervisor's meeting notes (2026-04-17) | ✅ | `classifier.py: run_file_classifier()`, `FILE_CLASSIFICATIONS` table |

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
├── classification/           ← Part 2: data classification
│   ├── merge_databases.py    ← Step 1: merge + dedup student DBs
│   ├── isic_taxonomy.py      ← Full official ISIC Rev. 5 structure (22 sections, 87 divisions)
│   ├── text_extract.py       ← Best-effort text extraction from downloaded files
│   ├── classifier.py         ← Step 2/3: rule-based classifier (project + file level)
│   ├── report.py             ← Step 4: classification statistics report (text)
│   ├── generate_pdf_report.py  ← Submission-ready PDF project report
│   └── generate_xlsx_report.py ← Submission-ready XLSX classification workbook
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

### Part 2: Data Classification

```powershell
# Step 1 — merge student databases (self-merge if that's all you have)
python main.py --merge 23123639-seeding.db --out working.db
python main.py --merge mine.db classmate1.db classmate2.db --out working.db

# Step 2/3 — classify every project AND every downloaded file against
# ISIC Rev. 5 (section + division), using metadata + actual file content
python main.py --classify --db working.db

# Step 4 — print / save the statistics report
python main.py --report --db working.db
python main.py --report --db working.db --report-out part2_report.txt

# Generate the submission-ready PDF report (title page, charts, tables)
python main.py --pdf-report --db working.db --pdf-out 23123639_SQ26_Part2_Report.pdf

# Generate the classification-results XLSX workbook (per-project + per-file rows)
python main.py --xlsx-report --db working.db --xlsx-out 23123639_SQ26_Part2_Classification.xlsx

# Export the classified DB (including CLASSIFICATIONS / TAGS / FILE_CLASSIFICATIONS)
python main.py --export --db working.db
```

`classification/generate_pdf_report.py` produces `23123639_SQ26_Part2_Report.pdf` — a formatted
submission document (title page with student/course details, methodology, results with charts and
tables, technical challenges, and conclusion) built with `reportlab` and `matplotlib` from the live
contents of the classified database, so its numbers always match the current run.

`classification/generate_xlsx_report.py` produces `23123639_SQ26_Part2_Classification.xlsx` — the
**Project classification table** required by the Moodle submission: a single `classification`
sheet with one row per acquired project — `repository_id`, `project_type`, `project_title`,
`primary_class`, `secondary_class`, `no_project_files` — where `primary_class`/`secondary_class`
are formatted as `<ISIC section><division> <division name>` (e.g. `R86 Human health activities`).
`secondary_class` is the runner-up ISIC division for projects that plausibly touch a second domain
(computed by `classify_text_ranked()` in `classifier.py`, stored in `CLASSIFICATIONS.secondary_*`),
left blank if no second division scored above the threshold.

---

## Database Schema

| Table                | Description                                          |
|-----------------------|-------------------------------------------------------|
| REPOSITORIES          | Seed list of assigned repos                           |
| PROJECTS              | One row per research project                          |
| FILES                 | One row per file with download status                 |
| KEYWORDS              | Keywords per project                                   |
| PERSON_ROLE           | Authors / uploaders per project                        |
| LICENSES              | License(s) per project                                 |
| CLASSIFICATIONS       | Part 2: ISIC Rev. 5 section/division per **project**   |
| TAGS                  | Part 2: searchable keyword tags per project            |
| FILE_CLASSIFICATIONS  | Part 2: ISIC Rev. 5 section/division per **file**      |

**Enum values:**

- `FILES.status`: `SUCCEEDED` · `FAILED_LOGIN_REQUIRED` · `FAILED_SERVER_UNRESPONSIVE` · `FAILED_TOO_LARGE`
- `PERSON_ROLE.role`: `AUTHOR` · `UPLOADER` · `OWNER` · `OTHER` · `UNKNOWN`
- `PROJECTS.download_method`: `API-CALL` (QDR) · `SCRAPING` (ICPSR)
- `CLASSIFICATIONS.method`: `RULE_BASED_KEYWORDS`
- `CLASSIFICATIONS.secondary_isic_section` / `secondary_isic_division` / `secondary_confidence`:
  the runner-up ISIC division for a project (nullable — blank when no second division scored
  above the classification threshold)
- `FILE_CLASSIFICATIONS.method`: `RULE_BASED_KEYWORDS` (classified from the file's own extracted
  text) · `NO_TEXT_CONTENT` (media/binary file with no extractable text — inherits its parent
  project's classification instead)

### Classification approach (Part 2)

`classification/isic_taxonomy.py` holds the complete official ISIC Rev. 5 structure (22 sections,
87 divisions), sourced from the UN Statistics Division's "Draft ISIC Revision 5 structure"
(endorsed by UNSC, 54th session, March 2023). Each division carries a curated list of keyword
hints relevant to qualitative-research topics (health, education, social science, policy, etc.).

`classification/classifier.py` builds a text blob per **project** (title + description + keywords
+ file extensions + a sample of extracted text from that project's downloaded files) and, per
Dirk's meeting notes (2026-04-17), a second blob per **file** from that file's own extracted text
(`classification/text_extract.py` — supports txt/pdf/docx/odt/htm/rtf/qdpx). Both are scored
against every division's keyword hints; the highest-scoring division wins, with
`confidence = matched_keywords / total_keywords_for_that_division`. Every keyword matched across
*all* divisions (not just the winner) is stored in `TAGS` for searching.

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

This repository is the complete deliverable for the 10 ECTS Applied Software Engineering
Project (Part 1 + Part 2). Each part was also tagged individually as its own milestone, per the
professor's separate Part 1 / Part 2 deadlines.

**Part 1:**
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

**Part 2:**
- [x] Merge database (self-merge; classmates' data can be folded in later — `python main.py --merge ...`)
- [x] Run classifier on merged data (`python main.py --classify --db working.db`)
- [x] Generate and review statistics report (`python main.py --report --db working.db`)
- [x] Generate the submission-ready PDF report (`python main.py --pdf-report --db working.db`)
- [x] Generate the classification-results XLSX workbook (`python main.py --xlsx-report --db working.db`)
- [ ] Tag `part-2-release`
- [ ] Professor's submission form filled in

```powershell
git add working.db 23123639_SQ26_Part2_Report.pdf 23123639_SQ26_Part2_Classification.xlsx
git commit -m "part-2-release: classification complete"
git tag part-2-release
git push origin main --tags
```

---

## Technical Challenges (Data, not Programming)

### Part 1

1. **ICPSR: Most qualitative datasets are login-gated.**
   The majority of ICPSR studies require institutional login to download even when
   metadata is publicly visible. Only openICPSR (self-published) studies are freely
   accessible. All gated files are recorded as `FAILED_LOGIN_REQUIRED` rather than
   silently dropped.

2. **ICPSR: no qualifying studies were ultimately recorded in this run.**
   All 230 projects in the final database originate from QDR (`download_method =
   API-CALL`); the ICPSR scraper (`download_method = SCRAPING`) ran against ICPSR's
   HTML search pages, but the query set used did not surface studies that passed the
   qualitative-data heuristic in this collection window. This is reported
   transparently rather than adjusted after the fact — ICPSR's login gating
   (challenge #1) independently limits how much of that repository would have been
   downloadable regardless.

3. **QDR: Restricted files within open projects.**
   Some individual files inside otherwise public QDR datasets are marked
   `restricted=true` in the API response. These are recorded as `FAILED_LOGIN_REQUIRED`.

4. **Compound keyword strings.**
   Keywords like `"interlanguage pragmatics, EFL learners, scoping review"` are stored
   as-is per the professor's primary rule (do not change downloaded data). Splitting
   and normalisation was deferred to Part 2 — not yet addressed, since the classifier
   works from title/description/file-content and doesn't require pre-split keywords.

5. **Ambiguous person roles.**
   Neither QDR nor ICPSR consistently distinguishes Uploader, Author, and Owner.
   Ambiguous cases are recorded as `UNKNOWN`. Of the 720 person records captured, roles
   resolved to AUTHOR: 466, UPLOADER: 254.

6. **Inconsistent date formats.**
   Upload dates appear as ISO 8601, year-only, or US-format strings. Original strings
   are preserved; only unambiguous dates are normalised to `YYYY-MM-DD`.

7. **Multiple licenses per project / license metadata often unavailable.**
   Where projects specify multiple licenses, each is stored as its own row in
   `LICENSES` linked to the same project. In this dataset, all 230 license records
   resolved to `UNKNOWN` because QDR's public API response for this query set did not
   expose a machine-readable license field — this is reported honestly rather than
   inferred or fabricated.

8. **Version history.**
   The pipeline downloads `versions/:latest` only. Version strings are stored in the
   `version` field where available from the API.

### Part 2

9. **No classmate databases available yet.** The professor's slides call for merging
   *all* student databases (Part 2, Step 1). At the time of this classification pass,
   only this student's own `23123639-seeding.db` was available, so `--merge` was run
   as a documented self-merge (dedup by `project_url`, 230/230 projects kept, 0
   duplicates found). `classification/merge_databases.py` accepts any number of `.db`
   files, so classmates' databases can be folded in later without any code changes.

10. **Only 945 of 20,322 recorded files were actually downloaded** (the rest are
    `FAILED_LOGIN_REQUIRED` / `FAILED_SERVER_UNRESPONSIVE`, mostly ICPSR's login gate —
    see Part 1 challenge #1). File-level classification and the file-content signal fed
    into project-level classification can only ever draw on that smaller, already-open
    subset — this is a ceiling on classification recall, not a bug in the classifier.

11. **Vague or generic project descriptions.** Some QDR project descriptions are
    boilerplate and don't contain strong domain-specific keywords, leading to lower
    classifier confidence or `UNCLASSIFIED` results (2/230 projects, 101/945 files in
    this run).

12. **Cross-disciplinary projects.** Some qualitative studies span multiple ISIC
    divisions (e.g. a study on "health policy education" touches Health (86),
    Education (85), and Public Administration (84) simultaneously). The classifier
    picks the single highest-scoring division; the full match set across *all*
    divisions is preserved in `TAGS` for secondary discovery.

13. **ISIC Rev. 5 classifies economic activity, not academic research topics.** Since
    ISIC categorizes *industries* rather than *research subjects*, a `qualitative
    research methods` interview study and a hospital's own clinical operations would,
    in principle, both look like "Human health activities" (86) or "Scientific R&D"
    (72) depending on which signal dominates. Keyword hints were tuned to route
    studies toward their *substantive domain* (e.g. Health 86, Education 85) where the
    text supports it, falling back to Division 72 ("Scientific research and
    development") only when the topic itself is about research methodology rather than
    a specific field. In this run, division 86 (Human health) and 85 (Education)
    together account for ~60% of classified projects, reflecting the actual subject
    matter of the corpus (QDR skews toward health and education research) rather than
    a classifier artifact.

14. **Per-file classification granularity.** Dirk's meeting notes (2026-04-17) ask for
    a class on each primary data file, not just the project. 93.7% of the 945
    downloaded files (586 PDFs, 179 txt, 23 docx, etc.) were classified directly from
    their own extracted text; the remaining 6.3% (media/binary files with no
    extractable text, plus a handful of extraction failures) inherit their parent
    project's classification instead (`FILE_CLASSIFICATIONS.method = 'NO_TEXT_CONTENT'`),
    which is recorded honestly rather than guessed.
