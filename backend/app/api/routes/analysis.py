from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisResponse
from app.services.ast_analyzer import (
    AnalysisError,
    analyze_project,
)

router = APIRouter()


@router.post(
    "/analyze/{upload_id}",
    response_model=AnalysisResponse,
)
async def analyze_uploaded_project(upload_id: str):
    """
    Analyze an uploaded Python project using AST.
    """

    try:
        result = analyze_project(upload_id)

        return result

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc