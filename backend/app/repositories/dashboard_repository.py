import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def get_dashboard_summary(
    db_path: Path | None = None,
) -> dict[str, int]:
    """
    Calculate dashboard metrics using saved SQLite records.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        # Total uploaded projects
        total_projects = connection.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]

        # Retrieve analysis results
        analysis_rows = connection.execute(
            """
            SELECT upload_id, result_json
            FROM analysis_results
            """
        ).fetchall()

        analyzed_project_ids = set()
        total_issues = 0

        for row in analysis_rows:
            analyzed_project_ids.add(row["upload_id"])

            try:
                result: dict[str, Any] = json.loads(
                    row["result_json"]
                )

                issue_count = result.get("total_issues", 0)

                if isinstance(issue_count, int) and issue_count >= 0:
                    total_issues += issue_count

            except (json.JSONDecodeError, TypeError):
                continue

        # Total generated tests
        test_rows = connection.execute(
            """
            SELECT result_json
            FROM test_generation_results
            """
        ).fetchall()

        total_tests_generated = 0

        for row in test_rows:
            try:
                result = json.loads(row["result_json"])

                test_count = result.get("total_tests", 0)

                if isinstance(test_count, int) and test_count >= 0:
                    total_tests_generated += test_count

            except (json.JSONDecodeError, TypeError):
                continue

        # Total saved code review records
        total_code_reviews = connection.execute(
            """
            SELECT COUNT(*)
            FROM review_results
            """
        ).fetchone()[0]

        return {
            "total_projects": total_projects,
            "projects_analyzed": len(analyzed_project_ids),
            "total_issues": total_issues,
            "total_tests_generated": total_tests_generated,
            "total_code_reviews": total_code_reviews,
        }

    finally:
        connection.close()