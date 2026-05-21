"""Streamlit dashboard for SentinelAI Reviewer.

Provides multi-page UI, repository loader, and visualization hooks into the orchestrator.
"""
from pathlib import Path
import streamlit as st
from project.ui.components.metrics import metric_card
from project.ui.components.issue_card import render_issue_card
from project.ui.components.code_view import render_code_snippet
from project.ui.charts.charts import severity_pie_chart, confidence_histogram
from project.orchestrator import Orchestrator                                         
from project.github.clone_repo import clone_repo                                      
from project.logging_config import get_logger                                         
import asyncio
import json
from project.ui.exports import export_json, export_csv

logger = get_logger("sentinelai.ui.dashboard")


ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "project" / "prompts"
from project.ui.components.graph_viz import plot_networkx_graph
try:
    from streamlit_plotly_events import plotly_events
except Exception:
    plotly_events = None
from project.parser.dependency_graph import build_dependency_graph
from project.analysis.hotspots import compute_hotspots
from project.analysis.propagation import propagate_risk_scores, compute_blast_radius, detect_high_impact_nodes, compute_instability_metrics
from project.auto_fix.suggester import suggest_auto_fix
from project.schemas import ReviewIssue
from project.ui.components.ast_explorer import render_ast_explorer
from project.ui.components.explainability_panel import render_explainability_panel
from project.ui.components.demo_presets import render_demo_presets
from project.ui.components.walkthrough import render_walkthrough
from project.ui.components.executive_summary import generate_executive_summary
from project.ui.components.demo_script import render_demo_script
from project.ui.components.architecture_panel import render_architecture_panel
import os


def sidebar_nav() -> str:
    pages = [
        "Repository Overview",
        "AI Review Explorer",
        "Agent Reasoning",
        "AST Intelligence",
        "Risk Analytics",
        "PR Review Simulator",
        "System Pipeline Monitor",
    ]
    return st.sidebar.selectbox("Navigate", pages)


def load_and_review(repo_url: str, mode: str = "Senior Engineer"):
    st.session_state["status"] = "cloning"
    res = clone_repo(repo_url)
    repo_path = res.path
    st.session_state["status"] = "reviewing"
    orch = Orchestrator(prompts_dir=PROMPTS_DIR, mode=mode)
    reviews = asyncio.run(orch.review_repo(repo_path))
    st.session_state["reviews"] = {k: [r.dict() for r in v] for k, v in reviews.items()}
    st.session_state["repo_path"] = str(repo_path)
    st.session_state["status"] = "done"


