from typing import List, Dict, Any
from collections import defaultdict
from ..schemas import ReviewIssue
import math


SEVERITY_MAP = {"critical": 100, "high": 80, "medium": 50, "low": 20, "info": 5}


def _color_for_score(score: float) -> str:
    if score <= 25:
        return "#2ecc71"  # green
    if score <= 50:
        return "#f1c40f"  # yellow
    if score <= 75:
        return "#e67e22"  # orange
    return "#e74c3c"  # red


def compute_node_risks(tree: List[Dict[str, Any]], issues: List[Dict[str, Any]], module_centrality: Dict[str, float], file_stem: str) -> Dict[str, Dict[str, Any]]:
    """Compute risk scores for each node in an AST tree.

    Returns mapping node_id -> {risk: float, color: str, confidence: float}
    """
    # Index issues by line ranges for quick lookup
    issues_by_line = defaultdict(list)
    for it in issues:
        ls = it.get("line_start")
        le = it.get("line_end")
        if ls is None:
            continue
        for l in range(ls, (le or ls) + 1):
            issues_by_line[l].append(it)

    # module centrality fallback
    module_c = module_centrality.get(file_stem, 0.0)

    node_risks = {}

    def score_for_node(node: Dict[str, Any]) -> Dict[str, Any]:
        # severity weight: highest severity among overlapping issues
        ls = node.get("line_start")
        le = node.get("line_end") or ls
        overlapping = []
        if ls:
            for l in range(ls, le + 1):
                overlapping.extend(issues_by_line.get(l, []))

        severity_scores = []
        confidences = []
        for it in overlapping:
            sev = it.get("severity")
            if isinstance(sev, dict):
                sev = sev.get("value")
            sev_val = SEVERITY_MAP.get(sev, 0) if isinstance(sev, str) else 0
            severity_scores.append(sev_val)
            confidences.append(it.get("confidence", 0))

        severity_weight = max(severity_scores) if severity_scores else 0
        avg_conf = (sum(confidences) / len(confidences)) if confidences else 0

        # complexity weight from cyclomatic_hint (cap at 20)
        cyclo = node.get("cyclomatic_hint", 1) or 1
        complexity_weight = min(100, (cyclo / 20.0) * 100)

        # dangerous pattern weight
        dangerous = 100 if node.get("dangerous_calls") else 0

        # dependency weight uses module centrality scaled
        dependency_weight = min(100, module_c * 100)

        # confidence weight: higher confidence increases score
        confidence_weight = avg_conf

        # weighted sum
        score = (
            severity_weight * 0.35
            + complexity_weight * 0.2
            + dangerous * 0.2
            + dependency_weight * 0.15
            + confidence_weight * 0.1
        )
        score = max(0.0, min(100.0, round(score, 2)))
        return {"risk": score, "color": _color_for_score(score), "confidence": round(avg_conf, 2), "issue_count": len(overlapping)}

    # traverse tree categories and children
    for category in tree:
        for node in category.get("children", []):
            # node itself
            node_risks[node["id"]] = score_for_node(node)
            # children (methods etc.)
            for c in node.get("children", []):
                node_risks[c["id"]] = score_for_node(c)

    return node_risks
