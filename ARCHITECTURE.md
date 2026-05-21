Concise Architecture Explanation

The pipeline is layered for clarity and auditability:

1. Ingestion: `project/github/clone_repo.py` clones a repo (or demo preset).
2. Parsing: `project/parser/` constructs ASTs and semantic chunks for LLM context.
3. Agents: multiple specialist agents analyze chunks in parallel. Each agent returns structured `ReviewIssue` objects and raw reasoning.
4. Verifier & Consensus: `VerifierAgent` validates evidence; consensus reduces hallucination and aggregates confidences.
5. Analysis: `project/analysis/` computes dependency graphs, propagates risk scores, and computes blast radius.
6. UI: `project/ui/` shows AST trees, risk heatmaps, propagation visualizations, and explainability traces.

Design priorities: deterministic demo behavior, explainability, and safe fallbacks for heavy ML dependencies.
