import streamlit as st
from typing import List, Dict, Any
from pathlib import Path
from project.ui.components.code_view import render_code_snippet_with_highlight
from project.parser.ast_utils import build_ast_tree
from project.analysis.risk import compute_node_risks
from project.schemas import ReviewIssue


def _render_node(node: Dict[str, Any], reviews_index: Dict[int, List[Dict]], node_risks: Dict[str, Dict], parent_expanded: bool = False):
    risk_info = node_risks.get(node.get('id'), {})
    risk = risk_info.get('risk') if risk_info else None
    color = risk_info.get('color') if risk_info else '#9aa0a6'
    label = f"{node.get('name')} [{node.get('type')}]"
    badge_html = f" <span style='background:{color}; padding:3px 8px; border-radius:6px; color:#fff; font-size:12px; margin-left:8px'>{int(risk) if risk is not None else ''}</span>"
    with st.expander(label + badge_html, expanded=False):
        cols = st.columns([3, 1])
        with cols[0]:
            st.write(f"**Type:** {node.get('type')}")
            st.write(f"**Lines:** {node.get('line_start')} - {node.get('line_end')}")
            st.write(f"**Cyclomatic hint:** {node.get('cyclomatic_hint')}")
            st.write(f"**Dangerous calls:** {', '.join(node.get('dangerous_calls', []))}")
            if risk_info:
                st.markdown(f"**Risk:** {risk_info.get('risk')}  \n**Confidence:** {risk_info.get('confidence')}  \n**Linked issues:** {risk_info.get('issue_count')}")
            if st.button("Inspect node", key=f"inspect_{node.get('id')}"):
                st.session_state['selected_node'] = node
        with cols[1]:
            st.write(f"Children: {node.get('child_count', 0)}")
        # Render children recursively
        for c in node.get('children', []):
            _render_node(c, reviews_index, node_risks, parent_expanded)


def render_ast_explorer(file_path: str, reviews: List[Dict[str, Any]]):
    try:
        p = Path(file_path)
        st.sidebar.markdown(f"**File:** {p.name}")
        from project.parser.ast_utils import build_ast_tree_cached
        tree = build_ast_tree_cached(str(p))
    except Exception as e:
        st.error(f"Failed to load AST for file: {e}")
        return

    # Build review index by line spans
    reviews_index = {}
    for r in reviews:
        try:
            start = r.get('line_start', 0)
            lst = reviews_index.setdefault(start, [])
            lst.append(r)
        except Exception:
            continue

    # compute node risks (module centrality placeholder)
    module_centrality = {Path(file_path).stem: 0.0}
    node_risks = compute_node_risks(tree, reviews, module_centrality, Path(file_path).stem)

    # Auto-select node if session state indicates a line to focus
    try:
        sel_line = st.session_state.get('selected_node_line')
        sel_file = st.session_state.get('selected_file')
        if sel_line and sel_file and Path(sel_file).resolve() == p.resolve():
            # find node that covers this line
            for category in tree:
                for node in category.get('children', []):
                    ls = node.get('line_start')
                    le = node.get('line_end') or ls
                    if ls and le and ls <= sel_line <= le:
                        st.session_state['selected_node'] = node
                        break
                if st.session_state.get('selected_node'):
                    break
    except Exception:
        # Do not raise; fallback to file-level view
        st.info("Could not auto-select AST node; showing file-level view.")

    left, right = st.columns([1, 2])
    with left:
        st.subheader("AST Tree")
        show_only_risky = st.checkbox("Show only risky nodes", value=False)
        risk_threshold = st.slider("Risk threshold", 0, 100, 30)
        for node in tree:
            # top-level categories
            with st.expander(node.get('name'), expanded=False):
                for child in node.get('children', []):
                    nr = node_risks.get(child.get('id'), {})
                    if show_only_risky and nr.get('risk', 0) < risk_threshold:
                        continue
                    _render_node(child, reviews_index, node_risks)

    with right:
        st.subheader("Node Inspector")
        selected = st.session_state.get('selected_node')
        if selected:
            st.markdown(f"**{selected.get('name')}** — {selected.get('type')}")
            st.write(f"Lines: {selected.get('line_start')} - {selected.get('line_end')}")
            st.write(f"Cyclomatic hint: {selected.get('cyclomatic_hint')}")
            st.write(f"Dangerous calls: {', '.join(selected.get('dangerous_calls', []))}")
            # show linked reviews
            linked = []
            for r in reviews:
                ls = r.get('line_start')
                le = r.get('line_end')
                if ls and le and selected.get('line_start') and selected.get('line_end'):
                    if not (le < selected.get('line_start') or ls > selected.get('line_end')):
                        linked.append(r)
            if linked:
                st.subheader("Linked Findings")
                for l in linked:
                    st.write(f"- {l.get('title')} ({l.get('confidence')}%)")
            # render source with highlights
            try:
                code = p.read_text(encoding='utf-8')
                hl_map = {}
                if selected.get('line_start'):
                    start = selected.get('line_start')
                    end = selected.get('line_end') or start
                    # get risk color for this node using precomputed risks
                    node_risks = compute_node_risks(tree, reviews, {Path(file_path).stem: 0.0}, Path(file_path).stem)
                    risk_info = node_risks.get(selected.get('id'), {})
                    color = risk_info.get('color') if risk_info else 'rgba(255,200,0,0.15)'
                    for ln in range(start, end + 1):
                        hl_map[ln] = color
                render_code_snippet_with_highlight(code, highlight_map=hl_map)
            except Exception as e:
                st.error(f"Failed to load source: {e}")
        else:
            st.info("Select a node to inspect its details and source.")
