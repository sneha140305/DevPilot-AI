import re

from fastapi import APIRouter, HTTPException

from app.repositories import project_repository

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.get("/")
def get_all_projects():
    """Retrieve all uploaded projects."""

    projects = project_repository.list_projects(
        db_path=project_repository.DATABASE_PATH
    )

    return {
        "success": True,
        "total_projects": len(projects),
        "projects": projects,
    }


@router.get("/{upload_id}")
def get_project_details(upload_id: str):
    """Retrieve a project using its upload ID."""

    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_UPLOAD_ID",
                "message": "Invalid upload ID.",
            },
        )

    project = project_repository.get_project(
        upload_id,
        db_path=project_repository.DATABASE_PATH,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": "Project not found.",
            },
        )

    return {
        "success": True,
        "project": project,
    }