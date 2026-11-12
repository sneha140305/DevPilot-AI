import logging

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.repositories.review_repository import (
    get_latest_review,
    list_reviews,
    save_review,
)
from app.schemas.review import CodeReviewResponse
from app.services.ast_analyzer import (
    AnalysisError,
    analyze_project,
    discover_python_files,
)
from app.services.code_reviewer import review_issues

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/review",
    tags=["Code Review"],
)


def load_review_source_files(upload_id: str) -> dict[str, str]:
    """
    Safely load uploaded Python source files for contextual review.

    Files are read as text only. Uploaded code is never executed.
    """

    source_files = {}

    max_file_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    discovered_files = discover_python_files(upload_id)

    for file_path, relative_path in discovered_files:
        try:
            if file_path.stat().st_size > max_file_size:
                logger.warning(
                    "Skipping oversized review context: %s",
                    relative_path,
                )
                continue

            source_code = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            source_files[relative_path] = source_code

        except OSError:
            logger.warning(
                "Could not load source context for %s",
                relative_path,
                exc_info=True,
            )

    return source_files


@router.post(
    "/{upload_id}",
    response_model=CodeReviewResponse,
)
def review_project(upload_id: str):
    """
    Analyze an uploaded project, generate contextual code reviews,
    and persist the review in SQLite.
    """

    try:
        # Step 1: Perform existing static analysis.
        analysis = analyze_project(upload_id)

        # Step 2: Load source files for contextual debugging.
        source_files = load_review_source_files(upload_id)

        # Step 3: Generate enhanced code reviews.
        reviewed_issues = review_issues(
            issues=analysis["issues"],
            source_files=source_files,
        )

        # Step 4: Prepare the API response.
        result = {
            "upload_id": upload_id,
            "total_issues": len(reviewed_issues),
            "review_provider": "rule_based",
            "reviews": reviewed_issues,
        }

        # Step 5: Persist the enhanced review.
        save_review(
            upload_id=upload_id,
            result=result,
        )

        return result

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
            "Failed to generate or save review for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "REVIEW_PERSISTENCE_ERROR",
                "message": (
                    "Code review completed or attempted, "
                    "but its result could not be saved."
                ),
            },
        ) from exc


@router.get("/{upload_id}/history")
def get_review_history(upload_id: str):
    """
    Retrieve all saved code reviews for a project.
    """

    try:
        return {
            "success": True,
            "upload_id": upload_id,
            "reviews": list_reviews(upload_id),
        }

    except Exception as exc:
        logger.exception(
            "Failed to retrieve review history for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "REVIEW_HISTORY_ERROR",
                "message": "Could not retrieve review history.",
            },
        ) from exc


@router.get("/{upload_id}/latest")
def get_latest_saved_review(upload_id: str):
    """
    Retrieve the latest saved code review for a project.
    """

    try:
        result = get_latest_review(upload_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "REVIEW_NOT_FOUND",
                    "message": (
                        "No saved review was found for this project."
                    ),
                },
            )

        return {
            "success": True,
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to retrieve latest review for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "REVIEW_RETRIEVAL_ERROR",
                "message": "Could not retrieve the saved review.",
            },
        ) from exc
