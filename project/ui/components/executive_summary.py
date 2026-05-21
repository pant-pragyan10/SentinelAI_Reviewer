from typing import Dict, Any, List


def generate_executive_summary(reviews: Dict[str, List[Dict[str, Any]]], hotspots: List[Dict[str, Any]] = None, propagated: Dict[str, float] = None) -> str:
    if not reviews:
        return "No review data available. Run a review or load a demo preset."

    total_files = len(reviews)
    total_issues = sum(len(v) for v in reviews.values())
    # top severities
    sev_count = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for flist in reviews.values():
        for it in flist:
            s = it.get('severity')
            if s in sev_count:
                sev_count[s] += 1

    top_hotspots = []
    if hotspots:
        top_hotspots = [h['module'] for h in hotspots[:5]]

    top_impacted = []
    if propagated:
        top_impacted = sorted(propagated.items(), key=lambda kv: kv[1], reverse=True)[:5]

    lines = []
    lines.append(f"Repository Health: Files={total_files}, Issues={total_issues}")
    lines.append(f"Top severities: critical={sev_count['critical']}, high={sev_count['high']}, medium={sev_count['medium']}")
    if top_hotspots:
        lines.append(f"Top architecture hotspots: {', '.join(top_hotspots)}")
    if top_impacted:
        lines.append("Top propagated impact:")
        for k, v in top_impacted:
            lines.append(f" - {k}: {v:.1f}")

    return "\n\n".join(lines)
