import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def save_test_generation(
    upload_id: str,
    result: dict[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Save generated test results in SQLite."""

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO test_generation_results (
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

        generation_id = cursor.lastrowid

        return get_test_generation_by_id(
            generation_id,
            db_path,
        )

    finally:
        connection.close()


def get_test_generation_by_id(
    generation_id: int,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve a test generation using its database ID."""

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
            FROM test_generation_results
            WHERE id = ?
            """,
            (generation_id,),
        ).fetchone()

        if row is None:
            return None

        generation = dict(row)

        generation["result"] = json.loads(
            generation.pop("result_json")
        )

        return generation

    finally:
        connection.close()


def get_latest_test_generation(
    upload_id: str,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve the latest test generation for a project."""

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
            FROM test_generation_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (upload_id,),
        ).fetchone()

        if row is None:
            return None

        generation = dict(row)

        generation["result"] = json.loads(
            generation.pop("result_json")
        )

        return generation

    finally:
        connection.close()


def list_test_generations(
    upload_id: str,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Retrieve all test generation history for a project."""

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
            FROM test_generation_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (upload_id,),
        ).fetchall()

        generations = []

        for row in rows:
            generation = dict(row)

            generation["result"] = json.loads(
                generation.pop("result_json")
            )

            generations.append(generation)

        return generations

    finally:
        connection.close()