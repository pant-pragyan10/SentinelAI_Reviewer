import uuid
from typing import List, Dict
from .base_agent import BaseAgent
from ..schemas import ReviewIssue, ASTEvidence, Severity
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.architecture")


class ArchitectureAgent(BaseAgent):
    name = "architecture"

    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str) -> List[ReviewIssue]:
        issues = []
        # Simple heuristic: very large module
        module_len = ast_meta.get("module_length", 0)
        if module_len and module_len > 1000:
            issues.append(
                ReviewIssue(
                    issue_id=str(uuid.uuid4()),
                    category="architecture",
                    severity=Severity.MEDIUM,
                    confidence=50.0,
                    confidence_bucket=None,
                    file_path=file_path,
                    line_start=1,
                    line_end=ast_meta.get("module_length", 0),
                    title="Large module may indicate poor separation of concerns",
                    description="Module length exceeds recommended boundaries.",
                    reasoning="Heuristic: module length.",
                    suggested_fix="Break module into smaller components by responsibility.",
                    ast_evidence=[],
                    tags=["module-size"],
                )
            )

        if self.llm and self.prompts:
            prompt = self.prompts.build_prompt("architecture_prompt", role="ArchitectureAgent", ast_meta=ast_meta, code=code)
            try:
                resp = await self.llm.call(prompt)
                for r in resp:
                    try:
                        issues.append(ReviewIssue(**r))
                    except Exception:
                        logger.exception("Failed to parse architecture LLM item: %s", r)
            except Exception:
                logger.exception("LLM architecture call failed")

        return issues
