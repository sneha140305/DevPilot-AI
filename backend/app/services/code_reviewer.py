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
        "fix": "Remove the import if it is not required.",
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
        "impact": "Unexpected errors may be hidden.",
        "fix": "Catch the specific exception types your code expects.",
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


ROOT_CAUSE_TEMPLATES = {
    "PY001": (
        "The Python parser encountered invalid syntax near the reported "
        "location. A missing delimiter, incorrect indentation, or "
        "malformed statement may be responsible."
    ),
    "PY002": (
        "The code uses dynamic expression evaluation. The underlying "
        "risk is that input may be interpreted as executable Python."
    ),
    "PY003": (
        "The code dynamically executes Python statements instead of "
        "using explicit, controlled program operations."
    ),
    "PY004": (
        "The exception handler does not specify an exception type, "
        "so it can catch unexpected errors."
    ),
    "PY005": (
        "The code imports names using a wildcard, making dependencies "
        "and name origins less explicit."
    ),
    "RUFF-F401": (
        "An imported name is not referenced in the analyzed file."
    ),
    "RUFF-F821": (
        "A referenced name could not be resolved by static analysis. "
        "It may be misspelled, missing, or outside the available scope."
    ),
    "RUFF-F841": (
        "A local variable receives a value that is not subsequently used."
    ),
    "RUFF-E501": (
        "The reported source line exceeds the configured maximum length."
    ),
    "RUFF-E722": (
        "The exception handler does not restrict which exception types "
        "it catches."
    ),
    "RUFF-F811": (
        "A name is defined more than once in a way that creates a "
        "redefinition warning."
    ),
}


DEBUGGING_STEPS = {
    "PY001": [
        "Inspect the reported line and the line immediately before it.",
        "Check matching parentheses, brackets, and quotation marks.",
        "Verify indentation and required colons.",
        "Run Python syntax validation again after correcting the issue.",
    ],
    "PY002": [
        "Identify the data passed into eval().",
        "Determine whether that data can originate from an untrusted source.",
        "Check whether ast.literal_eval() or explicit parsing is sufficient.",
        "Replace dynamic evaluation where possible.",
    ],
    "PY003": [
        "Identify the string or input passed into exec().",
        "Check whether external input can influence the executed statements.",
        "Replace dynamic execution with explicit functions or operations.",
        "Review the resulting implementation for unintended execution paths.",
    ],
    "PY004": [
        "Inspect the operations inside the except block.",
        "Identify the exceptions the code actually expects.",
        "Replace the bare handler with specific exception types.",
        "Ensure unexpected exceptions are not silently hidden.",
    ],
    "PY005": [
        "Identify the module being imported.",
        "Determine which names are actually needed.",
        "Replace the wildcard import with explicit imports.",
        "Check for naming conflicts after modifying the import.",
    ],
    "RUFF-F401": [
        "Locate the unused import.",
        "Search the file for references to the imported name.",
        "Remove the import if it is unnecessary.",
        "Run static analysis again.",
    ],
    "RUFF-F821": [
        "Identify the unresolved name in the reported message.",
        "Check its spelling and capitalization.",
        "Verify that it is defined or imported in the required scope.",
        "Check whether the name should be passed as a function parameter.",
    ],
    "RUFF-F841": [
        "Locate the variable assignment.",
        "Check whether the variable is used later.",
        "Remove the assignment if it is unnecessary.",
        "Otherwise, correct the missing usage.",
    ],
    "RUFF-E501": [
        "Inspect the reported line.",
        "Identify a suitable place to split the statement.",
        "Use parentheses or another appropriate multiline structure.",
        "Run the linter again.",
    ],
    "RUFF-E722": [
        "Locate the bare exception handler.",
        "Identify the exception types the code expects.",
        "Replace the bare handler with specific exception types.",
        "Verify that unexpected exceptions remain visible.",
    ],
    "RUFF-F811": [
        "Search for other definitions of the same name.",
        "Determine whether the repeated definition is intentional.",
        "Remove or rename the unnecessary definition.",
        "Check references to the affected name.",
    ],
}


def extract_code_context(
    source_code: str | None,
    line_number: int,
    radius: int = 3,
) -> str:
    """
    Return a numbered source snippet around an issue.

    This function only reads source text.
    It never executes or modifies uploaded code.
    """

    if not source_code or line_number < 1:
        return ""

    lines = source_code.splitlines()

    if line_number > len(lines):
        return ""

    start = max(1, line_number - radius)
    end = min(len(lines), line_number + radius)

    context_lines = []

    for current_line in range(start, end + 1):
        marker = ">" if current_line == line_number else " "

        context_lines.append(
            f"{marker} {current_line:4} | {lines[current_line - 1]}"
        )

    return "\n".join(context_lines)


def get_root_cause(
    rule_id: str,
    issue: dict[str, Any],
) -> str:
    """
    Generate a deterministic root-cause explanation.

    This is a rule-based assessment, not proof of runtime behavior.
    """

    root_cause = ROOT_CAUSE_TEMPLATES.get(
        rule_id,
        "The static analyzer identified a potential issue. "
        "Additional investigation is required to establish its cause.",
    )

    message = issue.get("message", "")

    if rule_id == "RUFF-F821" and message:
        root_cause += f" Analyzer message: {message}"

    return root_cause


def get_confidence_level(
    rule_id: str,
    context_available: bool,
) -> str:
    """
    Estimate confidence in the explanation.

    This describes confidence in the rule-based assessment,
    not a statistically calibrated probability.
    """

    if rule_id not in REVIEW_TEMPLATES:
        return "low"

    if rule_id == "PY001":
        return "medium" if context_available else "low"

    if context_available:
        return "high"

    return "medium"


def review_issue(
    issue: dict[str, Any],
    source_code: str | None = None,
) -> dict[str, Any]:
    """
    Generate an explanation, root cause, and debugging guidance
    for one issue without executing or modifying source code.
    """

    rule_id = issue.get("rule_id", "")
    template = REVIEW_TEMPLATES.get(rule_id, DEFAULT_REVIEW)

    line_number = issue.get("line", 0)

    code_context = extract_code_context(
        source_code=source_code,
        line_number=line_number,
    )

    context_available = bool(code_context)

    debugging_steps = DEBUGGING_STEPS.get(
        rule_id,
        [
            "Inspect the reported source location.",
            "Understand the relevant rule and its recommendation.",
            "Determine whether the issue affects application behavior.",
            "Apply an appropriate correction and rerun static analysis.",
        ],
    )

    return {
        **issue,
        "explanation": template["explanation"],
        "impact": template["impact"],
        "fix_suggestion": template["fix"],
        "review_provider": "rule_based",
        "code_context": code_context,
        "root_cause": get_root_cause(rule_id, issue),
        "debugging_steps": list(debugging_steps),
        "confidence_level": get_confidence_level(
            rule_id,
            context_available,
        ),
        "context_available": context_available,
    }


def review_issues(
    issues: list[dict[str, Any]],
    source_files: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Review multiple issues using their corresponding source files.

    source_files maps relative file paths to source code.
    """

    source_files = source_files or {}

    reviewed = []

    for issue in issues:
        file_path = issue.get("file_path", "")
        source_code = source_files.get(file_path)

        reviewed.append(
            review_issue(
                issue=issue,
                source_code=source_code,
            )
        )

    return reviewed
