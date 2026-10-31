from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.upload import UploadResponse
from app.services.upload_service import (
    UploadValidationError,
    store_python_file,
)

router = APIRouter()


@router.post(
    "/uploads",
    response_model=UploadResponse,
    status_code=201,
)
async def upload_python_file(
    file: Annotated[UploadFile, File()],
):
    """Upload and validate a single Python file."""

    try:
        result = await store_python_file(file)

        return {
            "success": True,
            **result,
        }

    except UploadValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc