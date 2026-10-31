import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

# Store uploads inside the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_ROOT = PROJECT_ROOT / "data" / "uploads"

CHUNK_SIZE = 64 * 1024


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message

        super().__init__(message)


def sanitize_filename(filename: str) -> str:
    """
    Extract a safe display filename.

    The original filename is never used as a storage path.
    """

    if not filename or "\x00" in filename:
        raise UploadValidationError(
            400,
            "INVALID_FILENAME",
            "A valid filename is required.",
        )

    normalized = filename.replace("\\", "/")
    safe_name = normalized.rsplit("/", maxsplit=1)[-1]

    if safe_name in {"", ".", ".."}:
        raise UploadValidationError(
            400,
            "INVALID_FILENAME",
            "The uploaded filename is invalid.",
        )

    return safe_name


async def store_python_file(upload: UploadFile) -> dict:
    """
    Validate and securely store one Python source file.

    Uploaded code is stored but never executed.
    """

    filename = sanitize_filename(upload.filename or "")

    if Path(filename).suffix.lower() != ".py":
        raise UploadValidationError(
            415,
            "UNSUPPORTED_FILE_TYPE",
            "Only Python (.py) files are allowed.",
        )

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if max_size <= 0:
        raise UploadValidationError(
            500,
            "INVALID_UPLOAD_CONFIGURATION",
            "The upload size limit is not configured correctly.",
        )

    upload_id = uuid4().hex

    upload_directory = UPLOAD_ROOT / upload_id
    destination = upload_directory / "source.py"

    total_size = 0

    try:
        upload_directory.mkdir(
            parents=True,
            exist_ok=False,
        )

        with destination.open("xb") as output_file:

            while True:
                chunk = await upload.read(CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size:
                    raise UploadValidationError(
                        413,
                        "FILE_TOO_LARGE",
                        f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                    )

                output_file.write(chunk)

        if total_size == 0:
            raise UploadValidationError(
                400,
                "EMPTY_FILE",
                "The uploaded file is empty.",
            )

        return {
            "upload_id": upload_id,
            "filename": filename,
            "file_size_bytes": total_size,
            "status": "uploaded",
            "python_files": [filename],
        }

    except Exception:
        # Remove incomplete uploads after any failure.
        shutil.rmtree(upload_directory, ignore_errors=True)
        raise

    finally:
        await upload.close()