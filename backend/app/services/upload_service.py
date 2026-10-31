import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

# Store uploads inside the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_ROOT = PROJECT_ROOT / "data" / "uploads"

CHUNK_SIZE = 64 * 1024
MAX_EXTRACTED_SIZE = (
    settings.MAX_EXTRACTED_SIZE_MB * 1024 * 1024
)

MAX_SINGLE_FILE_SIZE = (
    settings.MAX_FILE_SIZE_MB * 1024 * 1024
)

MAX_PROJECT_FILES = settings.MAX_FILES_PER_PROJECT

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".idea",
    ".vscode",
}

NESTED_ARCHIVE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
}

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

def validate_zip_path(filename: str) -> PurePosixPath:
    """
    Validate ZIP entry paths against path traversal attacks.
    """

    if not filename or "\x00" in filename:
        raise UploadValidationError(
            400,
            "INVALID_ZIP_PATH",
            "ZIP contains an invalid file path.",
        )

    normalized = filename.replace("\\", "/")
    path = PurePosixPath(normalized)

    if (
        path.is_absolute()
        or ".." in path.parts
        or ":" in normalized
        or normalized.startswith("/")
    ):
        raise UploadValidationError(
            400,
            "ZIP_PATH_TRAVERSAL",
            "ZIP contains an unsafe file path.",
        )

    if not path.parts:
        raise UploadValidationError(
            400,
            "INVALID_ZIP_PATH",
            "ZIP contains an invalid file path.",
        )

    return path

def should_ignore_path(path: PurePosixPath) -> bool:
    """
    Identify unnecessary project directories.
    """

    return any(
        part.lower() in IGNORED_DIRECTORIES
        for part in path.parts
    )

async def store_zip_project(upload: UploadFile) -> dict:
    """
    Safely validate and extract a ZIP project.

    Uploaded files are never executed.
    """

    filename = sanitize_filename(upload.filename or "")

    if Path(filename).suffix.lower() != ".zip":
        raise UploadValidationError(
            415,
            "UNSUPPORTED_FILE_TYPE",
            "Only ZIP archives are accepted by this operation.",
        )

    upload_id = uuid4().hex

    upload_directory = UPLOAD_ROOT / upload_id
    archive_path = upload_directory / "project.zip"
    project_directory = upload_directory / "project"

    max_archive_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    total_archive_size = 0

    try:
        upload_directory.mkdir(
            parents=True,
            exist_ok=False,
        )

        # Save the compressed archive safely.
        with archive_path.open("xb") as archive_file:

            while True:
                chunk = await upload.read(CHUNK_SIZE)

                if not chunk:
                    break

                total_archive_size += len(chunk)

                if total_archive_size > max_archive_size:
                    raise UploadValidationError(
                        413,
                        "ARCHIVE_TOO_LARGE",
                        "ZIP archive exceeds the upload size limit.",
                    )

                archive_file.write(chunk)

        if total_archive_size == 0:
            raise UploadValidationError(
                400,
                "EMPTY_ARCHIVE",
                "The uploaded ZIP archive is empty.",
            )

        if not zipfile.is_zipfile(archive_path):
            raise UploadValidationError(
                400,
                "INVALID_ARCHIVE",
                "The uploaded file is not a valid ZIP archive.",
            )

        project_directory.mkdir()

        total_extracted_size = 0
        extracted_file_count = 0
        python_files = []

        with zipfile.ZipFile(archive_path, "r") as archive:

            entries = archive.infolist()

            for entry in entries:

                safe_path = validate_zip_path(entry.filename)

                if should_ignore_path(safe_path):
                    continue

                if entry.is_dir():
                    continue

                # Reject symbolic links.
                unix_mode = entry.external_attr >> 16

                if stat.S_ISLNK(unix_mode):
                    raise UploadValidationError(
                        400,
                        "SYMLINK_NOT_ALLOWED",
                        "ZIP archives containing symbolic links are not allowed.",
                    )

                # Reject nested archives.
                extension = Path(safe_path.name).suffix.lower()

                if extension in NESTED_ARCHIVE_EXTENSIONS:
                    raise UploadValidationError(
                        400,
                        "NESTED_ARCHIVE_NOT_ALLOWED",
                        "Nested archives are not allowed.",
                    )

                extracted_file_count += 1

                if extracted_file_count > MAX_PROJECT_FILES:
                    raise UploadValidationError(
                        413,
                        "TOO_MANY_FILES",
                        "Project exceeds the maximum file count.",
                    )

                if entry.file_size > MAX_SINGLE_FILE_SIZE:
                    raise UploadValidationError(
                        413,
                        "FILE_TOO_LARGE",
                        "A project file exceeds the individual file size limit.",
                    )

                total_extracted_size += entry.file_size

                if total_extracted_size > MAX_EXTRACTED_SIZE:
                    raise UploadValidationError(
                        413,
                        "PROJECT_TOO_LARGE",
                        "Extracted project exceeds the size limit.",
                    )

                destination = project_directory.joinpath(
                    *safe_path.parts
                )

                # Ensure the resolved destination stays inside project_directory.
                resolved_destination = destination.resolve()
                resolved_root = project_directory.resolve()

                if not resolved_destination.is_relative_to(resolved_root):
                    raise UploadValidationError(
                        400,
                        "ZIP_PATH_TRAVERSAL",
                        "ZIP contains an unsafe destination path.",
                    )

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                # Never overwrite an existing extracted file.
                with (archive.open(entry, "r") as source,
                    destination.open("xb") as target,
                ):

                        copied_size = 0

                        while True:
                            chunk = source.read(CHUNK_SIZE)

                            if not chunk:
                                break

                            copied_size += len(chunk)

                            if copied_size > MAX_SINGLE_FILE_SIZE:
                                raise UploadValidationError(
                                    413,
                                    "FILE_TOO_LARGE",
                                    "A project file exceeds the individual file size limit.",
                                )

                            target.write(chunk)

                if safe_path.suffix.lower() == ".py":
                    python_files.append(safe_path.as_posix())

        if not python_files:
            raise UploadValidationError(
                400,
                "NO_PYTHON_FILES",
                "The ZIP archive does not contain any Python files.",
            )

        # Remove the compressed archive after extraction.
        archive_path.unlink(missing_ok=True)

        return {
            "upload_id": upload_id,
            "filename": filename,
            "file_size_bytes": total_archive_size,
            "status": "uploaded",
            "python_files": sorted(python_files),
        }

    except (
        UploadValidationError,
        zipfile.BadZipFile,
        RuntimeError,
        OSError,
    ) as exc:

        shutil.rmtree(upload_directory, ignore_errors=True)

        if isinstance(exc, UploadValidationError):
            raise

        if isinstance(exc, zipfile.BadZipFile):
            raise UploadValidationError(
                400,
                "INVALID_ARCHIVE",
                "The ZIP archive is corrupted or invalid.",
            ) from exc

        raise UploadValidationError(
            400,
            "ARCHIVE_PROCESSING_FAILED",
            "The ZIP archive could not be processed.",
        ) from exc

    finally:
        await upload.close()

