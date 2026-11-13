import ast
import re
from pathlib import Path

from app.core.config import settings
from app.services import upload_service
from app.services.issue_classifier import classify_issues
from app.services.ruff_analyzer import (
    RuffAnalysisError,
    analyze_with_ruff,
)
from app.services.security_analyzer import analyze_security
from app.services.technical_debt_analyzer import (
    analyze_technical_debt,
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

    if not upload_directory.exists():
        raise AnalysisError(
            404,
            "UPLOAD_NOT_FOUND",
            "The uploaded project could not be found.",
        )

    # Single Python file upload.
    single_file = upload_directory / "source.py"

    if single_file.is_file():
        return [
            (single_file, "source.py")
        ]

    # ZIP project upload.
    project_directory = (
        upload_directory / "project"
    ).resolve()

    if not project_directory.is_relative_to(upload_directory):
        raise AnalysisError(
            400,
            "INVALID_PROJECT_PATH",
            "Invalid project directory.",
        )

    if not project_directory.exists():
        raise AnalysisError(
            404,
            "PROJECT_NOT_FOUND",
            "The uploaded project directory could not be found.",
        )

    python_files = []

    ignored_directories = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        ".idea",
        ".vscode",
    }

    try:
        for file_path in project_directory.rglob("*.py"):

            if any(
                part in ignored_directories
                for part in file_path.parts
            ):
                continue

            resolved_file = file_path.resolve()

            if not resolved_file.is_relative_to(project_directory):
                continue

            if not resolved_file.is_file():
                continue

            relative_path = resolved_file.relative_to(
                project_directory
            ).as_posix()

            python_files.append((
                resolved_file,
                relative_path,
            ))

    except OSError as exc:
        raise AnalysisError(
            500,
            "FILE_DISCOVERY_FAILED",
            "Could not discover project Python files.",
        ) from exc

    python_files.sort(
        key=lambda item: item[1]
    )

    max_files = settings.MAX_FILES_PER_PROJECT

    if len(python_files) > max_files:
        raise AnalysisError(
            413,
            "TOO_MANY_FILES",
            "Project exceeds the maximum file count.",
        )

    return python_files


def analyze_python_file(
    file_path: Path,
    relative_path: str,
):
    """
    Analyze one Python file using AST.

    Uploaded source code is parsed but never executed.
    """

    try:
        file_size = file_path.stat().st_size

    except OSError as exc:
        raise AnalysisError(
            500,
            "FILE_ACCESS_FAILED",
            f"Could not access {relative_path}.",
        ) from exc

    max_file_size = 5 * 1024 * 1024

    if file_size > max_file_size:
        raise AnalysisError(
            413,
            "FILE_TOO_LARGE",
            f"File {relative_path} exceeds the analysis size limit.",
        )

    try:
        source_code = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except OSError as exc:
        raise AnalysisError(
            500,
            "FILE_READ_FAILED",
            f"Could not read {relative_path}.",
        ) from exc

    lines_of_code = len(
        source_code.splitlines()
    )

    try:
        syntax_tree = ast.parse(
            source_code,
            filename=relative_path,
        )

    except SyntaxError as exc:

        issue = {
            "rule_id": "PY001",
            "severity": "high",
            "message": (
                f"Python syntax error: {exc.msg}"
            ),
            "file_path": relative_path,
            "line": exc.lineno or 1,
            "column": exc.offset or 0,
            "suggestion": (
                "Correct the Python syntax before running the program."
            ),
        }

        return {
            "file_path": relative_path,
            "status": "syntax_error",
            "lines_of_code": lines_of_code,
            "issue_count": 1,
            "issues": [issue],
            "source_code": source_code,
        }

    analyzer = PythonCodeAnalyzer(
        relative_path
    )

    analyzer.visit(syntax_tree)

    return {
        "file_path": relative_path,
        "status": "parsed",
        "lines_of_code": lines_of_code,
        "issue_count": len(analyzer.issues),
        "issues": analyzer.issues,
        "source_code": source_code,
    }


