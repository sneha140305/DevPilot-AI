import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import PROJECT_ROOT
from app.repositories.accepted_fix_repository import (
    get_accepted_fix,
    list_accepted_fixes,
)
from app.schemas.fixes import FixRequest, FixResponse
from app.services.accepted_fix_service import accept_proposed_fix
from app.services.ast_analyzer import (
    AnalysisError,
    analyze_project,
    discover_python_files,
)
from app.services.fix_generator import generate_fix
from app.schemas.refactoring import (
    RefactoringRequest,
    RefactoringResponse,
)

from app.services.refactoring_advisor import (
    RefactoringError,
    build_refactoring_recommendation,
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fix",
    tags=["Proposed Fixes"],
)


class AcceptFixRequest(BaseModel):
    """Request schema for accepting a proposed fix."""

    file_path: str = Field(min_length=1, max_length=500)
    rule_id: str = Field(min_length=1, max_length=50)
    line: int = Field(ge=1)


def validate_upload_id(upload_id: str) -> None:
    """Validate upload ID format."""

    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_UPLOAD_ID",
                "message": "Invalid upload ID.",
            },
        )


def validate_fix_id(fix_id: str) -> None:
    """Validate accepted fix ID format."""

    if not re.fullmatch(r"[a-f0-9]{32}", fix_id):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FIX_ID",
                "message": "Invalid fix ID.",
            },
        )


@router.post(
    "/{upload_id}",
    response_model=FixResponse,
)
def generate_project_fix(
    upload_id: str,
    request: FixRequest,
):
    """
    Generate and validate a proposed code fix.

    The original uploaded source file is never modified.
    Uploaded code is never executed.
    """

    try:
        validate_upload_id(upload_id)

        analysis = analyze_project(upload_id)

        matching_issue = next(
            (
                issue
                for issue in analysis["issues"]
                if issue["file_path"] == request.file_path
                and issue["rule_id"] == request.rule_id
                and issue["line"] == request.line
            ),
            None,
        )

        if matching_issue is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ISSUE_NOT_FOUND",
                    "message": (
                        "The requested issue was not found "
                        "in the uploaded project."
                    ),
                },
            )

        result = generate_fix(
            upload_id=upload_id,
            file_path=request.file_path,
            rule_id=request.rule_id,
            line=request.line,
        )

        return {
            "success": result["success"],
            "upload_id": upload_id,
            "file_path": request.file_path,
            "rule_id": request.rule_id,
            "line": request.line,
            "supported": result["supported"],
            "message": result["message"],
            "original_code": result.get("original_code"),
            "proposed_code": result.get("proposed_code"),
            "diff": result.get("diff"),
            "validation_passed": result.get("validation_passed"),
            "validation_message": result.get("validation_message"),
        }

    except HTTPException:
        raise

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FIX_REQUEST",
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to generate proposed fix for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "FIX_GENERATION_ERROR",
                "message": "Could not generate the proposed fix.",
            },
        ) from exc


@router.post("/{upload_id}/accept")
def accept_fix_endpoint(
    upload_id: str,
    request: AcceptFixRequest,
):
    """
    Accept a proposed fix and save it separately.

    The backend regenerates and validates the fix.
    The original uploaded source is never overwritten.
    """

    try:
        validate_upload_id(upload_id)

        result = accept_proposed_fix(
            upload_id=upload_id,
            file_path=request.file_path,
            rule_id=request.rule_id,
            line=request.line,
        )

        return result

    except HTTPException:
        raise

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FIX_ACCEPTANCE_ERROR",
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to accept fix for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "FIX_ACCEPTANCE_ERROR",
                "message": "Could not accept the proposed fix.",
            },
        ) from exc


@router.get("/{upload_id}/accepted")
def get_accepted_fixes_endpoint(
    upload_id: str,
):
    """Return the accepted-fix history for a project."""

    try:
        validate_upload_id(upload_id)

        # Confirm that the uploaded project exists.
        discover_python_files(upload_id)

        records = list_accepted_fixes(upload_id)

        return {
            "success": True,
            "total": len(records),
            "accepted_fixes": records,
        }

    except HTTPException:
        raise

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to retrieve accepted fixes for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "ACCEPTED_FIX_HISTORY_ERROR",
                "message": "Could not retrieve accepted fixes.",
            },
        ) from exc


@router.get("/{upload_id}/accepted/{fix_id}")
def get_accepted_fix_endpoint(
    upload_id: str,
    fix_id: str,
):
    """Retrieve an accepted fix and its saved source code."""

    try:
        validate_upload_id(upload_id)
        validate_fix_id(fix_id)

        record = get_accepted_fix(fix_id)

        if record is None or record["upload_id"] != upload_id:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ACCEPTED_FIX_NOT_FOUND",
                    "message": "Accepted fix was not found.",
                },
            )

        accepted_path = (
            PROJECT_ROOT / record["accepted_path"]
        ).resolve()

        accepted_root = (
            PROJECT_ROOT / "data" / "accepted_fixes" / upload_id
        ).resolve()

        if not accepted_path.is_relative_to(accepted_root):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_ACCEPTED_FILE_PATH",
                    "message": "Invalid accepted file location.",
                },
            )

        if not accepted_path.is_file():
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ACCEPTED_FILE_NOT_FOUND",
                    "message": "Accepted file is missing.",
                },
            )

        content = accepted_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "fix": record,
            "accepted_code": content,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to retrieve accepted fix: upload_id=%s fix_id=%s",
            upload_id,
            fix_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "ACCEPTED_FIX_RETRIEVAL_ERROR",
                "message": "Could not retrieve the accepted fix.",
            },
        ) from exc

@router.post(
    "/{upload_id}/refactor",
    response_model=RefactoringResponse,
)
def generate_refactoring_recommendation(
    upload_id: str,
    request: RefactoringRequest,
):
    """
    Generate a safe refactoring recommendation.

    This endpoint never modifies or executes uploaded source.
    """

    try:
        validate_upload_id(upload_id)

        if request.rule_id not in {
            "CQ001",
            "CQ002",
            "CQ003",
        }:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "UNSUPPORTED_REFACTORING_RULE",
                    "message": (
                        "Refactoring recommendations are "
                        "not supported for this rule."
                    ),
                },
            )

        analysis = analyze_project(upload_id)

        matching_issue = next(
            (
                issue
                for issue in analysis["issues"]
                if issue["file_path"] == request.file_path
                and issue["rule_id"] == request.rule_id
                and issue["line"] == request.line
            ),
            None,
        )

        if matching_issue is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ISSUE_NOT_FOUND",
                    "message": (
                        "The requested issue was not found."
                    ),
                },
            )

        python_files = discover_python_files(upload_id)

        matching_file = next(
            (
                path
                for path, relative_path in python_files
                if relative_path == request.file_path
            ),
            None,
        )

        if matching_file is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "SOURCE_FILE_NOT_FOUND",
                    "message": "Source file was not found.",
                },
            )

        source_code = matching_file.read_text(
            encoding="utf-8",
            errors="replace",
        )

        recommendation = build_refactoring_recommendation(
            matching_issue,
            source_code,
        )

        return {
            "success": True,
            "upload_id": upload_id,
            "recommendation": recommendation,
        }

    except HTTPException:
        raise

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except RefactoringError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "REFACTORING_ERROR",
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        logger.exception(
            "Refactoring recommendation failed for %s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "REFACTORING_ERROR",
                "message": "Could not generate recommendation.",
            },
        ) from exc