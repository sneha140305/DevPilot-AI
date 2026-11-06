import logging

from fastapi import APIRouter, HTTPException

from app.repositories.analysis_repository import (
    get_latest_analysis,
    list_analyses,
    save_analysis,
)
from app.schemas.analysis import AnalysisResponse
from app.services.ast_analyzer import AnalysisError, analyze_project

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze/{upload_id}",
    response_model=AnalysisResponse,
)
async def analyze_uploaded_project(upload_id: str):
    try:
        result = analyze_project(upload_id)

        save_analysis(
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
            "Failed to persist analysis result for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_PERSISTENCE_ERROR",
                "message": (
                    "Analysis completed, but its result "
                    "could not be saved."
                ),
            },
        ) from exc


@router.get("/analysis/{upload_id}/history")
async def get_analysis_history(upload_id: str):
    try:
        return {
            "success": True,
            "upload_id": upload_id,
            "analyses": list_analyses(upload_id),
        }

    except Exception as exc:
        logger.exception(
            "Failed to retrieve analysis history for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_HISTORY_ERROR",
                "message": "Could not retrieve analysis history.",
            },
        ) from exc


@router.get("/analysis/{upload_id}/latest")
async def get_latest_saved_analysis(upload_id: str):
    try:
        result = get_latest_analysis(upload_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ANALYSIS_NOT_FOUND",
                    "message": (
                        "No saved analysis was found for this project."
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
            "Failed to retrieve latest analysis for upload_id=%s",
            upload_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_RETRIEVAL_ERROR",
                "message": "Could not retrieve the saved analysis.",
            },
        ) from exc