def analyze_project(upload_id: str):
    """
    Analyze uploaded Python files using:

    1. Python AST analysis
    2. Ruff static analysis
    3. Security analysis
    4. Technical debt analysis
    5. Centralized issue classification

    Uploaded source code is never executed.
    """

    python_files = discover_python_files(
        upload_id
    )

    if not python_files:
        raise AnalysisError(
            400,
            "NO_PYTHON_FILES",
            "No Python files were found for analysis.",
        )

    file_results = []
    all_issues = []
    technical_debt_files = []

    # --------------------------------------------------
    # STEP 1: Analyze each Python file
    # --------------------------------------------------

    for file_path, relative_path in python_files:

        result = analyze_python_file(
            file_path,
            relative_path,
        )

        combined_issues = list(
            result["issues"]
        )

        # --------------------------------------------------
        # STEP 2: Collect source for technical debt analysis
        # --------------------------------------------------

        if result["status"] == "parsed":

            technical_debt_files.append({
                "file_path": relative_path,
                "source_code": result["source_code"],
            })

        # --------------------------------------------------
        # STEP 3: Ruff static analysis
        # --------------------------------------------------

        if result["status"] == "parsed":

            try:
                ruff_issues = analyze_with_ruff(
                    file_path,
                    relative_path,
                )

                combined_issues.extend(
                    ruff_issues
                )

            except RuffAnalysisError as exc:
                raise AnalysisError(
                    503,
                    "RUFF_ANALYSIS_FAILED",
                    str(exc),
                ) from exc

        # --------------------------------------------------
        # STEP 4: Security analysis
        # --------------------------------------------------

        if result["status"] == "parsed":

            try:
                security_issues = analyze_security(
                    result["source_code"],
                    relative_path,
                )

                combined_issues.extend(
                    security_issues
                )

            except Exception as exc:
                raise AnalysisError(
                    500,
                    "SECURITY_ANALYSIS_FAILED",
                    "Security analysis could not be completed.",
                ) from exc

        # --------------------------------------------------
        # STEP 5: Save file-level findings
        # --------------------------------------------------

        file_results.append({
            "file_path": relative_path,
            "status": result["status"],
            "lines_of_code": result["lines_of_code"],
        })

        all_issues.extend(
            combined_issues
        )

    # --------------------------------------------------
    # STEP 6: Technical debt analysis
    # --------------------------------------------------

    try:
        technical_debt = analyze_technical_debt(
            technical_debt_files
        )

    except Exception as exc:
        raise AnalysisError(
            500,
            "TECHNICAL_DEBT_ANALYSIS_FAILED",
            "Technical debt analysis could not be completed.",
        ) from exc

    all_issues.extend(
        technical_debt["issues"]
    )

    # --------------------------------------------------
    # STEP 7: Centralized classification and deduplication
    # --------------------------------------------------

    classification = classify_issues(
        all_issues
    )

    classified_issues = classification[
        "issues"
    ]

    # --------------------------------------------------
    # STEP 8: Recalculate file-level issue counts
    # --------------------------------------------------

    for file_result in file_results:

        file_result["issue_count"] = sum(
            1
            for issue in classified_issues
            if issue["file_path"] == file_result["file_path"]
        )

    # --------------------------------------------------
    # STEP 9: Final analysis response
    # --------------------------------------------------

    return {
        "success": True,
        "upload_id": upload_id,

        "total_files": len(python_files),
        "analyzed_files": len(file_results),

        "total_issues": classification["total_issues"],

        "severity_counts": classification["severity_counts"],
        "category_counts": classification["category_counts"],

        "quality_score": classification["quality_score"],

        "files": file_results,
        "issues": classified_issues,

        "technical_debt": {
            key: value
            for key, value in technical_debt.items()
            if key != "issues"
        },
    }