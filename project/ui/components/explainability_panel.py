import streamlit as st
from pathlib import Path


def render_explainability_panel():
    sel_mod = st.session_state.get('selected_module')
    sel_file = st.session_state.get('selected_file')
    sel_node = st.session_state.get('selected_node')
    sel_finding = st.session_state.get('selected_finding')

    with st.expander('Unified Explainability', expanded=True):
        if not sel_mod and not sel_file and not sel_finding:
            st.write('No selection. Click a module or issue to begin a trace.')
            return

        if sel_mod:
            st.markdown(f"**Selected Module:** {sel_mod}")
        if sel_file:
            st.markdown(f"**Selected File:** {Path(sel_file).name}")
        if sel_node:
            st.markdown(f"**Selected Function/Node:** {sel_node.get('name')} ({sel_node.get('type')})")
            st.write(f"Lines: {sel_node.get('line_start')} - {sel_node.get('line_end')}")
        if sel_finding:
            st.markdown("**Detected Issue:**")
            st.write(f"- {sel_finding.get('title')} — Severity: {sel_finding.get('severity')} — Confidence: {sel_finding.get('confidence')}%")
            st.write("**AST Evidence:**")
            st.json(sel_finding.get('ast_evidence', []))

        # propagation summary if available
        propagated = st.session_state.get('propagated_map')
        if propagated and sel_mod:
            impact = propagated.get(sel_mod, 0.0)
            st.write(f"**Propagated Impact (score):** {impact:.1f}")

        # quick action buttons
        cols = st.columns(3)
        if cols[0].button('Jump to AST'):
            st.session_state['open_tab'] = 'AST Intelligence'
        if cols[1].button('Show Blast Radius'):
            st.session_state['open_tab'] = 'Risk Analytics'
        if cols[2].button('Filter Issues') and sel_mod:
            st.session_state['issue_filter_module'] = sel_mod
