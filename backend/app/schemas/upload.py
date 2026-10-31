from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    upload_id: str
    filename: str
    file_size_bytes: int
    status: str
    python_files: list[str]