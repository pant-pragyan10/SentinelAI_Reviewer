import streamlit as st
import networkx as nx
from typing import Any, Dict, Optional


# Defer Plotly imports to runtime to avoid import-time hangs when plotly is
# not installed in the environment. Functions will return None when Plotly is
# unavailable and callers should handle that case.
def _try_import_plotly():
    try:
        import plotly.graph_objects as go

        return go
    except Exception:
        return None


def plot_networkx_graph(g: nx.Graph, title: str = "Dependency Graph", propagated: Dict[str, float] = None, highlight_node: str = None) -> Optional[Any]:
    """Plot directed dependency graph with optional propagated risk overlay.

    - `propagated`: mapping node -> propagated risk (0-100)
    - `highlight_node`: node id to glow/highlight
    """
    pos = nx.spring_layout(g, seed=42)
    edge_x = []
    edge_y = []
    edge_text = []
    edge_colors = []
    edge_widths = []
    for u, v, data in g.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        label = data.get("type", "")
        # color by propagated risk on target node if available
        target_risk = (propagated or {}).get(v, 0.0)
        if target_risk >= 75:
            ec = "#e74c3c"
            ew = 3.5
        elif target_risk >= 50:
            ec = "#e67e22"
            ew = 2.5
        elif target_risk >= 25:
            ec = "#f1c40f"
            ew = 1.5
        else:
            ec = "#888"
            ew = 1.0
        edge_text.append(label)
        edge_colors.append(ec)
        edge_widths.append(ew)

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    for n, d in g.nodes(data=True):
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        meta = d.copy() if isinstance(d, dict) else {"info": str(d)}
        base_risk = meta.get("risk") or meta.get("risk_score") or 0.0
        prop = (propagated or {}).get(n, 0.0)
        centrality = meta.get("centrality")
        node_text.append(f"{n}<br>base_risk: {base_risk}<br>propagated: {prop:.1f}<br>centrality: {centrality}")
        # derive color from propagated risk
        if prop >= 75:
            nc = "#e74c3c"
        elif prop >= 50:
            nc = "#e67e22"
        elif prop >= 25:
            nc = "#f1c40f"
        elif base_risk and float(base_risk) > 0:
            nc = "#f39c12"
        else:
            nc = meta.get("color") or "#636EFA"
        node_color.append(nc)
        size = 20 + (centrality or 0.0) * 40 + (prop / 100.0) * 30
        node_size.append(size)

    go = _try_import_plotly()
    if go is None:
        # Plotly not available in environment
        return None

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color="#888"), hoverinfo="text", mode="lines")
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        textposition="top center",
        hoverinfo="text",
        marker=dict(color=node_color, size=node_size, line=dict(width=2, color="#222")),
        text=[str(n) for n in g.nodes()],
        customdata=[str(n) for n in g.nodes()],
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title=title, showlegend=False)
    return fig
