import uuid
from typing import List, Dict
from .base_agent import BaseAgent
from ..schemas import ReviewIssue, ASTEvidence, Severity
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.maintainability")


class MaintainabilityAgent(BaseAgent):
    name = "maintainability"

    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str) -> List[ReviewIssue]:
        issues = []
        cyclo = ast_meta.get("cyclomatic_hint", 1)
        func_len = (ast_meta.get("line_end", 0) - ast_meta.get("line_start", 0))
        if cyclo > 10 or func_len > 200:
            issues.append(
                ReviewIssue(
                    issue_id=str(uuid.uuid4()),
                    category="maintainability",
                    severity=Severity.MEDIUM,
                    confidence=55.0,
                    confidence_bucket=None,
                    file_path=file_path,
                    line_start=ast_meta.get("line_start", 0),
                    line_end=ast_meta.get("line_end", 0),
                    title="Complex or large function",
                    description=f"Function complexity {cyclo} and length {func_len} lines may reduce maintainability.",
                    reasoning="Heuristic: cyclomatic hint and function length.",
                    suggested_fix="Refactor into smaller functions and add documentation/tests.",
                    ast_evidence=[ASTEvidence(node_type="function", snippet=None, line_start=ast_meta.get("line_start"), line_end=ast_meta.get("line_end"))],
                    tags=["complexity", "refactor"],
                )
            )

        if self.llm and self.prompts:
            prompt = self.prompts.build_prompt("maintainability_prompt", role="MaintainabilityAgent", ast_meta=ast_meta, code=code)
            try:
                resp = await self.llm.call(prompt)
                for r in resp:
                    try:
                        issues.append(ReviewIssue(**r))
                    except Exception:
                        logger.exception("Failed to parse maintainability LLM item: %s", r)
            except Exception:
                logger.exception("LLM maintainability call failed")

        return issues
