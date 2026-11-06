from fastapi import APIRouter

from app.repositories import dashboard_repository

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def get_dashboard_summary():
    """
    Return actual dashboard metrics from SQLite.
    """

    summary = dashboard_repository.get_dashboard_summary(
        db_path=dashboard_repository.DATABASE_PATH
    )

    return {
        "success": True,
        "summary": summary,
    }