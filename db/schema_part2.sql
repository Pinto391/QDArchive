-- SQ26 Part 2 — Classification schema additions
-- Adds CLASSIFICATIONS, TAGS and FILE_CLASSIFICATIONS tables on top of the
-- Part 1 schema.

CREATE TABLE IF NOT EXISTS CLASSIFICATIONS (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id               INTEGER NOT NULL,
    isic_section             TEXT    NOT NULL,   -- e.g. 'Q'
    isic_division            TEXT    NOT NULL,   -- e.g. '85'
    section_name             TEXT    NOT NULL,
    division_name            TEXT    NOT NULL,
    confidence               REAL    NOT NULL,   -- 0.0 - 1.0, based on keyword match score
    secondary_isic_section   TEXT,               -- runner-up class, if any (e.g. cross-disciplinary projects)
    secondary_isic_division  TEXT,
    secondary_section_name   TEXT,
    secondary_division_name  TEXT,
    secondary_confidence     REAL,
    method                   TEXT    NOT NULL,   -- 'RULE_BASED_KEYWORDS'
    classified_date          TEXT    NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE IF NOT EXISTS TAGS (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    tag        TEXT    NOT NULL,       -- matched keyword / searchable tag
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE IF NOT EXISTS FILE_CLASSIFICATIONS (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER NOT NULL,
    project_id      INTEGER NOT NULL,
    isic_section    TEXT    NOT NULL,
    isic_division   TEXT    NOT NULL,
    section_name    TEXT    NOT NULL,
    division_name   TEXT    NOT NULL,
    confidence      REAL    NOT NULL,
    method          TEXT    NOT NULL,   -- 'RULE_BASED_KEYWORDS' | 'NO_TEXT_CONTENT'
    classified_date TEXT    NOT NULL,
    FOREIGN KEY (file_id)    REFERENCES FILES(id),
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE INDEX IF NOT EXISTS idx_classifications_project ON CLASSIFICATIONS(project_id);
CREATE INDEX IF NOT EXISTS idx_tags_project ON TAGS(project_id);
CREATE INDEX IF NOT EXISTS idx_file_classifications_file ON FILE_CLASSIFICATIONS(file_id);
