import streamlit as st
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
# Sample repo lives under project/demo_presets/sample_repo
SAMPLE_REPO = ROOT / "project" / "demo_presets" / "sample_repo"


PRESETS = [
    {
        "key": "security",
        "name": "Security Risk Demo",
        "repo": "https://example.com/security-demo",
        "desc": "Showcases unsafe auth, verifier checks, and blast radius.",
    },
    {
        "key": "blast",
        "name": "Dependency Blast Radius Demo",
        "repo": "https://example.com/blast-demo",
        "desc": "Focuses on propagation and critical-path visualization.",
    },
]


def render_demo_presets():
    st.subheader("Demo Presets")
    for p in PRESETS:
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(f"**{p['name']}**")
            st.write(p["desc"])
        with cols[1]:
            if st.button(f"Load {p['name']}", key=f"load_preset_{p['key']}"):
                # Load offline sample repo and sample reviews into session state
                st.session_state['demo_preset'] = p['key']
                st.session_state['repo_path'] = str(SAMPLE_REPO)
                # build sample reviews
                reviews = {}
                base = str(SAMPLE_REPO)
                reviews[f"{base}/unsafe_auth.py"] = [
                    {
                        "issue_id": "ISSUE-001",
                        "category": "security",
                        "severity": "high",
                        "confidence": 92,
                        "file_path": f"{base}/unsafe_auth.py",
                        "line_start": 1,
                        "line_end": 6,
                        "title": "Unsafe JWT decode without verification",
                        "description": "JWT tokens are decoded without signature verification.",
                        "reasoning": "VerifierAgent: token decode uses options={'verify_signature': False}.",
                        "suggested_fix": "Use jwt.decode(token, key=PUBLIC_KEY, algorithms=['RS256'])",
                        "ast_evidence": [{"node_type": "Call", "snippet": "jwt.decode(...)", "line_start": 3, "line_end": 3}],
                    }
                ]
                reviews[f"{base}/token_service.py"] = [
                    {
                        "issue_id": "ISSUE-002",
                        "category": "security",
                        "severity": "medium",
                        "confidence": 85,
                        "file_path": f"{base}/token_service.py",
                        "line_start": 1,
                        "line_end": 6,
                        "title": "Call to parse_token without validation",
                        "description": "Token parsing delegated to unsafe_auth.parse_token which does not verify signature.",
                        "reasoning": "Chain impact from unsafe_auth -> token_service.",
                        "suggested_fix": "Validate token signatures before use.",
                        "ast_evidence": [{"node_type": "Call", "snippet": "parse_token(req)", "line_start": 1, "line_end": 2}],
                    }
                ]
                reviews[f"{base}/payment_api.py"] = [
                    {
                        "issue_id": "ISSUE-003",
                        "category": "security",
                        "severity": "low",
                        "confidence": 70,
                        "file_path": f"{base}/payment_api.py",
                        "line_start": 1,
                        "line_end": 6,
                        "title": "Payment flow uses token service without exception handling",
                        "description": "Missing robust error handling could expose payment errors.",
                        "reasoning": "Propagation: errors in token_service may surface here.",
                        "suggested_fix": "Add try/except and fallback behavior.",
                        "ast_evidence": [{"node_type": "FunctionDef", "snippet": "process_payment", "line_start": 1, "line_end": 4}],
                    }
                ]
                st.session_state['reviews'] = reviews
                st.session_state['open_tab'] = 'AST Intelligence'
                # experimental_rerun may not exist on all Streamlit versions; guard it
                try:
                    st.experimental_rerun()
                except Exception:
                    # fallback: rely on Streamlit reactivity on next user interaction
                    pass