import sqlite3

from app.db.database import get_connection, initialize_database


def test_database_initialization(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    assert db_path.exists()


def test_all_tables_are_created(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    connection = get_connection(db_path)

    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    )

    tables = {
        row["name"]
        for row in cursor.fetchall()
    }

    connection.close()

    expected_tables = {
        "projects",
        "analysis_results",
        "review_results",
        "test_generation_results",
    }

    assert expected_tables.issubset(tables)


def test_project_can_be_inserted(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    connection = get_connection(db_path)

    connection.execute(
        """
        INSERT INTO projects (
            upload_id,
            original_filename,
            upload_type
        )
        VALUES (?, ?, ?)
        """,
        ("test123", "calculator.py", "python"),
    )

    connection.commit()

    project = connection.execute(
        """
        SELECT *
        FROM projects
        WHERE upload_id = ?
        """,
        ("test123",),
    ).fetchone()

    connection.close()

    assert project is not None
    assert project["original_filename"] == "calculator.py"


def test_foreign_key_prevents_orphan_results(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    connection = get_connection(db_path)

    try:

        try:

            connection.execute(
                """
                INSERT INTO analysis_results (
                    upload_id,
                    result_json
                )
                VALUES (?, ?)
                """,
                ("missing_project", '{"issues": []}'),
            )

            connection.commit()

            assert False, "Foreign key constraint was not enforced."

        except sqlite3.IntegrityError:
            connection.rollback()

    finally:

        connection.close()


def test_deleting_project_cascades_to_results(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    connection = get_connection(db_path)

    connection.execute(
        """
        INSERT INTO projects (
            upload_id,
            original_filename,
            upload_type
        )
        VALUES (?, ?, ?)
        """,
        ("project123", "main.py", "python"),
    )

    connection.execute(
        """
        INSERT INTO analysis_results (
            upload_id,
            result_json
        )
        VALUES (?, ?)
        """,
        ("project123", '{"issues": []}'),
    )

    connection.commit()

    connection.execute(
        "DELETE FROM projects WHERE upload_id = ?",
        ("project123",),
    )

    connection.commit()

    remaining = connection.execute(
        """
        SELECT COUNT(*)
        FROM analysis_results
        WHERE upload_id = ?
        """,
        ("project123",),
    ).fetchone()[0]

    connection.close()

    assert remaining == 0