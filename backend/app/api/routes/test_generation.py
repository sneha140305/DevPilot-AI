from fastapi import APIRouter, HTTPException

from app.schemas.test_generation import TestGenerationResponse
from app.services.test_generator import generate_tests_for_upload

router = APIRouter(
    prefix="/generate-tests",
    tags=["Test Generation"],
)


@router.post(
    "/{upload_id}/{file_name}",
    response_model=TestGenerationResponse,
)
def generate_project_tests(
    upload_id: str,
    file_name: str,
):
    try:
        return generate_tests_for_upload(
            upload_id,
            file_name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc