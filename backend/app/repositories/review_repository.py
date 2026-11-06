import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def save_review(
    upload_id: str,
    result: dict[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    """
    Save a code review result in SQLite.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        cursor = connection.execute(
            """
            INSERT INTO review_results (
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

        review_id = cursor.lastrowid

        return get_review_by_id(
            review_id,
            db_path,
        )

    finally:
        connection.close()


def get_review_by_id(
    review_id: int,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve one review using its database ID.
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
            FROM review_results
            WHERE id = ?
            """,
            (review_id,),
        ).fetchone()

        if row is None:
            return None

        review = dict(row)

        review["result"] = json.loads(
            review.pop("result_json")
        )

        return review

    finally:
        connection.close()


def get_latest_review(
    upload_id: str,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve the latest code review for a project.
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
            FROM review_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (upload_id,),
        ).fetchone()

        if row is None:
            return None

        review = dict(row)

        review["result"] = json.loads(
            review.pop("result_json")
        )

        return review

    finally:
        connection.close()


def list_reviews(
    upload_id: str,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve all code review history for a project.
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
            FROM review_results
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (upload_id,),
        ).fetchall()

        reviews = []

        for row in rows:
            review = dict(row)

            review["result"] = json.loads(
                review.pop("result_json")
            )

            reviews.append(review)

        return reviews

    finally:
        connection.close()