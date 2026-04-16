-- SQ26 Seeding QDArchive - Metadata Schema
-- Student: 23123639
-- Matches professor's schema document exactly

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS REPOSITORIES (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL,
    url  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS PROJECTS (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    query_string                TEXT,
    repository_id               INTEGER NOT NULL,
    repository_url              TEXT    NOT NULL,
    project_url                 TEXT    NOT NULL,
    version                     TEXT,
    title                       TEXT    NOT NULL,
    description                 TEXT    NOT NULL,
    language                    TEXT,
    doi                         TEXT,
    upload_date                 TEXT,
    download_date               TEXT    NOT NULL,
    download_repository_folder  TEXT    NOT NULL,
    download_project_folder     TEXT    NOT NULL,
    download_version_folder     TEXT,
    download_method             TEXT    NOT NULL
        CHECK(download_method IN ('SCRAPING', 'API-CALL')),
    FOREIGN KEY (repository_id) REFERENCES REPOSITORIES(id)
);

CREATE TABLE IF NOT EXISTS FILES (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_name  TEXT    NOT NULL,
    file_type  TEXT    NOT NULL,
    status     TEXT    NOT NULL
        CHECK(status IN (
            'SUCCEEDED',
            'FAILED_SERVER_UNRESPONSIVE',
            'FAILED_LOGIN_REQUIRED',
            'FAILED_TOO_LARGE'
        )),
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE IF NOT EXISTS KEYWORDS (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    keyword    TEXT    NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE IF NOT EXISTS PERSON_ROLE (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    role       TEXT    NOT NULL
        CHECK(role IN ('AUTHOR', 'UPLOADER', 'OWNER', 'OTHER', 'UNKNOWN')),
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE IF NOT EXISTS LICENSES (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    license    TEXT    NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

-- Seed repositories
INSERT OR IGNORE INTO REPOSITORIES (id, name, url) VALUES
    (1, 'qdr',   'https://data.qdr.syr.edu'),
    (2, 'icpsr', 'https://www.icpsr.umich.edu');
