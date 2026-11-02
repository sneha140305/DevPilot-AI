import ast
import re
from pathlib import Path

from app.core.config import settings
from app.services import upload_service
from app.services.ruff_analyzer import (
    RuffAnalysisError,
    analyze_with_ruff,
)


class AnalysisError(Exception):
    """Raised when project analysis cannot be performed."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message

        super().__init__(message)


class PythonCodeAnalyzer(ast.NodeVisitor):
    """
    Analyze Python AST nodes and identify potential issues.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []

    def add_issue(
        self,
        rule_id: str,
        severity: str,
        message: str,
        node: ast.AST,
        suggestion: str,
    ):
        self.issues.append({
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "file_path": self.filename,
            "line": getattr(node, "lineno", 1),
            "column": getattr(node, "col_offset", 0),
            "suggestion": suggestion,
        })

    def visit_Call(self, node: ast.Call):
        """Detect potentially dangerous built-in calls."""

        if isinstance(node.func, ast.Name):

            if node.func.id == "eval":
                self.add_issue(
                    "PY002",
                    "high",
                    "Use of eval() detected.",
                    node,
                    "Avoid eval(). Consider safer alternatives.",
                )

            elif node.func.id == "exec":
                self.add_issue(
                    "PY003",
                    "high",
                    "Use of exec() detected.",
                    node,
                    "Avoid executing dynamically generated code.",
                )

        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Detect bare except blocks."""

        if node.type is None:
            self.add_issue(
                "PY004",
                "medium",
                "Bare except block detected.",
                node,
                "Catch specific exceptions instead of using bare except.",
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Detect wildcard imports."""

        for alias in node.names:

            if alias.name == "*":
                self.add_issue(
                    "PY005",
                    "medium",
                    "Wildcard import detected.",
                    node,
                    "Import only the specific names you need.",
                )

        self.generic_visit(node)


def discover_python_files(upload_id: str):
    """
    Locate Python files belonging to an existing upload.

    The client can supply only a generated upload ID,
    never an arbitrary filesystem path.
    """

    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise AnalysisError(
            400,
            "INVALID_UPLOAD_ID",
            "The upload ID is invalid.",
        )

    upload_root = upload_service.UPLOAD_ROOT.resolve()

    upload_directory = (
        upload_root / upload_id
    ).resolve()

    if not upload_directory.is_relative_to(upload_root):
        raise AnalysisError(
            400,
            "INVALID_UPLOAD_PATH",
            "Invalid upload directory.",
        )

    if not upload_directory.is_dir():
        raise AnalysisError(
            404,
            "UPLOAD_NOT_FOUND",
            "The requested upload was not found.",
        )

    # Individual Python file upload.
    single_file = upload_directory / "source.py"

    if single_file.is_file():
        return [(single_file, "source.py")]

    # ZIP project upload.
    project_directory = upload_directory / "project"

    if project_directory.is_dir():

        python_files = []

        for file_path in project_directory.rglob("*.py"):

            if file_path.is_file():
                relative_path = file_path.relative_to(
                    project_directory
                ).as_posix()

                python_files.append(
                    (file_path, relative_path)
                )

                if len(python_files) > settings.MAX_FILES_PER_PROJECT:
                    raise AnalysisError(
                        413,
                        "TOO_MANY_FILES",
                        "Project contains too many Python files.",
                    )

        return sorted(
            python_files,
            key=lambda item: item[1],
        )

    raise AnalysisError(
        404,
        "PROJECT_NOT_FOUND",
        "No Python project was found for this upload.",
    )


def analyze_python_file(
    file_path: Path,
    relative_path: str,
):
    """
    Parse and analyze a single Python file.
    """

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    file_size = file_path.stat().st_size

    if file_size > max_size:
        raise AnalysisError(
            413,
            "SOURCE_FILE_TOO_LARGE",
            f"{relative_path} exceeds the analysis size limit.",
        )

    source_code = file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines_of_code = len(source_code.splitlines())

    try:
        syntax_tree = ast.parse(
            source_code,
            filename=relative_path,
        )

    except SyntaxError as exc:

        issue = {
            "rule_id": "PY001",
            "severity": "high",
            "message": f"Syntax error: {exc.msg}",
            "file_path": relative_path,
            "line": exc.lineno or 1,
            "column": max((exc.offset or 1) - 1, 0),
            "suggestion": "Correct the Python syntax and analyze again.",
        }

        return {
            "file_path": relative_path,
            "status": "syntax_error",
            "lines_of_code": lines_of_code,
            "issue_count": 1,
            "issues": [issue],
        }

    analyzer = PythonCodeAnalyzer(relative_path)

    analyzer.visit(syntax_tree)

    return {
        "file_path": relative_path,
        "status": "parsed",
        "lines_of_code": lines_of_code,
        "issue_count": len(analyzer.issues),
        "issues": analyzer.issues,
    }


def analyze_project(upload_id: str):
    """
    Analyze all Python files using AST and Ruff.
    """

    python_files = discover_python_files(upload_id)

    if not python_files:
        raise AnalysisError(
            400,
            "NO_PYTHON_FILES",
            "No Python files were found for analysis.",
        )

    file_results = []
    all_issues = []

    for file_path, relative_path in python_files:

        # First: AST analysis
        result = analyze_python_file(
            file_path,
            relative_path,
        )

        combined_issues = list(result["issues"])

        # Second: Ruff analysis
        # Skip Ruff if AST already detected invalid syntax.
        if result["status"] == "parsed":

            try:
                ruff_issues = analyze_with_ruff(
                    file_path,
                    relative_path,
                )

                combined_issues.extend(ruff_issues)

            except RuffAnalysisError as exc:
                raise AnalysisError(
                    503,
                    "RUFF_ANALYSIS_FAILED",
                    str(exc),
                ) from exc

        file_results.append({
            "file_path": result["file_path"],
            "status": result["status"],
            "lines_of_code": result["lines_of_code"],
            "issue_count": len(combined_issues),
        })

        all_issues.extend(combined_issues)

    severity_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for issue in all_issues:
        severity_counts[issue["severity"]] += 1

    return {
        "success": True,
        "upload_id": upload_id,
        "total_files": len(python_files),
        "analyzed_files": len(file_results),
        "total_issues": len(all_issues),
        "severity_counts": severity_counts,
        "files": file_results,
        "issues": all_issues,
    }