import sqlite3
import os
from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_task (
    id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL,
    app_name TEXT,
    user_goal TEXT,
    rating_filter TEXT,
    time_range TEXT,
    version_filter TEXT,
    status TEXT DEFAULT 'pending',
    is_using_cache INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS review (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    author TEXT,
    rating INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    review_date TEXT NOT NULL,
    version TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS category (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    review_count INTEGER,
    sentiment TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS finding (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    category_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    evidence_strength TEXT,
    supporting_review_ids TEXT,
    is_hypothesis INTEGER DEFAULT 0,
    is_contradictory INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS requirement (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    finding_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT,
    version_suggestion TEXT,
    FOREIGN KEY (task_id) REFERENCES analysis_task(id)
);

CREATE TABLE IF NOT EXISTS test_case (
    id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    title TEXT NOT NULL,
    preconditions TEXT,
    steps TEXT,
    expected_result TEXT,
    case_type TEXT,
    FOREIGN KEY (requirement_id) REFERENCES requirement(id)
);
"""


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.close()


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
