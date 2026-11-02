import json
import subprocess
import sys
from pathlib import Path


class RuffAnalysisError(Exception):
    """Raised when Ruff analysis cannot be completed."""


SEVERITY_MAP = {
    "F821": "high",
    "E999": "high",
    "F401": "medium",
    "F841": "medium",
    "F811": "medium",
    "E722": "medium",
}


def get_severity(rule_code: str) -> str:
    """Map Ruff rule codes to DevPilot severity levels."""

    return SEVERITY_MAP.get(rule_code, "low")


def analyze_with_ruff(
    file_path: Path,
    relative_path: str,
) -> list[dict]:
    """
    Analyze a Python file using Ruff.

    The file is analyzed without modifying or executing it.
    """

    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--output-format",
        "json",
        "--no-fix",
        "--isolated",
        "--select",
        "E4,E7,E9,F",
        "--select",
        "E501",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:
        raise RuffAnalysisError(
            "Ruff analysis timed out."
        ) from exc

    except OSError as exc:
        raise RuffAnalysisError(
            "Unable to start Ruff."
        ) from exc

    # Ruff returns:
    # 0 = no violations
    # 1 = lint violations found
    # 2 = abnormal execution

    if result.returncode not in (0, 1):
        raise RuffAnalysisError(
            "Ruff could not analyze the Python file."
        )

    try:
        diagnostics = json.loads(result.stdout)

    except json.JSONDecodeError as exc:
        raise RuffAnalysisError(
            "Ruff returned an invalid JSON response."
        ) from exc

    issues = []

    for diagnostic in diagnostics:

        rule_code = diagnostic.get("code") or "UNKNOWN"

        location = diagnostic.get("location") or {}

        issues.append({
            "rule_id": f"RUFF-{rule_code}",
            "severity": get_severity(rule_code),
            "message": diagnostic.get(
                "message",
                "Code quality issue detected.",
            ),
            "file_path": relative_path,
            "line": location.get("row", 1),
            "column": max(location.get("column", 1) - 1, 0),
            "suggestion": (
                f"Review Ruff rule {rule_code} "
                "and update the code accordingly."
            ),
        })

    return issues