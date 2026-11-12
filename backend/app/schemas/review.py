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

    # Phase 11: Intelligent debugging fields
    code_context: str = ""
    root_cause: str = "The underlying cause could not be determined."
    debugging_steps: list[str] = Field(default_factory=list)
    confidence_level: str = "low"
    context_available: bool = False


class CodeReviewResponse(BaseModel):
    upload_id: str
    total_issues: int
    review_provider: str = "rule_based"
    reviews: list[ReviewedIssue]