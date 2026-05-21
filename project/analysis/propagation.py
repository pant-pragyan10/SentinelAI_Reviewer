from typing import Dict, Any, Tuple, List
import networkx as nx


def propagate_risk_scores(
    g: nx.DiGraph,
    node_risks: Dict[str, float],
    decay: float = 0.6,
    max_hops: int = 10,
) -> Dict[str, float]:
    """Propagate risks downstream across the directed dependency graph.

    Returns a mapping of node -> propagated risk score (0-100 normalized).
    Algorithm: BFS from each risky node, attenuate by decay per hop and by edge weight if provided.
    """
    propagated: Dict[str, float] = {n: 0.0 for n in g.nodes()}

    # Normalize base node risks to 0-1
    max_base = max((v for v in node_risks.values()), default=0.0)
    norm = {n: (node_risks.get(n, 0.0) / max_base) if max_base > 0 else 0.0 for n in g.nodes()}

    for source, base in norm.items():
        if base <= 0:
            continue
        # traverse downstream
        visited = set()
        queue: List[Tuple[str, int, float]] = [(source, 0, base)]
        while queue:
            node, depth, score = queue.pop(0)
            if depth > max_hops:
                continue
            # accumulate score
            propagated[node] += score
            visited.add(node)
            for succ in g.successors(node):
                if succ in visited:
                    continue
                edge_w = g.get_edge_data(node, succ, default={}).get("weight", 1.0)
                next_score = score * decay * float(edge_w)
                if next_score < 1e-4:
                    continue
                queue.append((succ, depth + 1, next_score))

    # normalize propagated to 0-100
    max_p = max(propagated.values()) if propagated else 0.0
    if max_p <= 0:
        return {n: 0.0 for n in propagated}
    return {n: float((v / max_p) * 100.0) for n, v in propagated.items()}


def compute_blast_radius(
    g: nx.DiGraph, source: str, propagated: Dict[str, float], threshold: float = 10.0
) -> Dict[str, Any]:
    """Compute blast radius details for a source node.

    Returns summary: affected_count, affected_nodes list, blast_score (sum of propagated values), top_impacted
    """
    affected = [n for n, v in propagated.items() if v >= threshold and nx.has_path(g, source, n)]
    blast_score = sum(propagated.get(n, 0.0) for n in affected)
    top_impacted = sorted(affected, key=lambda n: propagated.get(n, 0.0), reverse=True)[:10]
    return {
        "source": source,
        "affected_count": len(affected),
        "blast_score": blast_score,
        "affected": top_impacted,
    }


def detect_high_impact_nodes(g: nx.DiGraph, propagated: Dict[str, float], top_k: int = 10) -> List[Dict[str, Any]]:
    items = sorted(propagated.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    out = []
    for n, score in items:
        out.append({"module": n, "propagated_score": score, "fan_out": g.out_degree(n), "fan_in": g.in_degree(n)})
    return out


def compute_instability_metrics(g: nx.DiGraph) -> Dict[str, Dict[str, float]]:
    """Compute fan-in, fan-out, coupling and simple instability metric per node."""
    metrics: Dict[str, Dict[str, float]] = {}
    for n in g.nodes():
        fan_in = g.in_degree(n)
        fan_out = g.out_degree(n)
        coupling = float(fan_in + fan_out)
        instability = (fan_out / coupling) if coupling > 0 else 0.0
        metrics[n] = {"fan_in": float(fan_in), "fan_out": float(fan_out), "coupling": coupling, "instability": instability}
    return metrics
