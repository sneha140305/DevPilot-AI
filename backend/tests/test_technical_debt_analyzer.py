import ast

from app.services.technical_debt_analyzer import (
    analyze_technical_debt,
    calculate_complexity,
)


def test_simple_function_complexity():
    source = """
def calculate():
    return 10
"""

    tree = ast.parse(source)
    function = tree.body[0]

    assert calculate_complexity(function) == 1


def test_conditional_complexity():
    source = """
def calculate(value):
    if value > 10:
        return True
    else:
        return False
"""

    tree = ast.parse(source)
    function = tree.body[0]

    assert calculate_complexity(function) == 2


def test_boolean_complexity():
    source = """
def calculate(a, b, c):
    if a and b or c:
        return True
    return False
"""

    tree = ast.parse(source)
    function = tree.body[0]

    assert calculate_complexity(function) == 4


def test_long_function_detection():
    source = (
        "def long_function():\n"
        + "    value = 1\n" * 55
        + "    return value\n"
    )

    result = analyze_technical_debt([
        {
            "file_path": "example.py",
            "source_code": source,
        }
    ])

    assert any(
        issue["rule_id"] == "CQ002"
        for issue in result["issues"]
    )


def test_high_complexity_detection():
    source = """
def complex_function(value):
    if value > 1:
        if value > 2:
            if value > 3:
                if value > 4:
                    if value > 5:
                        if value > 6:
                            if value > 7:
                                if value > 8:
                                    if value > 9:
                                        if value > 10:
                                            return True
    return False
"""

    result = analyze_technical_debt([
        {
            "file_path": "example.py",
            "source_code": source,
        }
    ])

    assert any(
        issue["rule_id"] == "CQ001"
        for issue in result["issues"]
    )


def test_duplicate_block_detection():
    first = """
def first():
    value = 10
    result = value + 5
    print(result)
    return result
"""

    second = """
def second():
    value = 10
    result = value + 5
    print(result)
    return result
"""

    result = analyze_technical_debt([
        {
            "file_path": "first.py",
            "source_code": first,
        },
        {
            "file_path": "second.py",
            "source_code": second,
        },
    ])

    assert result["total_duplicate_blocks"] > 0
    assert any(
        issue["rule_id"] == "CQ003"
        for issue in result["issues"]
    )


def test_empty_project():
    result = analyze_technical_debt([])

    assert result["total_functions"] == 0
    assert result["total_duplicate_blocks"] == 0
    assert result["technical_debt_score"] == 100
    assert result["average_maintainability_index"] == 100


def test_syntax_error_is_skipped():
    result = analyze_technical_debt([
        {
            "file_path": "broken.py",
            "source_code": "def broken(:",
        }
    ])

    assert result["files"][0]["status"] == "skipped"