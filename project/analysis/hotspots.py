from typing import List, Dict
from collections import defaultdict
from ..schemas import ReviewIssue
from ..logging_config import get_logger

logger = get_logger("sentinelai.analysis.hotspots")


def compute_hotspots(issues: List[ReviewIssue], module_metrics: Dict[str, Dict]) -> List[Dict]:
    """Compute hotspot scores per module.

    module_metrics: mapping module -> {module_length, fan_in, fan_out}
    issues: list of ReviewIssue
    """
    counts = defaultdict(int)
    sev_weight = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}
    for it in issues:
        counts[it.file_path] += sev_weight.get(it.severity.value if hasattr(it.severity, 'value') else it.severity, 1)

    results = []
    for module, metrics in module_metrics.items():
        issue_score = counts.get(module, 0)
        complexity = metrics.get("module_length", 0)
        fan_in = metrics.get("fan_in", 0)
        fan_out = metrics.get("fan_out", 0)
        score = issue_score * 0.4 + min(100, complexity / 10) * 0.2 + fan_in * 0.2 + fan_out * 0.2
        results.append({"module": module, "score": round(score, 2), "issue_score": issue_score, "complexity": complexity, "fan_in": fan_in, "fan_out": fan_out})
    results.sort(key=lambda x: x["score"], reverse=True)
    logger.debug("Computed %d hotspots", len(results))
    return results
