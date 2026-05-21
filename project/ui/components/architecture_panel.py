import streamlit as st


def render_architecture_panel():
    st.subheader("Architecture Showcase")
    st.markdown(
        """
        **Pipeline Overview**

        GitHub Repo → AST Parser → Semantic Chunker → Reviewer Agents → Verifier → Consensus Engine → Confidence Calibration → Dashboard

        - **AST Parser:** Extracts syntax and function boundaries
        - **Semantic Chunker:** Groups code by semantics for LLM context
        - **Reviewer Agents:** Specialized agents (Security, Performance, Maintainability)
        - **VerifierAgent:** Confirms evidence and reduces hallucination
        - **Consensus & Confidence:** Combines reviewers into final scored issues
        """
    )
