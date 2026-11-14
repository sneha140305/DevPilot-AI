from pydantic import BaseModel, Field


class RefactoringRequest(BaseModel):
    file_path: str = Field(
        min_length=1,
        max_length=500,
    )

    rule_id: str = Field(
        min_length=1,
        max_length=50,
    )

    line: int = Field(ge=1)


class RefactoringResponse(BaseModel):
    success: bool
    upload_id: str
    recommendation: dict