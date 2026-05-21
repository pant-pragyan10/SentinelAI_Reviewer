SentinelAI Reviewer — concise evaluator-ready README

This repository contains a Streamlit-based code-review demo application focused on AST-aware analysis, explainability, and dependency-risk visualization.

Quick start (demo/offline):

```bash
python project/scripts/startup_check.py
streamlit run project/ui/dashboard.py --server.port 8501
```

Dependencies:
- Install runtime deps: `pip install -r requirements.txt`
- Optional (interactive graphs / heavy embeddings):
  - `pip install plotly streamlit-plotly-events` (interactive graphs)
  - `pip install "sentence-transformers>=2.2.0" torch` (optional heavy embeddings)

Configuration:
- Use `.env` or environment variables. See `project/.env.example` for keys expected by the app (do NOT commit secrets).
- To run in demo/offline mode keep `LLM_PROVIDER` and provider keys unset.
- To enable heavy embeddings set `ENABLE_HEAVY_EMBEDDINGS=1`.

What to expect:
- The app is demo-ready: core workflows are deterministic with optional heavy components behind feature flags.
- If optional packages are missing, the UI falls back to static messages and preserves stability.

Structure (key folders):
- `project/ui/` — Streamlit dashboard and UI components
- `project/parser/` — AST parsing and metadata extraction
- `project/analysis/` — dependency graph and propagation analysis
- `project/agents/` — reviewer agents and orchestration
- `project/embeddings/` — embedding adapter (lightweight stub by default)

Contact:
- For issues or contributions, open a GitHub issue or PR. Do not commit secrets.

This README is intentionally concise for evaluator use.
