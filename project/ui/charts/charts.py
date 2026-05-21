import pandas as pd
from typing import List, Optional


def _try_import_px():
    try:
        import plotly.express as px

        return px
    except Exception:
        return None


def severity_pie_chart(severities: List[str]) -> Optional[object]:
    px = _try_import_px()
    if px is None:
        return None
    if not severities:
        return px.pie(values=[1], names=["no data"], title="Severity Distribution")
    df = pd.DataFrame({"severity": severities})
    counts = df["severity"].value_counts().reset_index()
    counts.columns = ["severity", "count"]
    fig = px.pie(counts, names="severity", values="count", title="Severity Distribution")
    return fig


def confidence_histogram(confidences: List[float]) -> Optional[object]:
    px = _try_import_px()
    if px is None:
        return None
    if not confidences:
        confidences = [0]
    fig = px.histogram(confidences, nbins=10, title="Confidence Distribution")
    return fig
