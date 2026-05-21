import streamlit as st


def render_demo_script(reviews, hotspots=None, propagated=None):
    st.subheader("Demo Script Helper")
    tabs = st.tabs(["2 Minute Demo", "Technical Deep Dive", "Architecture Summary"])

    with tabs[0]:
        st.write("A concise 2-minute script to highlight core features:")
        st.markdown("- Show Repository Overview and overall health\n- Open AST Intelligence and highlight unsafe_auth.py\n- Click graph node to show blast radius and impacted modules\n- Open Agent Reasoning to explain findings\n- Export a summary via PR Review Simulator")

    with tabs[1]:
        st.write("Technical talking points:")
        st.markdown("- AST-based analysis with cyclomatic hints\n- Multi-agent reviewers with VerifierAgent\n- Semantic deduplication and confidence calibration\n- Risk propagation across dependency graphs")

    with tabs[2]:
        st.write("Architecture summary bullets for executives:")
        st.markdown("- Ingest: Git cloning and file discovery\n- Parse: AST parsing + semantic chunking\n- Analyze: Agent-based reviews + verifier\n- Synthesize: Consensus + confidence calibration\n- Visualize: AST explorer, blast radius, risk analytics")
