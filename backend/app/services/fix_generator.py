import ast
import difflib
import re

from app.services.ast_analyzer import (
    AnalysisError,
    discover_python_files,
)

SUPPORTED_RULES = {"PY004", "RUFF-E722"}


def validate_python_source(source_code: str) -> dict:
    """Validate Python source code without executing it."""
    try:
        ast.parse(source_code)
        return {
            "valid": True,
            "message": "Proposed code passed Python AST syntax validation.",
        }
    except SyntaxError as exc:
        return {
            "valid": False,
            "message": (
                f"Syntax error at line {exc.lineno}, "
                f"column {exc.offset}: {exc.msg}"
            ),
        }


def generate_fix(
    upload_id: str,
    file_path: str,
    rule_id: str,
    line: int,
) -> dict:
    """Generate and validate a proposed fix without modifying source files."""

    if rule_id not in SUPPORTED_RULES:
        return {
            "success": False,
            "supported": False,
            "message": (
                f"Automatic fixes are not yet supported for rule {rule_id}."
            ),
            "original_code": None,
            "proposed_code": None,
            "diff": None,
            "validation_passed": None,
            "validation_message": None,
        }

    if line < 1:
        raise ValueError("Line number must be greater than zero.")

    python_files = discover_python_files(upload_id)

    matching_file = next(
        (
            path
            for path, relative_path in python_files
            if relative_path == file_path
        ),
        None,
    )

    if matching_file is None:
        raise AnalysisError(
            404,
            "SOURCE_FILE_NOT_FOUND",
            "The requested Python file was not found.",
        )

    source = matching_file.read_text(
        encoding="utf-8",
        errors="replace",
    )

    source_lines = source.splitlines(keepends=True)

    if line > len(source_lines):
        raise ValueError("The requested line does not exist.")

    original_line = source_lines[line - 1]

    pattern = re.compile(r"^(\s*)except\s*:(\s*(?:#.*)?)$")
    match = pattern.match(original_line.rstrip("\r\n"))

    if match is None:
        return {
            "success": False,
            "supported": False,
            "message": "The selected line does not contain a supported bare except statement.",
            "original_code": source,
            "proposed_code": None,
            "diff": None,
            "validation_passed": None,
            "validation_message": None,
        }

    indentation, trailing_content = match.groups()

    if original_line.endswith("\r\n"):
        newline = "\r\n"
    elif original_line.endswith("\n"):
        newline = "\n"
    else:
        newline = ""

    proposed_line = (
        f"{indentation}except Exception:{trailing_content}{newline}"
    )

    proposed_lines = source_lines.copy()
    proposed_lines[line - 1] = proposed_line

    proposed_source = "".join(proposed_lines)

    validation = validate_python_source(proposed_source)

    if not validation["valid"]:
        return {
            "success": False,
            "supported": True,
            "message": "The proposed fix failed syntax validation.",
            "original_code": source,
            "proposed_code": proposed_source,
            "diff": None,
            "validation_passed": False,
            "validation_message": validation["message"],
        }

    diff = "".join(
        difflib.unified_diff(
            source.splitlines(keepends=True),
            proposed_source.splitlines(keepends=True),
            fromfile=f"original/{file_path}",
            tofile=f"proposed/{file_path}",
        )
    )

    return {
        "success": True,
        "supported": True,
        "message": "A proposed fix was generated and validated successfully.",
        "original_code": source,
        "proposed_code": proposed_source,
        "diff": diff,
        "validation_passed": True,
        "validation_message": validation["message"],
    }