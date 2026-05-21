import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SAMPLE_REPO = ROOT / "demo_presets" / "sample_repo"


STEPS = [
    ("Clone Repository", "Load a repository into the platform."),
    ("Parse AST", "AST parser extracts functions, imports, and complexity metrics."),
    ("Extract Semantic Metadata", "Chunker and metadata extractors run."),
    ("Run Reviewer Agents", "Security, Performance, and Maintainability agents analyze code."),
    ("Verification & Consensus", "VerifierAgent checks evidence and Consensus consolidates findings."),
    ("Build Dependency Intelligence", "Dependency graph and centrality computed."),
    ("Visualize Risk Propagation", "Blast Radius and propagated risk displayed."),
    ("Generate Executive Summary", "Auto-generated executive summary for stakeholders."),
]


def render_walkthrough():
    st.subheader("Guided Walkthrough")
    step = st.session_state.get('walkthrough_step', 0)
    st.info(f"Step {step+1}/{len(STEPS)}: {STEPS[step][0]}")
    st.write(STEPS[step][1])

    cols = st.columns([1, 1, 1])
    if cols[0].button("Previous"):
        st.session_state['walkthrough_step'] = max(0, step - 1)
    if cols[1].button("Next"):
        st.session_state['walkthrough_step'] = min(len(STEPS) - 1, step + 1)
    if cols[2].button("Auto-run demo step"):
        # quick demo: load sample repo and advance to visualization steps
        st.session_state['repo_path'] = str(SAMPLE_REPO)
        # preserve existing reviews if present, else load demo preset reviews via demo_presets component
        st.session_state['open_tab'] = 'Repository Overview'
        st.session_state['walkthrough_step'] = step + 1 if step + 1 < len(STEPS) else step
        # `st.experimental_rerun` is not available on all Streamlit versions.
        # Call it if present, otherwise fall back to normal reactivity.
        try:
            rerun = getattr(st, "experimental_rerun", None)
            if callable(rerun):
                rerun()
        except Exception:
            # Avoid surfacing raw tracebacks in the UI; rely on Streamlit's
            # reactive model or next user interaction to pick up session state.
            pass
