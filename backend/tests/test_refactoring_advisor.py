import pytest
from app.services.refactoring_advisor import (
    RefactoringError,
    build_refactoring_recommendation,
    extract_source_context,
    find_function_at_line,
    rank_recommendations,
)


def test_extract_source_context():
    source = "\n".join(
        f"line_{number}"
        for number in range(1, 21)
    )

    result = extract_source_context(
        source,
        line=10,
        radius=2,
    )

    assert result["start_line"] == 8
    assert result["end_line"] == 12


def test_find_function_at_line():
    source = """
def calculate(value):
    if value > 10:
        return True
    return False
"""

    result = find_function_at_line(
        source,
        line=3,
    )

    assert result is not None
    assert result["name"] == "calculate"
    assert result["start_line"] == 2


def test_find_function_returns_none_outside_function():
    source = """
value = 10

def calculate():
    return 20
"""

    result = find_function_at_line(
        source,
        line=2,
    )

    assert result is None


def test_complexity_recommendation():
    source = """
def calculate(value):
    if value > 10:
        return True
    return False
"""

    issue = {
        "rule_id": "CQ001",
        "message": "High complexity",
        "file_path": "example.py",
        "line": 2,
    }

    result = build_refactoring_recommendation(
        issue,
        source,
    )

    assert result["strategy"] == "simplify_conditionals"
    assert result["priority"] == "High"
    assert result["original_source_preserved"] is True
    assert result["automatic_rewrite_available"] is False


def test_long_function_recommendation():
    source = """
def process_data():
    value = 10
    return value
"""

    issue = {
        "rule_id": "CQ002",
        "message": "Long function",
        "file_path": "example.py",
        "line": 2,
    }

    result = build_refactoring_recommendation(
        issue,
        source,
    )

    assert result["strategy"] == "extract_helper_functions"


def test_duplicate_code_recommendation():
    source = """
def calculate():
    return 10
"""

    issue = {
        "rule_id": "CQ003",
        "message": "Duplicate code",
        "file_path": "example.py",
        "line": 2,
    }

    result = build_refactoring_recommendation(
        issue,
        source,
    )

    assert result["strategy"] == "extract_shared_function"


def test_unsupported_rule():
    with pytest.raises(RefactoringError):
        build_refactoring_recommendation(
            {
                "rule_id": "UNKNOWN",
                "line": 1,
            },
            "value = 10",
        )


def test_invalid_line():
    with pytest.raises(RefactoringError):
        extract_source_context(
            "value = 10",
            line=10,
        )


def test_rank_recommendations():
    recommendations = [
        {
            "priority": "Low",
            "file_path": "b.py",
            "line": 2,
        },
        {
            "priority": "High",
            "file_path": "a.py",
            "line": 5,
        },
        {
            "priority": "Medium",
            "file_path": "c.py",
            "line": 1,
        },
    ]

    result = rank_recommendations(recommendations)

    assert result[0]["priority"] == "High"
    assert result[1]["priority"] == "Medium"
    assert result[2]["priority"] == "Low"