def main():
    st.set_page_config(page_title="SentinelAI Reviewer", layout="wide")
    st.sidebar.title("SentinelAI")
    # Demo mode banner: shown when no LLM provider/api key configured
    if not os.environ.get("LLM_PROVIDER") or not os.environ.get("GROQ_API_KEY"):
        st.sidebar.warning("Demo Mode Active: running in offline/demo mode (no LLM provider configured). Some features are stubbed.")
    nav = sidebar_nav()
    # allow programmatic navigation via session_state (e.g., explainability quick actions)
    nav = st.session_state.get('open_tab', nav)

    with st.sidebar.expander("Load Repository"):
        repo_url = st.text_input("GitHub repo URL", value="https://github.com/psf/requests")
        mode = st.selectbox("Reviewer Mode", options=["Senior Engineer", "Security Auditor", "Strict Reviewer", "Performance Specialist"], index=0)
        demo = st.selectbox("Demo Preset", options=["None", "Sample: Flask Demo"], index=0)
        # demo presets UI
        render_demo_presets()
        if st.button("Load and Review"):
            try:
                load_and_review(repo_url, mode=mode)
            except Exception as e:
                st.error(f"Failed to review repository: {e}")

    reviews = st.session_state.get("reviews", {})

    # render explainability panel in sidebar
    try:
        render_explainability_panel()
    except Exception as e:
        st.error(f"Explainability panel failed to render: {e}")
    # demo walkthrough and scripts
    try:
        render_walkthrough()
    except Exception as e:
        st.error(f"Walkthrough failed to render: {e}")
    try:
        render_demo_script(st.session_state.get('reviews', {}), None, st.session_state.get('propagated_map'))
    except Exception as e:
        st.error(f"Demo script failed to render: {e}")
    try:
        render_architecture_panel()
    except Exception as e:
        st.error(f"Architecture panel failed to render: {e}")

    if nav == "Repository Overview":
        st.header("Repository Overview")
        repo_path = st.session_state.get("repo_path")
        if not repo_path:
            st.info("Load a repository to start analysis.")
            return
        total_files = len(reviews)
        total_issues = sum(len(v) for v in reviews.values())
        # severity distribution
        severities = []
        confidences = []
        for flist in reviews.values():
            for it in flist:
                severities.append(it.get("severity"))
                confidences.append(it.get("confidence", 0))

        col1, col2, col3, col4 = st.columns(4)
        metric_card(col1, "Total Files", total_files)
        metric_card(col2, "Total Issues", total_issues)
        health_score = 100 - (severities.count("critical") * 10 + severities.count("high") * 5 + severities.count("medium") * 2)
        metric_card(col3, "Repo Health", f"{max(0, health_score)} / 100")
        metric_card(col4, "Avg Confidence", f"{(sum(confidences)/len(confidences) if confidences else 0):.1f}")

        sp = severity_pie_chart(severities)
        ch = confidence_histogram(confidences)
        if sp is None or ch is None:
            st.warning("Plotly is not installed: install `plotly` to enable interactive charts.")
        else:
            st.plotly_chart(sp, use_container_width=True)
            st.plotly_chart(ch, use_container_width=True)
        # executive summary for presentation
        if st.button("Generate Executive Summary"):
            hotspots = compute_hotspots([r for fl in reviews.values() for r in fl], {})
            summary = generate_executive_summary(reviews, hotspots=hotspots, propagated=st.session_state.get('propagated_map'))
            st.subheader("Executive Summary")
            st.code(summary)
            st.download_button("Download Summary", summary, file_name="executive_summary.md")

    elif nav == "AI Review Explorer":
        st.header("AI Review Explorer")
        if not reviews:
            st.info("No reviews available. Load a repo first.")
            return
        severity_filter = st.multiselect("Severity", options=["critical", "high", "medium", "low", "info"], default=[])
        min_conf = st.slider("Min Confidence", 0, 100, 0)
        search = st.text_input("Search issues")
        module_filter = st.session_state.get('issue_filter_module')
        if module_filter:
            st.write(f"Filtering issues for module: {module_filter}")

        items = []
        for fpath, flist in reviews.items():
            for it in flist:
                if severity_filter and it.get("severity") not in severity_filter:
                    continue
                if it.get("confidence", 0) < min_conf:
                    continue
                # module filter
                if module_filter:
                    if Path(fpath).stem != module_filter:
                        continue
                if search and search.lower() not in (it.get("title", "") + it.get("description", "") + it.get("reasoning", "")).lower():
                    continue
                items.append((fpath, it))

        for fpath, it in items:
            render_issue_card(it, file_path=fpath)

    elif nav == "Agent Reasoning":
        st.header("Agent Reasoning")
        st.markdown("Visual trace of agent findings and reasoning.")
        # Simple expandable traces
        for fpath, flist in reviews.items():
            for it in flist:
                with st.expander(f"{it.get('title')} ({it.get('confidence')}%)"):
                    st.write("Category:", it.get("category"))
                    st.write("Severity:", it.get("severity"))
                    st.write("Reasoning:")
                    st.code(it.get("reasoning", ""))
                    st.write("AST Evidence:")
                    st.json(it.get("ast_evidence", []))

    elif nav == "AST Intelligence":
        st.header("AST Intelligence View")
        st.info("Interactive AST explorer and dependency graphs are available here.")
        st.write("(Use the orchestrator output for file-level metadata and dependencies.)")
        repo_path = st.session_state.get("repo_path")
        if repo_path:
            from project.github.repo_scanner import discover_source_files

            files = discover_source_files(repo_path)
            if files:
                g = build_dependency_graph(files)
                # basic module metrics
                module_metrics = {}
                for p in files:
                    try:
                        with open(p, "r", encoding="utf-8") as fh:
                            module_metrics[p.name] = {"module_length": sum(1 for _ in fh)}
                    except Exception:
                        module_metrics[p.name] = {"module_length": 0}

                issues = []
                for flist in st.session_state.get("reviews", {}).values():
                    for it in flist:
                        try:
                            issues.append(ReviewIssue(**it))
                        except Exception:
                            pass
                hotspots = compute_hotspots(issues, module_metrics)
                # annotate graph nodes with centrality and hotspot risk
                import networkx as nx

                centrality = nx.degree_centrality(g)
                hotspot_map = {h["module"]: h for h in hotspots}
                for n in list(g.nodes()):
                    g.nodes[n]["centrality"] = centrality.get(n, 0.0)
                    h = hotspot_map.get(n)
                    if h:
                        g.nodes[n]["risk"] = h.get("score")
                        if h.get("score") <= 25:
                            g.nodes[n]["color"] = "#2ecc71"
                        elif h.get("score") <= 50:
                            g.nodes[n]["color"] = "#f1c40f"
                        elif h.get("score") <= 75:
                            g.nodes[n]["color"] = "#e67e22"
                        else:
                            g.nodes[n]["color"] = "#e74c3c"

                # derive base module risks from issues (grouped by file stem)
                from project.analysis.risk import SEVERITY_MAP

                module_base_risks = {}
                for it in issues:
                    try:
                        m = Path(it.file_path).stem
                    except Exception:
                        # if ReviewIssue object lacks file_path string
                        m = Path(getattr(it, 'file_path', '') or '').stem
                    sev = it.get('severity') if isinstance(it, dict) else getattr(it, 'severity', None)
                    if isinstance(sev, str):
                        sev_val = SEVERITY_MAP.get(sev, 0)
                    else:
                        sev_val = 0
                    module_base_risks[m] = max(module_base_risks.get(m, 0), sev_val)

                propagated = propagate_risk_scores(g, module_base_risks)
                st.session_state['propagated_map'] = propagated

                fig = plot_networkx_graph(g, propagated=propagated)
                clicks = None
                try:
                    if fig is None:
                        st.warning("Plotly is not installed: install `plotly` to enable interactive dependency graphs.")
                    else:
                        # capture clicks from plotly via streamlit-plotly-events if available
                        if plotly_events is not None:
                            try:
                                clicks = plotly_events(fig, select_event=False, override_height=600, key="dep_graph")
                            except Exception:
                                # avoid raw tracebacks from plotly events handler
                                st.error("Interactive graph events temporarily unavailable.")
                                clicks = None
                        try:
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            st.error("Failed to render interactive graph. Showing static fallback.")
                            st.write("[Interactive graph unsupported in this environment]")
                except Exception as e:
                    st.error(f"Graph rendering failed: {e}")

                if clicks:
                    # clicks is list of event dicts; customdata holds node id
                    first = clicks[0]
                    node_id = None
                    # customdata may be at point 'customdata'
                    if 'customdata' in first:
                        node_id = first.get('customdata')
                    elif 'points' in first and first['points']:
                        node_id = first['points'][0].get('customdata')
                    if node_id:
                        st.session_state['selected_module'] = node_id
                        # find file path for module
                        mod_file = None
                        for p in files:
                            if p.stem == node_id:
                                mod_file = str(p)
                                break
                        if mod_file:
                            # Always set the file selection; do AST jump in guarded manner
                            st.session_state['selected_file'] = mod_file
                            st.session_state['open_tab'] = 'AST Intelligence'
                            try:
                                # find reviews for this module and attempt to pick top finding
                                reviews_for_mod = [r for fl in st.session_state.get('reviews', {}).values() for r in fl if Path(r.get('file_path','')).stem == node_id]
                                if reviews_for_mod:
                                    top = sorted(reviews_for_mod, key=lambda r: r.get('confidence',0), reverse=True)[0]
                                    st.session_state['selected_finding'] = top
                                    st.session_state['selected_node_line'] = top.get('line_start')
                            except Exception:
                                # fallback: only open the file-level explorer
                                st.info("Opened module view; AST jump not available for this item.")

                st.subheader("Architecture Hotspots")
                for h in hotspots[:10]:
                    st.write(h)

                st.info("Click nodes in the graph to inspect modules. Use Issue Explorer to jump to findings.")
                # File selector + AST explorer
                st.subheader("Files")
                file_options = [str(p) for p in files]
                # respect session selected_file when available
                default_idx = 0
                sf = st.session_state.get('selected_file')
                if sf and str(sf) in file_options:
                    try:
                        default_idx = file_options.index(str(sf))
                    except Exception:
                        default_idx = 0
                sel = st.selectbox("Select file to explore", options=file_options, index=default_idx)
                if sel:
                    render_ast_explorer(sel, [r for fl in st.session_state.get("reviews", {}).values() for r in fl])

    elif nav == "Risk Analytics":
        st.header("Risk Analytics")
        st.write("Aggregated risk visualizations and hotspots")
        repo_path = st.session_state.get("repo_path")
        if repo_path:
            from project.github.repo_scanner import discover_source_files

            files = discover_source_files(repo_path)
            module_metrics = {}
            for p in files:
                try:
                    with open(p, "r", encoding="utf-8") as fh:
                        module_metrics[p.name] = {"module_length": sum(1 for _ in fh), "fan_in": 0, "fan_out": 0}
                except Exception:
                    module_metrics[p.name] = {"module_length": 0, "fan_in": 0, "fan_out": 0}
            issues = []
            for flist in st.session_state.get("reviews", {}).values():
                for it in flist:
                    try:
                        issues.append(ReviewIssue(**it))
                    except Exception:
                        pass
            hotspots = compute_hotspots(issues, module_metrics)
            st.subheader("Hotspots Summary")
            st.table(hotspots[:20])

            # Build dependency graph and compute propagation
            g = build_dependency_graph(files)
            from project.analysis.risk import SEVERITY_MAP
            module_base_risks = {}
            for it in issues:
                m = Path(it.file_path).stem
                sev = it.severity.value if getattr(it, 'severity', None) else None
                sev_val = SEVERITY_MAP.get(sev, 0) if sev else 0
                module_base_risks[m] = max(module_base_risks.get(m, 0), sev_val)

            propagated = propagate_risk_scores(g, module_base_risks)
            st.session_state['propagated_map'] = propagated
            import networkx as nx
            instability = compute_instability_metrics(g)
            high_impacts = detect_high_impact_nodes(g, propagated, top_k=15)

            st.subheader("High Impact Modules")
            for hi in high_impacts:
                st.write(f"{hi['module']}: score={hi['propagated_score']:.1f}, fan_out={hi['fan_out']}, fan_in={hi['fan_in']}")

            st.subheader("Blast Radius Explorer")
            node_options = [h['module'] for h in high_impacts]
            sel = st.selectbox("Select module to analyze blast radius", options=node_options)
            if sel:
                br = compute_blast_radius(g, sel, propagated, threshold=10.0)
                st.metric("Affected Modules", br['affected_count'], delta=f"Blast Score: {br['blast_score']:.1f}")
                st.write("Top affected modules:")
                for a in br['affected']:
                    st.write(f" - {a} (propagated: {propagated.get(a,0):.1f})")

                # show critical path examples: shortest path to top affected
                st.write("Critical paths to top affected modules:")
                for target in br['affected'][:5]:
                    try:
                        path = list(nx.shortest_path(g, sel, target))
                        st.write(f"{sel} -> {' -> '.join(path[1:])} (len={len(path)-1})")
                    except Exception:
                        st.write(f"No path to {target}")

            st.subheader("Instability Metrics (Top Fragile Modules)")
            fragile = sorted(instability.items(), key=lambda kv: kv[1].get('instability',0), reverse=True)[:10]
            for n, m in fragile:
                st.write(f"{n}: instability={m['instability']:.2f}, fan_in={m['fan_in']}, fan_out={m['fan_out']}")

            st.info("Use the AST Intelligence page to click modules and jump to findings. Use the blast radius explorer to identify cascading risks.")

    elif nav == "PR Review Simulator":
        st.header("PR Review Simulator")
        st.write("Simulate posting a PR review and export markdown summary.")
        if st.button("Export Review Markdown"):
            try:
                md = generate_markdown_export(reviews)
                st.download_button("Download Review.md", md, file_name="sentinel_review.md")
            except Exception as e:
                st.error(f"Export failed: {e}")
        if reviews:
            try:
                j = export_json(reviews)
                c = export_csv(reviews)
                st.download_button("Download JSON", j, file_name="sentinel_review.json")
                st.download_button("Download CSV", c, file_name="sentinel_review.csv")
            except Exception as e:
                st.error(f"Failed to prepare exports: {e}")
            # auto-fix preview for first low-confidence finding
            shown = False
            for fpath, flist in reviews.items():
                for it in flist:
                    if it.get("confidence", 100) < 60 and not shown:
                        try:
                            code = open(fpath, "r", encoding="utf-8").read()
                        except Exception:
                            code = ""
                        fix = suggest_auto_fix(code, it)
                        if fix.get("diff"):
                            st.subheader("Auto-fix Preview")
                            st.code(fix.get("diff"))
                            st.download_button("Download Patch", fix.get("patch"), file_name="patch.py")
                            shown = True
                            break
                if shown:
                    break

    elif nav == "System Pipeline Monitor":
        st.header("System Pipeline Monitor")
        st.write("Live pipeline stages and timings")
        st.write(st.session_state.get("status", "idle"))


def generate_markdown_export(reviews: dict) -> str:
    parts = ["# SentinelAI Review\n"]
    for fpath, flist in reviews.items():
        parts.append(f"## {fpath}\n")
        for it in flist:
            parts.append(f"### {it.get('title')} - {it.get('severity').upper()}\n")
            parts.append(f"**Confidence:** {it.get('confidence')}\n")
            parts.append(it.get('description', '') + "\n")
            parts.append("---\n")
    return "\n".join(parts)


if __name__ == "__main__":
    main()
