import pytest

from app.services.security_analyzer import analyze_security


@pytest.mark.parametrize(
    "source, expected_rule",
    [
        (
            'API_KEY = "sk_test_123456789"',
            "SEC001",
        ),
        (
            'cursor.execute(f"SELECT * FROM users WHERE id={user_id}")',
            "SEC002",
        ),
        (
            'subprocess.run(command, shell=True)',
            "SEC003",
        ),
        (
            "pickle.loads(user_data)",
            "SEC004",
        ),
        (
            "hashlib.md5(data)",
            "SEC005",
        ),
    ],
)
def test_detect_security_vulnerabilities(source, expected_rule):

    issues = analyze_security(
        source,
        "main.py",
    )

    assert any(
        issue["rule_id"] == expected_rule
        for issue in issues
    )


def test_clean_code_has_no_security_issues():

    source = """
def add(a, b):
    return a + b
"""

    issues = analyze_security(source, "main.py")

    assert issues == []


def test_placeholder_api_key_is_not_flagged():

    source = 'API_KEY = "your_api_key"'

    issues = analyze_security(source, "main.py")

    assert issues == []


def test_shell_false_is_not_flagged():

    source = "subprocess.run(command, shell=False)"

    issues = analyze_security(source, "main.py")

    assert issues == []


def test_syntax_error_returns_empty_list():

    source = "def broken("

    issues = analyze_security(source, "main.py")

    assert issues == []


def test_issue_contains_location():

    source = """
import pickle
data = pickle.loads(user_data)
"""

    issues = analyze_security(source, "main.py")

    assert len(issues) == 1
    assert issues[0]["file_path"] == "main.py"
    assert issues[0]["line"] == 3
    assert issues[0]["column"] >= 0