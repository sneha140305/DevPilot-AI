import ast
from pathlib import Path
from typing import Any


REFACTORING_GUIDES = {
    "CQ001": {
        "title": "Reduce Cyclomatic Complexity",
        "priority": "High",
        "strategy": "simplify_conditionals",
        "steps": [
            "Identify deeply nested conditional statements.",
            "Extract independent conditions into descriptive helper functions.",
            "Use early returns where they improve readability.",
            "Separate validation logic from business logic.",
            "Keep each function focused on one responsibility.",
        ],
        "benefit": (
            "Simpler control flow improves readability, "
            "testing and maintenance."
        ),
    },
    "CQ002": {
        "title": "Break Down Long Function",
        "priority": "Medium",
        "strategy": "extract_helper_functions",
        "steps": [
            "Identify logically independent sections of the function.",
            "Group related statements into smaller responsibilities.",
            "Extract suitable sections into helper functions.",
            "Use descriptive function names.",
            "Keep inputs and return values explicit.",
        ],
        "benefit": (
            "Smaller functions are easier to understand, "
            "test and reuse."
        ),
    },
    "CQ003": {
        "title": "Remove Duplicate Code",
        "priority": "Medium",
        "strategy": "extract_shared_function",
        "steps": [
            "Compare the reported duplicate code locations.",
            "Identify the common functionality.",
            "Extract reusable functionality into a shared function.",
            "Replace repeated blocks with calls to the shared function.",
            "Run tests to confirm behavior remains unchanged.",
        ],
        "benefit": (
            "Reducing duplication makes future changes "
            "easier and more consistent."
        ),
    },
}


class RefactoringError(Exception):
    pass


def extract_source_context(
    source_code: str,
    line: int,
    radius: int = 8,
) -> dict[str, Any]:
    lines = source_code.splitlines()

    if line < 1 or line > len(lines):
        raise RefactoringError("Invalid source line.")

    start = max(0, line - radius - 1)
    end = min(len(lines), line + radius)

    return {
        "start_line": start + 1,
        "end_line": end,
        "source": "\n".join(lines[start:end]),
    }


def find_function_at_line(
    source_code: str,
    line: int,
) -> dict[str, Any] | None:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None

    candidates = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        end_line = getattr(node, "end_lineno", node.lineno)

        if node.lineno <= line <= end_line:
            candidates.append(node)

    if not candidates:
        return None

    # Prefer the smallest enclosing function.
    function = min(
        candidates,
        key=lambda node: (
            getattr(node, "end_lineno", node.lineno)
            - node.lineno
        ),
    )

    return {
        "name": function.name,
        "start_line": function.lineno,
        "end_line": getattr(
            function,
            "end_lineno",
            function.lineno,
        ),
        "arguments": [
            argument.arg
            for argument in function.args.args
        ],
    }


def build_refactoring_recommendation(
    issue: dict,
    source_code: str,
) -> dict[str, Any]:
    rule_id = issue.get("rule_id")

    guide = REFACTORING_GUIDES.get(rule_id)

    if guide is None:
        raise RefactoringError(
            f"No refactoring guide exists for {rule_id}."
        )

    line = issue.get("line")

    if not isinstance(line, int) or line < 1:
        raise RefactoringError("Invalid issue line.")

    context = extract_source_context(
        source_code,
        line,
    )

    function = find_function_at_line(
        source_code,
        line,
    )

    return {
        "rule_id": rule_id,
        "title": guide["title"],
        "priority": guide["priority"],
        "strategy": guide["strategy"],
        "file_path": issue.get("file_path"),
        "line": line,
        "issue": issue.get("message", ""),
        "function": function,
        "source_context": context,
        "recommended_steps": guide["steps"],
        "expected_benefit": guide["benefit"],
        "automatic_rewrite_available": False,
        "original_source_preserved": True,
    }


def rank_recommendations(
    recommendations: list[dict],
) -> list[dict]:
    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    return sorted(
        recommendations,
        key=lambda item: (
            priority_order.get(item["priority"], 3),
            item["file_path"],
            item["line"],
        ),
    )