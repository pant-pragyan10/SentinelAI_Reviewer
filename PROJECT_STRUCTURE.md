Project Structure (summary)

- project/
  - parser/: AST parsing, metadata extraction, chunking
  - agents/: reviewer agents and verifier
  - orchestrator.py: coordinates review pipeline
  - analysis/: propagation, hotspots, risk math
  - dedup/: deduplicator and similarity engine
  - embeddings/: embedding engine (stub / optional heavy)
  - ui/: Streamlit dashboard and components
  - github/: repo clone and scanner helpers
  - scripts/: startup checks and utilities

Key files:
- `project/ui/dashboard.py` — main demo app
- `project/orchestrator.py` — pipeline orchestration
- `project/analysis/propagation.py` — blast radius and propagation logic
