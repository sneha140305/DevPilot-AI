from app.services.code_reviewer import (
    extract_code_context,
    get_confidence_level,
    get_root_cause,
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

def test_extract_code_context_highlights_issue_line():
    source_code = "\n".join(
        f"line {number}" for number in range(1, 9)
    )

    context = extract_code_context(
        source_code=source_code,
        line_number=5,
    )

    assert ">    5 | line 5" in context
    assert "    4 | line 4" in context
    assert "    6 | line 6" in context


def test_extract_code_context_invalid_line():
    assert extract_code_context(
        source_code="print('hello')",
        line_number=5,
    ) == ""


def test_root_cause_generation():
    issue = create_issue("PY004")

    root_cause = get_root_cause("PY004", issue)

    assert "exception" in root_cause.lower()
    assert "unexpected errors" in root_cause.lower()


def test_confidence_level_assessment():
    assert get_confidence_level("PY004", True) == "high"

    assert get_confidence_level("PY004", False) == "medium"

    assert get_confidence_level("UNKNOWN", True) == "low"


def test_review_issue_without_source_context():
    issue = create_issue("PY002")

    result = review_issue(issue)

    assert result["context_available"] is False
    assert result["code_context"] == ""
    assert result["confidence_level"] == "medium"
    assert result["root_cause"]
    assert len(result["debugging_steps"]) > 0


def test_review_multiple_files_with_correct_context():
    issues = [
        {
            **create_issue("PY002"),
            "file_path": "first.py",
            "line": 2,
        },
        {
            **create_issue("PY004"),
            "file_path": "second.py",
            "line": 2,
        },
    ]

    source_files = {
        "first.py": "def calculate():\n    eval('10 + 20')",
        "second.py": "try:\n    print('hello')\nexcept:\n    pass",
    }

    results = review_issues(
        issues=issues,
        source_files=source_files,
    )

    assert len(results) == 2

    assert "eval" in results[0]["code_context"]
    assert "except:" in results[1]["code_context"]

    assert results[0]["context_available"] is True
    assert results[1]["context_available"] is True