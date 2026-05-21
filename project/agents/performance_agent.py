import uuid
from typing import List, Dict
from .base_agent import BaseAgent
from ..schemas import ReviewIssue, ASTEvidence, Severity
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.performance")


class PerformanceAgent(BaseAgent):
    name = "performance"

    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str) -> List[ReviewIssue]:
        issues = []
        depth = ast_meta.get("nested_loop_depth", 0)
        if depth >= 2:
            issues.append(
                ReviewIssue(
                    issue_id=str(uuid.uuid4()),
                    category="performance",
                    severity=Severity.MEDIUM,
                    confidence=60.0,
                    confidence_bucket=None,
                    file_path=file_path,
                    line_start=ast_meta.get("line_start", 0),
                    line_end=ast_meta.get("line_end", 0),
                    title="Deeply nested loops",
                    description=f"Function has nested loop depth {depth}, which can be a performance concern.",
                    reasoning="Detected nested loops via AST analysis.",
                    suggested_fix="Consider flattening loops or using streaming/iterators to reduce complexity.",
                    ast_evidence=[ASTEvidence(node_type="loops", snippet=f"depth={depth}", line_start=ast_meta.get("line_start"), line_end=ast_meta.get("line_end"))],
                    tags=["nested-loops"],
                )
            )

        # LLM enrichment optional
        if self.llm and self.prompts:
            prompt = self.prompts.build_prompt("performance_prompt", role="PerformanceAgent", ast_meta=ast_meta, code=code)
            try:
                resp = await self.llm.call(prompt)
                for r in resp:
                    try:
                        issues.append(ReviewIssue(**r))
                    except Exception:
                        logger.exception("Failed to parse LLM performance item: %s", r)
            except Exception:
                logger.exception("LLM performance call failed")

        return issues
