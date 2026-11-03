from typing import Any

REVIEW_TEMPLATES = {
    "PY001": {
        "explanation": (
            "This file contains invalid Python syntax. "
            "Python cannot parse the code correctly."
        ),
        "impact": (
            "The application may fail before the affected code can run."
        ),
        "fix": (
            "Check the reported line for missing colons, brackets, "
            "quotes, indentation, or other syntax mistakes."
        ),
    },
    "PY002": {
        "explanation": (
            "The eval() function dynamically evaluates a string "
            "as Python code."
        ),
        "impact": (
            "Untrusted input passed to eval() can execute unwanted code."
        ),
        "fix": (
            "Avoid eval(). Use safer alternatives such as ast.literal_eval() "
            "when you only need to parse Python literals."
        ),
    },
    "PY003": {
        "explanation": (
            "The exec() function dynamically executes Python code."
        ),
        "impact": (
            "Executing untrusted input can introduce serious security risks."
        ),
        "fix": (
            "Avoid exec() where possible. Replace dynamic execution "
            "with explicit functions or controlled operations."
        ),
    },
    "PY004": {
        "explanation": (
            "A bare except clause catches almost every exception, "
            "including exceptions that should usually not be suppressed."
        ),
        "impact": (
            "It can hide unexpected errors and make debugging difficult."
        ),
        "fix": (
            "Catch specific exceptions, such as ValueError or TypeError."
        ),
    },
    "PY005": {
        "explanation": (
            "A wildcard import imports multiple names without "
            "making their origin clear."
        ),
        "impact": (
            "It can cause naming conflicts and reduce code readability."
        ),
        "fix": (
            "Import only the functions or classes that your code needs."
        ),
    },
    "RUFF-F401": {
        "explanation": (
            "This import is not used anywhere in the analyzed file."
        ),
        "impact": (
            "Unused imports create unnecessary dependencies "
            "and reduce code cleanliness."
        ),
        "fix": (
            "Remove the import if it is not required."
        ),
    },
    "RUFF-F821": {
        "explanation": (
            "This code references a variable or name that Python "
            "cannot identify."
        ),
        "impact": (
            "It may cause a NameError when the affected code executes."
        ),
        "fix": (
            "Check the spelling and make sure the variable or function "
            "is defined or imported before use."
        ),
    },
    "RUFF-F841": {
        "explanation": (
            "A local variable is assigned a value but never used."
        ),
        "impact": (
            "It makes the code less clear and may indicate unnecessary work."
        ),
        "fix": (
            "Remove the unused variable or use it where intended."
        ),
    },
    "RUFF-E501": {
        "explanation": (
            "This line exceeds the configured maximum line length."
        ),
        "impact": (
            "Long lines can make code harder to read and maintain."
        ),
        "fix": (
            "Break the statement into shorter lines while preserving "
            "its behavior."
        ),
    },
    "RUFF-E722": {
        "explanation": (
            "A bare except clause catches exceptions without specifying "
            "which errors should be handled."
        ),
        "impact": (
            "Unexpected errors may be hidden."
        ),
        "fix": (
            "Catch the specific exception types your code expects."
        ),
    },
    "RUFF-F811": {
        "explanation": (
            "A name is defined more than once, potentially replacing "
            "an earlier definition."
        ),
        "impact": (
            "This can cause unexpected behavior and confusion."
        ),
        "fix": (
            "Remove the unnecessary definition or rename the conflicting "
            "variable or function."
        ),
    },
}


DEFAULT_REVIEW = {
    "explanation": (
        "The static analyzer detected a potential code quality issue."
    ),
    "impact": (
        "Review this issue to determine whether it affects reliability, "
        "readability, or maintainability."
    ),
    "fix": (
        "Inspect the reported code and follow the recommendation "
        "associated with the rule."
    ),
}


def review_issue(issue: dict[str, Any]) -> dict[str, Any]:
    """
    Generate an explanation and fix recommendation for one issue.
    This function does not execute or modify source code.
    """

    rule_id = issue.get("rule_id", "")
    template = REVIEW_TEMPLATES.get(rule_id, DEFAULT_REVIEW)

    return {
        **issue,
        "explanation": template["explanation"],
        "impact": template["impact"],
        "fix_suggestion": template["fix"],
        "review_provider": "rule_based",
    }


def review_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Review multiple issues.
    """

    return [review_issue(issue) for issue in issues]