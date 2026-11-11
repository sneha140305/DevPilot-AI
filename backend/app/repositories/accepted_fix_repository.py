from app.db.database import DATABASE_PATH, get_connection


def save_accepted_fix(
    fix_id: str,
    upload_id: str,
    file_path: str,
    rule_id: str,
    line: int,
    accepted_path: str,
    original_sha256: str,
    accepted_sha256: str,
    db_path=None,
) -> dict:
    """Save accepted fix metadata in SQLite."""

    database = db_path or DATABASE_PATH
    connection = get_connection(database)

    try:
        connection.execute(
            """
            INSERT INTO accepted_fixes (
                id,
                upload_id,
                file_path,
                rule_id,
                line,
                accepted_path,
                original_sha256,
                accepted_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fix_id,
                upload_id,
                file_path,
                rule_id,
                line,
                accepted_path,
                original_sha256,
                accepted_sha256,
            ),
        )

        connection.commit()

        return get_accepted_fix(fix_id, database)

    finally:
        connection.close()


def get_accepted_fix(
    fix_id: str,
    db_path=None,
) -> dict | None:
    """Retrieve one accepted fix."""

    database = db_path or DATABASE_PATH
    connection = get_connection(database)

    try:
        row = connection.execute(
            """
            SELECT *
            FROM accepted_fixes
            WHERE id = ?
            """,
            (fix_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def list_accepted_fixes(
    upload_id: str,
    db_path=None,
) -> list[dict]:
    """Retrieve all accepted fixes for a project."""

    database = db_path or DATABASE_PATH
    connection = get_connection(database)

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM accepted_fixes
            WHERE upload_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (upload_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()