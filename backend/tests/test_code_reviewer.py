from app.services.code_reviewer import (
    review_issue,
    review_issues,
)


def create_issue(rule_id="PY002"):
    return {
        "rule_id": rule_id,
        "rule_name": "Test Rule",
        "severity": "high",
        "category": "security",
        "message": "Test issue detected",
        "file_path": "test.py",
        "line": 5,
        "column": 1,
        "suggestion": "Test suggestion",
        "confidence": 0.95,
    }


def test_review_eval_issue():
    result = review_issue(create_issue("PY002"))

    assert result["review_provider"] == "rule_based"
    assert "eval()" in result["explanation"]
    assert result["fix_suggestion"]


def test_review_exec_issue():
    result = review_issue(create_issue("PY003"))

    assert "exec()" in result["explanation"]
    assert result["impact"]


def test_review_bare_except_issue():
    result = review_issue(create_issue("PY004"))

    assert "except" in result["explanation"]
    assert "specific" in result["fix_suggestion"]


def test_review_unused_import():
    result = review_issue(create_issue("RUFF-F401"))

    assert "import" in result["explanation"].lower()


def test_unknown_rule_uses_default_review():
    result = review_issue(create_issue("UNKNOWN"))

    assert result["explanation"]
    assert result["impact"]
    assert result["fix_suggestion"]


def test_review_multiple_issues():
    issues = [
        create_issue("PY002"),
        create_issue("PY003"),
        create_issue("PY004"),
    ]

    results = review_issues(issues)

    assert len(results) == 3
    assert all(
        item["review_provider"] == "rule_based"
        for item in results
    )


def test_review_preserves_original_issue():
    issue = create_issue()

    result = review_issue(issue)

    assert result["rule_id"] == issue["rule_id"]
    assert result["file_path"] == issue["file_path"]
    assert result["line"] == issue["line"]


def test_review_does_not_modify_original_issue():
    issue = create_issue()
    original = issue.copy()

    review_issue(issue)

    assert issue == original