import streamlit as st
from typing import Dict

SEVERITY_COLORS = {
    "critical": "#e10600",
    "high": "#ff7a00",
    "medium": "#ffd32a",
    "low": "#2b9af3",
    "info": "#9aa0a6",
}


def render_issue_card(issue: Dict, file_path: str = None):
    title = issue.get("title")
    severity = issue.get("severity")
    confidence = issue.get("confidence")
    color = SEVERITY_COLORS.get(severity, "#9aa0a6")

    st.markdown(f"<div style='border-left:4px solid {color}; padding:8px'>", unsafe_allow_html=True)
    st.subheader(f"{title}")
    st.write(f"**File:** {file_path} | **Severity:** {severity} | **Confidence:** {confidence}%")
    # Jump-to-AST button
    if file_path and issue.get('line_start'):
        if st.button("Jump to AST", key=f"jump_{issue.get('issue_id', title)}"):
            st.session_state['selected_file'] = file_path
            st.session_state['selected_node_line'] = issue.get('line_start')
            st.session_state['selected_finding'] = issue
    with st.expander("Details"):
        st.write(issue.get("description"))
        st.write("**Reasoning**")
        st.code(issue.get("reasoning", ""))
        st.write("**Suggested Fix**")
        st.code(issue.get("suggested_fix", ""))
        st.write("**AST Evidence**")
        st.json(issue.get("ast_evidence", []))
    st.markdown("</div>", unsafe_allow_html=True)
