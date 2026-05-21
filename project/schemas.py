from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConfidenceBucket(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    VERIFY_THIS = "VERIFY_THIS"


class ASTEvidence(BaseModel):
    node_type: str
    snippet: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]


class ReviewIssue(BaseModel):
    issue_id: str
    category: str
    severity: Severity
    confidence: float = Field(ge=0, le=100)
    confidence_bucket: Optional[ConfidenceBucket]
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    reasoning: Optional[str]
    suggested_fix: Optional[str]
    ast_evidence: List[ASTEvidence] = []
    tags: List[str] = []

    @validator("issue_id")
    def id_not_empty(cls, v):
        if not v:
            raise ValueError("issue_id required")
        return v
