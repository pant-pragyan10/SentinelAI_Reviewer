from typing import List, Dict
from .base_agent import BaseAgent
from ..schemas import ReviewIssue, ASTEvidence
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.verifier")


class VerifierAgent(BaseAgent):
    name = "verifier"

    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str, findings: List[ReviewIssue] = None) -> List[ReviewIssue]:
        """Verify findings by checking AST evidence and downgrading unsupported claims."""
        findings = findings or []
        verified = []
        for f in findings:
            # Simple verification: ensure ast_evidence non-empty or description mentions dangerous token
            has_evidence = bool(f.ast_evidence)
            if has_evidence:
                # mark as confirmed
                f.reasoning = (f.reasoning or "") + " Verified by AST evidence."
                verified.append(f)
            else:
                # downgrade
                f.confidence = max(0.0, f.confidence * 0.5)
                f.reasoning = (f.reasoning or "") + " Verification: limited AST evidence; downgraded confidence."
                verified.append(f)
        return verified
