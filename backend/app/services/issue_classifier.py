from app.services.rule_registry import (
    DEFAULT_RULE,
    RULE_REGISTRY,
)

SEVERITY_WEIGHTS = {
    "high": 15,
    "medium": 7,
    "low": 2,
}


CATEGORY_NAMES = {
    "security": "security",
    "correctness": "correctness",
    "maintainability": "maintainability",
    "style": "style",
}


def get_duplicate_group(rule_id: str) -> str:
    """
    Map equivalent findings to the same duplicate group.
    """

    duplicate_groups = {
        "PY004": "BARE_EXCEPT",
        "RUFF-E722": "BARE_EXCEPT",
    }

    return duplicate_groups.get(rule_id, rule_id)


def classify_issue(issue: dict) -> dict:
    """
    Apply centralized rule metadata to an issue.
    """

    rule_id = issue["rule_id"]

    rule = RULE_REGISTRY.get(
        rule_id,
        DEFAULT_RULE,
    )

    classified_issue = {
        **issue,
        "rule_name": rule["name"],
        "severity": rule["severity"],
        "category": rule["category"],
        "confidence": rule["confidence"],
        "suggestion": rule["suggestion"],
    }

    return classified_issue


def remove_duplicate_issues(issues: list[dict]) -> list[dict]:
    """
    Remove duplicate findings from AST and Ruff.
    """

    unique_issues = {}
    
    for issue in issues:

        rule_id = issue["rule_id"]

        duplicate_group = get_duplicate_group(rule_id)

        key = (
            issue["file_path"],
            issue["line"],
            duplicate_group,
        )

        if key not in unique_issues:
            unique_issues[key] = issue

    return list(unique_issues.values())


def classify_issues(issues: list[dict]) -> dict:
    """
    Classify, deduplicate, and summarize all findings.
    """

    unique_issues = remove_duplicate_issues(issues)

    classified_issues = [
        classify_issue(issue)
        for issue in unique_issues
    ]

    severity_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    category_counts = {
        "security": 0,
        "correctness": 0,
        "maintainability": 0,
        "style": 0,
    }

    penalty = 0

    for issue in classified_issues:

        severity = issue["severity"]
        category = issue["category"]

        severity_counts[severity] += 1
        category_counts[category] += 1

        penalty += SEVERITY_WEIGHTS[severity]

    quality_score = max(
        0,
        100 - penalty,
    )

    return {
        "issues": classified_issues,
        "total_issues": len(classified_issues),
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "quality_score": quality_score,
    }