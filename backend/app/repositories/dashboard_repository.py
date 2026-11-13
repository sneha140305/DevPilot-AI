import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection

SECURITY_RULES = (
    "SEC001",
    "SEC002",
    "SEC003",
    "SEC004",
    "SEC005",
)

SEVERITY_WEIGHTS = {
    "high": 15,
    "medium": 7,
    "low": 2,
}


def get_dashboard_summary(
    db_path: Path | None = None,
) -> dict[str, Any]:
    """
    Calculate dashboard metrics using saved SQLite records.

    Security score is a heuristic based on saved security findings.
    It is not a formal security rating.
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

        # Security metrics
        total_security_issues = 0
        high_risk_security_issues = 0
        medium_risk_security_issues = 0
        low_risk_security_issues = 0

        security_rule_counts = {
            rule_id: 0 for rule_id in SECURITY_RULES
        }

        for row in analysis_rows:
            analyzed_project_ids.add(row["upload_id"])

            try:
                result = json.loads(row["result_json"])

                if not isinstance(result, dict):
                    continue

                issue_count = result.get("total_issues", 0)

                if type(issue_count) is int and issue_count >= 0:
                    total_issues += issue_count

                issues = result.get("issues", [])

                if not isinstance(issues, list):
                    continue

                for issue in issues:
                    if not isinstance(issue, dict):
                        continue

                    rule_id = issue.get("rule_id")
                    category = issue.get("category")

                    is_security_issue = (
                        category == "security"
                        or (
                            isinstance(rule_id, str)
                            and rule_id.startswith("SEC")
                        )
                    )

                    if not is_security_issue:
                        continue

                    total_security_issues += 1

                    if rule_id in security_rule_counts:
                        security_rule_counts[rule_id] += 1

                    severity = issue.get("severity")

                    if severity == "high":
                        high_risk_security_issues += 1

                    elif severity == "medium":
                        medium_risk_security_issues += 1

                    elif severity == "low":
                        low_risk_security_issues += 1

            except (json.JSONDecodeError, TypeError):
                continue

        # Calculate heuristic security score
        security_penalty = (
            high_risk_security_issues * SEVERITY_WEIGHTS["high"]
            + medium_risk_security_issues * SEVERITY_WEIGHTS["medium"]
            + low_risk_security_issues * SEVERITY_WEIGHTS["low"]
        )

        security_score = max(0, 100 - security_penalty)

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

                if not isinstance(result, dict):
                    continue

                test_count = result.get("total_tests", 0)

                if type(test_count) is int and test_count >= 0:
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

        # Retrieve saved Docker test executions
        execution_rows = connection.execute(
            """
            SELECT result_json
            FROM test_execution_results
            """
        ).fetchall()

        total_test_executions = len(execution_rows)
        total_tests_passed = 0
        total_tests_failed = 0

        for row in execution_rows:
            try:
                result = json.loads(row["result_json"])

                if not isinstance(result, dict):
                    continue

                passed = result.get("passed", 0)
                failed = result.get("failed", 0)

                if type(passed) is int and passed >= 0:
                    total_tests_passed += passed

                if type(failed) is int and failed >= 0:
                    total_tests_failed += failed

            except (json.JSONDecodeError, TypeError):
                continue

        # Latest execution status
        latest_execution = connection.execute(
            """
            SELECT result_json
            FROM test_execution_results
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

        latest_execution_status = None

        if latest_execution is not None:
            try:
                latest_result = json.loads(
                    latest_execution["result_json"]
                )

                if not isinstance(latest_result, dict):
                    latest_execution_status = "unknown"
                else:
                    status = latest_result.get("status")

                    if isinstance(status, str):
                        latest_execution_status = status

            except (json.JSONDecodeError, TypeError):
                latest_execution_status = "unknown"

        return {
            "total_projects": total_projects,
            "projects_analyzed": len(analyzed_project_ids),
            "total_issues": total_issues,
            "total_tests_generated": total_tests_generated,
            "total_code_reviews": total_code_reviews,
            "total_test_executions": total_test_executions,
            "total_tests_passed": total_tests_passed,
            "total_tests_failed": total_tests_failed,
            "latest_execution_status": latest_execution_status,

            # Security dashboard metrics
            "total_security_issues": total_security_issues,
            "high_risk_security_issues": high_risk_security_issues,
            "medium_risk_security_issues": medium_risk_security_issues,
            "low_risk_security_issues": low_risk_security_issues,
            "security_score": security_score,
            "security_rule_counts": security_rule_counts,
        }

    finally:
        connection.close()