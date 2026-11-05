from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def create_project(
    upload_id: str,
    original_filename: str,
    upload_type: str,
    db_path: Path = DATABASE_PATH,
) -> dict[str, Any]:
    """
    Save uploaded project metadata in SQLite.
    """

    connection = get_connection(db_path)

    try:
        connection.execute(
            """
            INSERT INTO projects (
                upload_id,
                original_filename,
                upload_type
            )
            VALUES (?, ?, ?)
            """,
            (
                upload_id,
                original_filename,
                upload_type,
            ),
        )

        connection.commit()

        return get_project(upload_id, db_path)

    finally:
        connection.close()


def get_project(
    upload_id: str,
    db_path: Path = DATABASE_PATH,
) -> dict[str, Any] | None:
    """
    Retrieve a project using its upload ID.
    """

    connection = get_connection(db_path)

    try:
        row = connection.execute(
            """
            SELECT
                upload_id,
                original_filename,
                upload_type,
                created_at
            FROM projects
            WHERE upload_id = ?
            """,
            (upload_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def list_projects(
    db_path: Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """
    Retrieve all uploaded projects, newest first.
    """

    connection = get_connection(db_path)

    try:
        rows = connection.execute(
            """
            SELECT
                upload_id,
                original_filename,
                upload_type,
                created_at
            FROM projects
            ORDER BY created_at DESC, rowid DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()