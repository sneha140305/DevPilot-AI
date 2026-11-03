from pydantic import BaseModel


class TestGenerationResponse(BaseModel):
    upload_id: str
    file_path: str
    total_functions: int
    total_tests: int
    success: bool
    test_code: str
    message: str