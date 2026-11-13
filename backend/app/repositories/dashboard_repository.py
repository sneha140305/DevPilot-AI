import json
from pathlib import Path
from typing import Any

from app.db.database import DATABASE_PATH, get_connection


def get_dashboard_summary(
    db_path: Path | None = None,
) -> dict[str, Any]:
    """
    Calculate dashboard metrics using saved SQLite records.

    Metrics include:
    - Projects and code analysis
    - Code reviews and generated tests
    - Docker test executions
    - Security scanning
    - Code quality and technical debt

    Analysis metrics aggregate all saved analysis runs.
    Repeated analyses are counted separately.
    """

    if db_path is None:
        db_path = DATABASE_PATH

    connection = get_connection(db_path)

    try:
        # --------------------------------------------------
        # PROJECT METRICS
        # --------------------------------------------------

        total_projects = connection.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]

        # --------------------------------------------------
        # ANALYSIS AND SECURITY METRICS
        # --------------------------------------------------

        analysis_rows = connection.execute(
            """
            SELECT upload_id, result_json
            FROM analysis_results
            """
        ).fetchall()

        analyzed_project_ids = set()

        total_issues = 0

        total_security_issues = 0
        high_risk_security_issues = 0
        medium_risk_security_issues = 0
        low_risk_security_issues = 0

        security_rule_counts = {
            "SEC001": 0,
            "SEC002": 0,
            "SEC003": 0,
            "SEC004": 0,
            "SEC005": 0,
        }

        # Technical debt metrics
        total_technical_debt_issues = 0
        total_duplicate_blocks = 0

        maintainability_values = []
        complexity_values = []
        technical_debt_scores = []

        for row in analysis_rows:

            analyzed_project_ids.add(row["upload_id"])

            try:
                result: dict[str, Any] = json.loads(
                    row["result_json"]
                )

                if not isinstance(result, dict):
                    continue

                # Total analysis issues
                issue_count = result.get(
                    "total_issues",
                    0,
                )

                if type(issue_count) is int and issue_count >= 0:
                    total_issues += issue_count

                issues = result.get("issues", [])

                if not isinstance(issues, list):
                    issues = []

                # Security issue metrics
                for issue in issues:

                    if not isinstance(issue, dict):
                        continue

                    rule_id = issue.get("rule_id")
                    category = issue.get("category")
                    severity = issue.get("severity")

                    if category == "security":

                        total_security_issues += 1

                        if severity == "high":
                            high_risk_security_issues += 1

                        elif severity == "medium":
                            medium_risk_security_issues += 1

                        elif severity == "low":
                            low_risk_security_issues += 1

                        if rule_id in security_rule_counts:
                            security_rule_counts[rule_id] += 1

                # Technical debt issue metrics
                technical_debt_rule_ids = {
                    "CQ001",
                    "CQ002",
                    "CQ003",
                }

                total_technical_debt_issues += sum(
                    1
                    for issue in issues
                    if isinstance(issue, dict)
                    and issue.get("rule_id") in technical_debt_rule_ids
                )

                # Technical debt summary
                debt = result.get(
                    "technical_debt",
                    {},
                )

                if not isinstance(debt, dict):
                    debt = {}

                duplicate_count = debt.get(
                    "total_duplicate_blocks",
                    0,
                )

                if (
                    type(duplicate_count) is int
                    and duplicate_count >= 0
                ):
                    total_duplicate_blocks += duplicate_count

                maintainability = debt.get(
                    "average_maintainability_index"
                )

                if isinstance(maintainability, (int, float)) and 0 <= maintainability <= 100:
                        maintainability_values.append(
                            float(maintainability)
                        )

                complexity = debt.get(
                    "average_cyclomatic_complexity"
                )

                if isinstance(complexity, (int, float)) and complexity >= 0:
                        complexity_values.append(
                            float(complexity)
                        )

                debt_score = debt.get(
                    "technical_debt_score"
                )

                if (
                    type(debt_score) is int
                    and 0 <= debt_score <= 100
                ):
                    technical_debt_scores.append(debt_score)

            except (json.JSONDecodeError, TypeError):
                continue

        # Security score: heuristic, not a formal security rating.
        security_penalty = (
            high_risk_security_issues * 15
            + medium_risk_security_issues * 7
            + low_risk_security_issues * 2
        )

        security_score = max(
            0,
            100 - security_penalty,
        )

        # --------------------------------------------------
        # GENERATED TEST METRICS
        # --------------------------------------------------

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

                test_count = result.get(
                    "total_tests",
                    0,
                )

                if type(test_count) is int and test_count >= 0:
                    total_tests_generated += test_count

            except (json.JSONDecodeError, TypeError):
                continue

        # --------------------------------------------------
        # CODE REVIEW METRICS
        # --------------------------------------------------

        total_code_reviews = connection.execute(
            """
            SELECT COUNT(*)
            FROM review_results
            """
        ).fetchone()[0]

        # --------------------------------------------------
        # DOCKER TEST EXECUTION METRICS
        # --------------------------------------------------

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

        # --------------------------------------------------
        # LATEST TEST EXECUTION STATUS
        # --------------------------------------------------

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

                if isinstance(latest_result, dict):

                    status = latest_result.get("status")

                    if isinstance(status, str):
                        latest_execution_status = status

            except (json.JSONDecodeError, TypeError):
                latest_execution_status = "unknown"

        # --------------------------------------------------
        # TECHNICAL DEBT AGGREGATES
        # --------------------------------------------------

        average_maintainability_index = (
            round(
                sum(maintainability_values)
                / len(maintainability_values),
                2,
            )
            if maintainability_values
            else None
        )

        average_cyclomatic_complexity = (
            round(
                sum(complexity_values)
                / len(complexity_values),
                2,
            )
            if complexity_values
            else None
        )

        average_technical_debt_score = (
            round(
                sum(technical_debt_scores)
                / len(technical_debt_scores),
                2,
            )
            if technical_debt_scores
            else None
        )

        # --------------------------------------------------
        # FINAL DASHBOARD RESPONSE
        # --------------------------------------------------

        return {
            # Project metrics
            "total_projects": total_projects,
            "projects_analyzed": len(analyzed_project_ids),

            # Analysis metrics
            "total_issues": total_issues,

            # Code review metrics
            "total_code_reviews": total_code_reviews,

            # Test generation metrics
            "total_tests_generated": total_tests_generated,

            # Test execution metrics
            "total_test_executions": total_test_executions,
            "total_tests_passed": total_tests_passed,
            "total_tests_failed": total_tests_failed,
            "latest_execution_status": latest_execution_status,

            # Security metrics
            "total_security_issues": total_security_issues,
            "high_risk_security_issues": high_risk_security_issues,
            "medium_risk_security_issues": medium_risk_security_issues,
            "low_risk_security_issues": low_risk_security_issues,
            "security_score": security_score,
            "security_rule_counts": security_rule_counts,

            # Technical debt metrics
            "total_technical_debt_issues": (
                total_technical_debt_issues
            ),
            "total_duplicate_blocks": total_duplicate_blocks,
            "average_maintainability_index": (
                average_maintainability_index
            ),
            "average_cyclomatic_complexity": (
                average_cyclomatic_complexity
            ),
            "average_technical_debt_score": (
                average_technical_debt_score
            ),
        }

    finally:
        connection.close()

