import uuid
from typing import List, Dict
from .base_agent import BaseAgent
from ..schemas import ReviewIssue, ASTEvidence, Severity
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.security")


class SecurityAgent(BaseAgent):
    name = "security"

    DANGEROUS_PATTERNS = {"eval", "exec", "subprocess", "pickle", "yaml.safe_load"}

    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str) -> List[ReviewIssue]:
        issues = []
        # Heuristic checks from ast_meta
        dangerous = ast_meta.get("dangerous_calls", [])
        for d in dangerous:
            issue = ReviewIssue(
                issue_id=str(uuid.uuid4()),
                category="security",
                severity=Severity.HIGH,
                confidence=75.0,
                confidence_bucket=None,
                file_path=file_path,
                line_start=ast_meta.get("line_start", 0),
                line_end=ast_meta.get("line_end", 0),
                title=f"Dangerous call: {d}",
                description=f"Detected potentially dangerous call `{d}`.",
                reasoning="Detected via AST heuristics.",
                suggested_fix=f"Avoid using `{d}`; use a safer alternative or validate inputs.",
                ast_evidence=[ASTEvidence(node_type="call", snippet=d, line_start=ast_meta.get("line_start"), line_end=ast_meta.get("line_end"))],
                tags=["insecure", d],
            )
            issues.append(issue)

        # If LLM available, ask for corroboration and additional issues
        if self.llm and self.prompts:
            prompt = self.prompts.build_prompt("security_prompt", role="SecurityAgent", ast_meta=ast_meta, code=code)
            try:
                resp = await self.llm.call(prompt)
                # Expect list of dicts; try to convert to ReviewIssue
                for r in resp:
                    try:
                        ri = ReviewIssue(**r)
                        issues.append(ri)
                    except Exception:
                        logger.exception("Failed to parse LLM security response item: %s", r)
            except Exception:
                logger.exception("LLM security call failed")

        return issues
