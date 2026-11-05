import shutil
import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.repositories.project_repository import create_project
from app.schemas.upload import UploadResponse
from app.services.upload_service import (
    UPLOAD_ROOT,
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
    Upload a Python file or ZIP project
    and persist its metadata in SQLite.
    """

    filename = file.filename or ""

    extension = Path(
        filename.replace("\\", "/")
    ).suffix.lower()

    try:

        if extension == ".py":
            result = await store_python_file(file)
            upload_type = "python"

        elif extension == ".zip":
            result = await store_zip_project(file)
            upload_type = "zip"

        else:
            raise HTTPException(
                status_code=415,
                detail={
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": "Only .py and .zip files are supported.",
                },
            )

        try:
            create_project(
                upload_id=result["upload_id"],
                original_filename=result["filename"],
                upload_type=upload_type,
            )

        except sqlite3.Error as exc:

            # Remove stored files if database registration fails.
            shutil.rmtree(
                UPLOAD_ROOT / result["upload_id"],
                ignore_errors=True,
            )

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "DATABASE_ERROR",
                    "message": "Upload succeeded, but project metadata could not be saved.",
                },
            ) from exc

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