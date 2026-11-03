from pydantic import BaseModel, Field


class ReviewedIssue(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    category: str

    message: str
    explanation: str
    impact: str
    fix_suggestion: str

    file_path: str
    line: int
    column: int

    confidence: float = Field(ge=0, le=1)
    review_provider: str


class CodeReviewResponse(BaseModel):
    upload_id: str
    total_issues: int
    review_provider: str = "rule_based"
    reviews: list[ReviewedIssue]