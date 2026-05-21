from ..schemas import ReviewIssue, ConfidenceBucket
from ..logging_config import get_logger

logger = get_logger("sentinelai.confidence.calibrator")


def calibrate_issue(issue: ReviewIssue, *, ast_score: float = 80.0, llm_score: float = 70.0, consensus_score: float = 75.0, rule_score: float = 80.0, verifier_score: float = 80.0) -> ReviewIssue:
    """Compute weighted confidence and set bucket on the issue.

    All inputs in 0-100.
    """
    total = (
        ast_score * 0.25
        + llm_score * 0.20
        + consensus_score * 0.25
        + rule_score * 0.15
        + verifier_score * 0.15
    )
    issue.confidence = round(total, 2)
    if issue.confidence >= 85:
        issue.confidence_bucket = ConfidenceBucket.HIGH_CONFIDENCE
    elif issue.confidence >= 60:
        issue.confidence_bucket = ConfidenceBucket.MEDIUM_CONFIDENCE
    else:
        issue.confidence_bucket = ConfidenceBucket.VERIFY_THIS
    logger.debug("Calibrated %s -> %s", issue.issue_id, issue.confidence_bucket)
    return issue
