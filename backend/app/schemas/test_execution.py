from typing import Any

from pydantic import BaseModel, Field


class TestExecutionResponse(BaseModel):
    success: bool
    upload_id: str
    status: str
    exit_code: int
    stdout: str
    stderr: str
    test_file: str

    # Parsed pytest results
    tests_total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    xfailed: int = 0
    xpassed: int = 0

    duration_seconds: float | None = None
    summary_available: bool = False
    failure_details: list[str] = Field(default_factory=list)


class TestExecutionRecord(BaseModel):
    id: int
    upload_id: str
    result: dict[str, Any]
    created_at: str


class TestExecutionHistoryResponse(BaseModel):
    upload_id: str
    total_executions: int
    executions: list[TestExecutionRecord]