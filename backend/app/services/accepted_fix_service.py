import hashlib
import uuid

from app.core.config import PROJECT_ROOT
from app.repositories.accepted_fix_repository import save_accepted_fix
from app.services.ast_analyzer import AnalysisError, discover_python_files
from app.services.fix_generator import (
    SUPPORTED_RULES,
    generate_fix,
    validate_python_source,
)

ACCEPTED_FIX_ROOT = PROJECT_ROOT / "data" / "accepted_fixes"


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def accept_proposed_fix(
    upload_id: str,
    file_path: str,
    rule_id: str,
    line: int,
) -> dict:
    """
    Regenerate, validate and save an accepted fix separately.

    The original uploaded source is never modified.
    Uploaded code is never executed.
    """

    if rule_id not in SUPPORTED_RULES:
        raise ValueError(
            f"Automatic fixes are not supported for rule {rule_id}."
        )

    # Locate the original uploaded file.
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

    # Resolve and validate the original source location.
    original_path = matching_file.resolve()
    upload_root = (PROJECT_ROOT / "data" / "uploads" / upload_id).resolve()

    if not original_path.is_relative_to(upload_root):
        raise ValueError("Invalid source file location.")

    original_bytes = original_path.read_bytes()

    try:
        original_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Source file must contain valid UTF-8.") from exc

    original_hash = calculate_sha256(original_bytes)

    # Regenerate the fix instead of trusting frontend-submitted code.
    proposed = generate_fix(
        upload_id=upload_id,
        file_path=file_path,
        rule_id=rule_id,
        line=line,
    )

    if not proposed["success"] or not proposed["supported"]:
        raise ValueError(proposed["message"])

    proposed_code = proposed["proposed_code"]

    if not isinstance(proposed_code, str):
        raise TypeError("No proposed code was generated.")

    validation = validate_python_source(proposed_code)

    if not validation["valid"]:
        raise ValueError(
            f"Proposed fix failed validation: {validation['message']}"
        )

    # Ensure source has not changed during fix generation.
    current_bytes = original_path.read_bytes()

    if calculate_sha256(current_bytes) != original_hash:
        raise ValueError(
            "Original source changed during fix generation. "
            "Please generate the proposal again."
        )

    # Generate unique identifiers.
    fix_id = uuid.uuid4().hex

    accepted_directory = ACCEPTED_FIX_ROOT / upload_id / fix_id
    accepted_directory.mkdir(parents=True, exist_ok=False)

    accepted_path = accepted_directory / "accepted.py"

    accepted_bytes = proposed_code.encode("utf-8")
    accepted_hash = calculate_sha256(accepted_bytes)

    try:
        # Save separately using exclusive file creation.
        with accepted_path.open("xb") as accepted_file:
            accepted_file.write(accepted_bytes)

        # Verify saved content.
        saved_bytes = accepted_path.read_bytes()

        if calculate_sha256(saved_bytes) != accepted_hash:
            raise OSError("Accepted file verification failed.")

        # Ensure the original file is still unchanged.
        if calculate_sha256(original_path.read_bytes()) != original_hash:
            raise ValueError(
                "Original source changed during acceptance."
            )

        # Persist acceptance metadata.
        record = save_accepted_fix(
            fix_id=fix_id,
            upload_id=upload_id,
            file_path=file_path,
            rule_id=rule_id,
            line=line,
            accepted_path=str(
                accepted_path.relative_to(PROJECT_ROOT)
            ),
            original_sha256=original_hash,
            accepted_sha256=accepted_hash,
        )

        if record is None:
            raise RuntimeError("Could not save accepted fix metadata.")

        return {
            "success": True,
            "fix_id": fix_id,
            "upload_id": upload_id,
            "file_path": file_path,
            "rule_id": rule_id,
            "line": line,
            "accepted_path": str(
                accepted_path.relative_to(PROJECT_ROOT)
            ),
            "original_sha256": original_hash,
            "accepted_sha256": accepted_hash,
            "validation_passed": True,
            "message": "Proposed fix accepted and saved successfully.",
            "created_at": record["created_at"],
        }

    except Exception:
        # Avoid leaving an untracked accepted file after failure.
        if accepted_path.exists():
            accepted_path.unlink()

        raise