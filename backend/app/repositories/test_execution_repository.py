import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def save_test_execution(
    upload_id: str,
    result: dict[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Save a test execution result in SQLite."""

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO test_execution_results (
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

        execution_id = cursor.lastrowid

        return get_test_execution_by_id(
            execution_id,
            db_path,
        )

    finally:
        connection.close()


def get_test_execution_by_id(
    execution_id: int,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve a test execution by its database ID."""

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
            FROM test_execution_results
            WHERE id = ?
            """,
            (execution_id,),
        ).fetchone()

        if row is None:
            return None

        execution = dict(row)

        execution["result"] = json.loads(
            execution.pop("result_json")
        )

        return execution

    finally:
        connection.close()


def get_latest_test_execution(
    upload_id: str,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve the latest execution for a project."""

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
            FROM test_execution_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (upload_id,),
        ).fetchone()

        if row is None:
            return None

        execution = dict(row)

        execution["result"] = json.loads(
            execution.pop("result_json")
        )

        return execution

    finally:
        connection.close()


def list_test_executions(
    upload_id: str,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Retrieve all execution history for a project."""

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
            FROM test_execution_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (upload_id,),
        ).fetchall()

        executions = []

        for row in rows:
            execution = dict(row)

            execution["result"] = json.loads(
                execution.pop("result_json")
            )

            executions.append(execution)

        return executions

    finally:
        connection.close()