from app.db.database import initialize_database
from app.main import app
from app.repositories import dashboard_repository
from fastapi.testclient import TestClient


def setup_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_dashboard.db"

    initialize_database(db_path)

    monkeypatch.setattr(
        dashboard_repository,
        "DATABASE_PATH",
        db_path,
    )

    return db_path


def test_dashboard_summary_empty_database(
    tmp_path,
    monkeypatch,
):
    setup_database(tmp_path, monkeypatch)

    client = TestClient(app)

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["summary"] == {
        "total_projects": 0,
        "projects_analyzed": 0,
        "total_issues": 0,
        "total_tests_generated": 0,
        "total_code_reviews": 0,
        "total_test_executions": 0,
        "total_tests_passed": 0,
        "total_tests_failed": 0,
        "latest_execution_status": None,
    }


def test_dashboard_summary_aggregates_records(
    tmp_path,
    monkeypatch,
):
    db_path = setup_database(tmp_path, monkeypatch)

    from app.db.database import get_connection

    connection = get_connection(db_path)

    try:
        projects = [
            ("a" * 32, "project1.py", "python"),
            ("b" * 32, "project2.py", "python"),
            ("c" * 32, "project3.zip", "zip"),
        ]

        connection.executemany(
            """
            INSERT INTO projects (
                upload_id,
                original_filename,
                upload_type
            )
            VALUES (?, ?, ?)
            """,
            projects,
        )

        analyses = [
            ("a" * 32, '{"total_issues": 5}'),
            ("a" * 32, '{"total_issues": 3}'),
            ("b" * 32, '{"total_issues": 4}'),
        ]

        connection.executemany(
            """
            INSERT INTO analysis_results (
                upload_id,
                result_json
            )
            VALUES (?, ?)
            """,
            analyses,
        )

        reviews = [
            ("a" * 32, '{"total_issues": 8}'),
            ("b" * 32, '{"total_issues": 4}'),
        ]

        connection.executemany(
            """
            INSERT INTO review_results (
                upload_id,
                result_json
            )
            VALUES (?, ?)
            """,
            reviews,
        )

        generations = [
            ("a" * 32, '{"total_tests": 3}'),
            ("b" * 32, '{"total_tests": 5}'),
        ]

        connection.executemany(
            """
            INSERT INTO test_generation_results (
                upload_id,
                result_json
            )
            VALUES (?, ?)
            """,
            generations,
        )

        connection.commit()

    finally:
        connection.close()

    client = TestClient(app)

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200

    summary = response.json()["summary"]

    assert summary["total_projects"] == 3
    assert summary["projects_analyzed"] == 2
    assert summary["total_issues"] == 12
    assert summary["total_tests_generated"] == 8
    assert summary["total_code_reviews"] == 2