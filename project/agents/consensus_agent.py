from typing import List
from .base_agent import BaseAgent
from ..schemas import ReviewIssue
from ..logging_config import get_logger

logger = get_logger("sentinelai.agents.consensus")


class ConsensusAgent(BaseAgent):
    name = "consensus"

    async def analyze(self, *, findings: List[ReviewIssue]) -> List[ReviewIssue]:
        # Simple placeholder: average confidences for identical categories/locations
        grouped = {}
        for f in findings:
            key = (f.file_path, f.line_start, f.line_end, f.category)
            lst = grouped.setdefault(key, [])
            lst.append(f)

        merged = []
        for key, lst in grouped.items():
            if len(lst) == 1:
                merged.append(lst[0])
                continue
            # merge into single issue
            base = lst[0]
            avg_conf = sum(i.confidence for i in lst) / len(lst)
            base.confidence = avg_conf
            base.reasoning = (base.reasoning or "") + " Aggregated by ConsensusAgent."
            merged.append(base)

        return merged
