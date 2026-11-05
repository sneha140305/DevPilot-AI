import sqlite3
from pathlib import Path

from app.core.config import PROJECT_ROOT

# Database location
DATABASE_PATH = PROJECT_ROOT / "data" / "devpilot.db"


def get_connection(
    db_path: Path = DATABASE_PATH,
) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)

    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    # Wait if the database is temporarily locked
    connection.execute("PRAGMA busy_timeout = 5000")

    return connection


def initialize_database(
    db_path: Path = DATABASE_PATH,
) -> None:
    """
    Initialize the DevPilot AI database and create tables.
    """

    connection = get_connection(db_path)

    try:

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                upload_id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                upload_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (upload_id)
                    REFERENCES projects(upload_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS review_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (upload_id)
                    REFERENCES projects(upload_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS test_generation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (upload_id)
                    REFERENCES projects(upload_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_upload_id
                ON analysis_results(upload_id);

            CREATE INDEX IF NOT EXISTS idx_review_upload_id
                ON review_results(upload_id);

            CREATE INDEX IF NOT EXISTS idx_test_generation_upload_id
                ON test_generation_results(upload_id);
            """
        )

        connection.commit()

    finally:

        connection.close()