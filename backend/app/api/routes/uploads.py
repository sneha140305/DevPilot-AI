from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.upload import UploadResponse
from app.services.upload_service import (
    UploadValidationError,
    store_python_file,
    store_zip_project,
)

router = APIRouter()


@router.post(
    "/uploads",
    response_model=UploadResponse,
    status_code=201,
)
async def upload_project(
    file: Annotated[UploadFile, File()],
):
    """
    Upload an individual Python file or ZIP project.
    """

    filename = file.filename or ""

    extension = Path(filename.replace("\\", "/")).suffix.lower()

    try:

        if extension == ".py":
            result = await store_python_file(file)

        elif extension == ".zip":
            result = await store_zip_project(file)

        else:
            raise HTTPException(
                status_code=415,
                detail={
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": "Only .py and .zip files are supported.",
                },
            )

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