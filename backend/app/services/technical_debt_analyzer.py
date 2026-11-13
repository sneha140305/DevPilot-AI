import ast
import hashlib
from collections import defaultdict
from typing import Any

MAX_COMPLEXITY = 10
MAX_FUNCTION_LINES = 50
MIN_DUPLICATE_STATEMENTS = 3


class FunctionComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity without executing source code."""

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Match(self, node):
        self.complexity += len(node.cases)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Nested function complexity is measured separately.
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_ClassDef(self, node):
        return


def calculate_complexity(function_node: ast.AST) -> int:
    visitor = FunctionComplexityVisitor()

    for statement in function_node.body:
        visitor.visit(statement)

    return visitor.complexity


def get_function_line_count(node: ast.AST) -> int:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start)

    return max(1, end - start + 1)


def normalize_ast(node: ast.AST) -> str:
    """
    Normalize identifiers and literal values to identify
    structurally similar code blocks.

    This is heuristic duplicate detection, not semantic equivalence.
    """

    class Normalizer(ast.NodeTransformer):

        def visit_Name(self, current):
            return ast.copy_location(
                ast.Name(id="VARIABLE", ctx=current.ctx),
                current,
            )

        def visit_Constant(self, current):
            return ast.copy_location(
                ast.Constant(value="LITERAL"),
                current,
            )

        def visit_arg(self, current):
            current.arg = "ARGUMENT"
            return current

        def visit_FunctionDef(self, current):
            current.name = "FUNCTION"
            current.decorator_list = []
            return self.generic_visit(current)

        def visit_AsyncFunctionDef(self, current):
            current.name = "FUNCTION"
            current.decorator_list = []
            return self.generic_visit(current)

    normalized = Normalizer().visit(node)
    ast.fix_missing_locations(normalized)

    return ast.dump(
        normalized,
        include_attributes=False,
    )


def find_duplicate_blocks(
    parsed_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fingerprints = defaultdict(list)

    for file_data in parsed_files:
        tree = file_data["tree"]
        file_path = file_data["file_path"]

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            statements = node.body

            if len(statements) < MIN_DUPLICATE_STATEMENTS:
                continue

            for start in range(
                len(statements) - MIN_DUPLICATE_STATEMENTS + 1
            ):
                block = statements[
                    start:start + MIN_DUPLICATE_STATEMENTS
                ]

                normalized = "|".join(
                    normalize_ast(statement)
                    for statement in block
                )

                fingerprint = hashlib.sha256(
                    normalized.encode("utf-8")
                ).hexdigest()

                fingerprints[fingerprint].append({
                    "file_path": file_path,
                    "line": getattr(block[0], "lineno", 1),
                    "function": node.name,
                })

    duplicates = []

    for occurrences in fingerprints.values():
        unique_locations = {
            (
                item["file_path"],
                item["line"],
                item["function"],
            )
            for item in occurrences
        }

        if len(unique_locations) < 2:
            continue

        duplicates.append({
            "occurrences": sorted(
                [
                    {
                        "file_path": item[0],
                        "line": item[1],
                        "function": item[2],
                    }
                    for item in unique_locations
                ],
                key=lambda item: (
                    item["file_path"],
                    item["line"],
                ),
            )
        })

    return duplicates


def analyze_technical_debt(
    file_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze complexity, long functions and duplicate code."""

    parsed_files = []
    file_reports = []
    issues = []

    total_complexity = 0
    total_functions = 0
    total_duplicate_blocks = 0

    for item in file_data:
        file_path = item["file_path"]
        source_code = item["source_code"]

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            file_reports.append({
                "file_path": file_path,
                "status": "skipped",
                "function_count": 0,
                "average_complexity": 0,
                "max_complexity": 0,
                "max_function_lines": 0,
                "maintainability_index": None,
                "duplicate_blocks": 0,
            })
            continue

        parsed_files.append({
            "file_path": file_path,
            "tree": tree,
        })

        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
        ]

        complexities = []
        function_lengths = []

        for function in functions:
            complexity = calculate_complexity(function)
            lines = get_function_line_count(function)

            complexities.append(complexity)
            function_lengths.append(lines)

            total_complexity += complexity
            total_functions += 1

            if complexity > MAX_COMPLEXITY:
                issues.append({
                    "rule_id": "CQ001",
                    "message": (
                        f"Function '{function.name}' has cyclomatic "
                        f"complexity {complexity}."
                    ),
                    "file_path": file_path,
                    "line": function.lineno,
                    "column": function.col_offset,
                })

            if lines > MAX_FUNCTION_LINES:
                issues.append({
                    "rule_id": "CQ002",
                    "message": (
                        f"Function '{function.name}' contains "
                        f"{lines} lines."
                    ),
                    "file_path": file_path,
                    "line": function.lineno,
                    "column": function.col_offset,
                })

        average_complexity = (
            sum(complexities) / len(complexities)
            if complexities else 0
        )

        max_complexity = max(complexities, default=0)
        max_function_lines = max(function_lengths, default=0)

        file_line_count = len(source_code.splitlines())

        # A transparent heuristic, not a standard MI implementation.
        complexity_penalty = min(40, average_complexity * 3)
        size_penalty = min(30, file_line_count / 20)
        long_function_penalty = min(
            20,
            sum(1 for lines in function_lengths if lines > MAX_FUNCTION_LINES) * 5,
        )

        maintainability_index = round(
            max(
                0,
                min(
                    100,
                    100
                    - complexity_penalty
                    - size_penalty
                    - long_function_penalty,
                ),
            ),
            2,
        )

        file_reports.append({
            "file_path": file_path,
            "status": "analyzed",
            "function_count": len(functions),
            "average_complexity": round(average_complexity, 2),
            "max_complexity": max_complexity,
            "max_function_lines": max_function_lines,
            "maintainability_index": maintainability_index,
            "duplicate_blocks": 0,
        })

    duplicates = find_duplicate_blocks(parsed_files)
    total_duplicate_blocks = len(duplicates)

    for duplicate in duplicates:
        for occurrence in duplicate["occurrences"]:
            issues.append({
                "rule_id": "CQ003",
                "message": (
                    "Potential duplicated code block detected. "
                    "Consider extracting reusable functionality."
                ),
                "file_path": occurrence["file_path"],
                "line": occurrence["line"],
                "column": 0,
            })

            for report in file_reports:
                if report["file_path"] == occurrence["file_path"]:
                    report["duplicate_blocks"] += 1

    valid_indexes = [
        report["maintainability_index"]
        for report in file_reports
        if report["maintainability_index"] is not None
    ]

    average_maintainability = (
        round(sum(valid_indexes) / len(valid_indexes), 2)
        if valid_indexes else 100.0
    )

    average_complexity = (
        round(total_complexity / total_functions, 2)
        if total_functions else 0
    )

    debt_penalty = (
        sum(15 if issue["rule_id"] == "CQ001" else
            7 if issue["rule_id"] == "CQ002" else 5
            for issue in issues)
    )

    technical_debt_score = max(0, 100 - debt_penalty)

    return {
        "average_maintainability_index": average_maintainability,
        "average_cyclomatic_complexity": average_complexity,
        "total_functions": total_functions,
        "total_duplicate_blocks": total_duplicate_blocks,
        "technical_debt_score": technical_debt_score,
        "files": file_reports,
        "duplicate_blocks": duplicates,
        "issues": issues,
    }