from fastapi import APIRouter, HTTPException

from app.schemas.review import CodeReviewResponse
from app.services.ast_analyzer import (
    AnalysisError,
    analyze_project,
)
from app.services.code_reviewer import review_issues

router = APIRouter(prefix="/review", tags=["Code Review"])


@router.post("/{upload_id}", response_model=CodeReviewResponse)
def review_project(upload_id: str):
    """
    Analyze a previously uploaded project and generate
    explanations and fix suggestions for detected issues.
    """

    try:
        analysis = analyze_project(upload_id)

    except AnalysisError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    reviewed_issues = review_issues(analysis["issues"])

    return {
        "upload_id": upload_id,
        "total_issues": len(reviewed_issues),
        "review_provider": "rule_based",
        "reviews": reviewed_issues,
    }