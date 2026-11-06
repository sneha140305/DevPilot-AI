import logging
import re

from fastapi import APIRouter, HTTPException

from app.repositories.test_generation_repository import (
    get_latest_test_generation,
    list_test_generations,
    save_test_generation,
)
from app.schemas.test_generation import TestGenerationResponse
from app.services.test_generator import generate_tests_for_upload

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/generate-tests",
    tags=["Test Generation"],
)


def validate_upload_id(upload_id: str):
    if not re.fullmatch(r"[a-f0-9]{32}", upload_id):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_UPLOAD_ID",
                "message": "Invalid upload ID.",
            },
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
        result = generate_tests_for_upload(
            upload_id,
            file_name,
        )

        save_test_generation(
            upload_id,
            result,
        )

        return result

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

    except Exception as exc:
        logger.exception(
            "Test generation persistence failed."
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "TEST_GENERATION_ERROR",
                "message": "Unable to generate or save tests.",
            },
        ) from exc


@router.get("/{upload_id}/history")
def get_test_generation_history(upload_id: str):
    validate_upload_id(upload_id)

    history = list_test_generations(upload_id)

    return {
        "success": True,
        "upload_id": upload_id,
        "total_generations": len(history),
        "history": history,
    }


@router.get("/{upload_id}/latest")
def get_latest_test_generation_result(upload_id: str):
    validate_upload_id(upload_id)

    result = get_latest_test_generation(upload_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TEST_GENERATION_NOT_FOUND",
                "message": "No test generation history found.",
            },
        )

    return {
        "success": True,
        **result,
    }