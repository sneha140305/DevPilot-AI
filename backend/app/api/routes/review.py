import logging

from fastapi import APIRouter, HTTPException

from app.repositories.review_repository import (
    get_latest_review,
    list_reviews,
    save_review,
)
from app.schemas.review import CodeReviewResponse
from app.services.ast_analyzer import (
    AnalysisError,
    analyze_project,
)
from app.services.code_reviewer import review_issues

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/review",
    tags=["Code Review"],
)


@router.post(
    "/{upload_id}",
    response_model=CodeReviewResponse,
)
def review_project(upload_id: str):
    """
    Analyze an uploaded project, generate code review
    suggestions, and persist the review in SQLite.
    """

    try:
        analysis = analyze_project(upload_id)

        reviewed_issues = review_issues(
            analysis["issues"]
        )

        result = {
            "upload_id": upload_id,
            "total_issues": len(reviewed_issues),
            "review_provider": "rule_based",
            "reviews": reviewed_issues,
        }

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