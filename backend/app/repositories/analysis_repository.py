import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def save_analysis(
    upload_id: str,
    result: dict[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    """
    Save an analysis result in SQLite.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO analysis_results (
                upload_id,
                result_json
            )
            VALUES (?, ?)
            """,
            (
                upload_id,
                json.dumps(result),
            ),
        )

        connection.commit()

        analysis_id = cursor.lastrowid

        return get_analysis_by_id(
            analysis_id,
            db_path,
        )

    finally:
        connection.close()


def get_analysis_by_id(
    analysis_id: int,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve one analysis using its database ID.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        row = connection.execute(
            """
            SELECT
                id,
                upload_id,
                result_json,
                created_at
            FROM analysis_results
            WHERE id = ?
            """,
            (analysis_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)

        result["result"] = json.loads(
            result.pop("result_json")
        )

        return result

    finally:
        connection.close()


def get_latest_analysis(
    upload_id: str,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve the latest analysis for an uploaded project.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        row = connection.execute(
            """
            SELECT
                id,
                upload_id,
                result_json,
                created_at
            FROM analysis_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (upload_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)

        result["result"] = json.loads(
            result.pop("result_json")
        )

        return result

    finally:
        connection.close()


def list_analyses(
    upload_id: str,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve all analysis history for a project.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                upload_id,
                result_json,
                created_at
            FROM analysis_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (upload_id,),
        ).fetchall()

        analyses = []

        for row in rows:
            analysis = dict(row)

            analysis["result"] = json.loads(
                analysis.pop("result_json")
            )

            analyses.append(analysis)

        return analyses

    finally:
        connection.close()