"""Async orchestrator coordinating agents, verifier, deduplication, and calibration."""
import asyncio
from typing import List, Dict
from .parser.chunk_builder import build_chunks_for_file
from .schemas import ReviewIssue
from .llm.llm_client import LLMClient
from .prompts.prompt_loader import PromptLoader
from .agents.security_agent import SecurityAgent
from .agents.performance_agent import PerformanceAgent
from .agents.maintainability_agent import MaintainabilityAgent
from .agents.architecture_agent import ArchitectureAgent
from .agents.verifier_agent import VerifierAgent
from .agents.consensus_agent import ConsensusAgent
from .dedup.deduplicator import Deduplicator
from .confidence.calibrator import calibrate_issue
from .logging_config import get_logger
from pathlib import Path

logger = get_logger("sentinelai.orchestrator")


class Orchestrator:
    def __init__(self, prompts_dir: Path, mode: str = "Senior Engineer"):
        self.llm = LLMClient()
        self.prompts = PromptLoader(prompts_dir)
        self.prompts.mode = mode
        self.security = SecurityAgent(llm_client=self.llm, prompt_loader=self.prompts)
        self.performance = PerformanceAgent(llm_client=self.llm, prompt_loader=self.prompts)
        self.maintain = MaintainabilityAgent(llm_client=self.llm, prompt_loader=self.prompts)
        self.arch = ArchitectureAgent(llm_client=self.llm, prompt_loader=self.prompts)
        self.verifier = VerifierAgent()
        self.consensus = ConsensusAgent()
        self.dedup = Deduplicator()

    async def review_file(self, path: Path) -> List[ReviewIssue]:
        chunks = build_chunks_for_file(path)
        tasks = []
        for c in chunks:
            ast_meta = {
                "line_start": c.get("start"),
                "line_end": c.get("end"),
                "dangerous_calls": [],
                "nested_loop_depth": 0,
                "cyclomatic_hint": 1,
                "module_length": c.get("end") or 0,
            }
            code = c.get("code") or ""
            # dispatch agents concurrently per chunk
            tasks.append(self.security.analyze(code=code, ast_meta=ast_meta, file_path=str(path)))
            tasks.append(self.performance.analyze(code=code, ast_meta=ast_meta, file_path=str(path)))
            tasks.append(self.maintain.analyze(code=code, ast_meta=ast_meta, file_path=str(path)))
            tasks.append(self.arch.analyze(code=code, ast_meta=ast_meta, file_path=str(path)))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        findings: List[ReviewIssue] = []
        for r in results:
            if isinstance(r, Exception):
                logger.exception("Agent task failed: %s", r)
                continue
            findings.extend(r)

        # verifier pass
        findings = await self.verifier.analyze(code="", ast_meta={}, file_path=str(path), findings=findings)

        # consensus aggregation
        findings = await self.consensus.analyze(findings=findings)

        # deduplicate
        findings = self.dedup.deduplicate(findings)

        # calibrate
        calibrated = [calibrate_issue(f) for f in findings]

        return calibrated

    async def review_repo(self, repo_path: Path) -> Dict[str, List[ReviewIssue]]:
        from .github.repo_scanner import discover_source_files

        files = discover_source_files(repo_path)
        out = {}
        for f in files:
            out[str(f)] = await self.review_file(f)
        return out
