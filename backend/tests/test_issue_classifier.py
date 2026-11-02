from app.services.issue_classifier import (
    classify_issues,
    remove_duplicate_issues,
)


def create_issue(rule_id, line=1):

    return {
        "rule_id": rule_id,
        "severity": "low",
        "message": "Test issue",
        "file_path": "main.py",
        "line": line,
        "column": 0,
        "suggestion": "Fix the issue.",
    }


def test_classify_high_severity_issue():

    result = classify_issues([
        create_issue("RUFF-F821"),
    ])

    assert result["total_issues"] == 1
    assert result["severity_counts"]["high"] == 1

    assert result["issues"][0]["category"] == "correctness"


def test_classify_security_issue():

    result = classify_issues([
        create_issue("PY002"),
    ])

    assert result["category_counts"]["security"] == 1

    assert result["issues"][0]["rule_name"] == "Dangerous eval Usage"


def test_remove_duplicate_bare_except():

    issues = [
        create_issue("PY004", line=5),
        create_issue("RUFF-E722", line=5),
    ]

    unique_issues = remove_duplicate_issues(issues)

    assert len(unique_issues) == 1


def test_same_rule_on_different_lines_is_not_duplicate():

    issues = [
        create_issue("RUFF-F401", line=2),
        create_issue("RUFF-F401", line=8),
    ]

    unique_issues = remove_duplicate_issues(issues)

    assert len(unique_issues) == 2


def test_quality_score_calculation():

    issues = [
        create_issue("RUFF-F821"),
        create_issue("RUFF-F401"),
        create_issue("RUFF-E501"),
    ]

    result = classify_issues(issues)

    # High = 15, Medium = 7, Low = 2.
    # 100 - 15 - 7 - 2 = 76.

    assert result["quality_score"] == 76


def test_clean_project_has_perfect_score():

    result = classify_issues([])

    assert result["total_issues"] == 0
    assert result["quality_score"] == 100


def test_quality_score_never_negative():

    issues = [
        create_issue("RUFF-F821", line=index)
        for index in range(1, 15)
    ]

    result = classify_issues(issues)

    assert result["quality_score"] == 0


def test_unknown_rule_uses_default_classification():

    result = classify_issues([
        create_issue("UNKNOWN-RULE"),
    ])

    issue = result["issues"][0]

    assert issue["severity"] == "low"
    assert issue["category"] == "style"
    assert issue["confidence"] == 0.70