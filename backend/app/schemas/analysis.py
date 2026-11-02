from typing import Literal

from pydantic import BaseModel


class AnalysisIssue(BaseModel):
    rule_id: str
    severity: Literal["high", "medium", "low"]
    message: str
    file_path: str
    line: int
    column: int
    suggestion: str


class FileAnalysis(BaseModel):
    file_path: str
    status: str
    lines_of_code: int
    issue_count: int


class AnalysisResponse(BaseModel):
    success: bool
    upload_id: str
    total_files: int
    analyzed_files: int
    total_issues: int
    severity_counts: dict[str, int]
    files: list[FileAnalysis]
    issues: list[AnalysisIssue]