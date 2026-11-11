from pydantic import BaseModel, Field


class FixRequest(BaseModel):
    file_path: str = Field(min_length=1, max_length=500)
    rule_id: str = Field(min_length=1, max_length=50)
    line: int = Field(ge=1)


class FixResponse(BaseModel):
    success: bool
    upload_id: str
    file_path: str
    rule_id: str
    line: int
    supported: bool
    message: str
    original_code: str | None = None
    proposed_code: str | None = None
    diff: str | None = None
    validation_passed: bool | None = None
    validation_message: str | None = None