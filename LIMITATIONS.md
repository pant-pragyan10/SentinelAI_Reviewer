Known Limitations & Future Improvements

Limitations
- The embedding stub is deterministic and not semantically accurate — it is intentionally used for demo/offline stability.
- Heavy embedding stacks (`sentence-transformers`, `torch`) are optional and may add startup latency and platform-specific requirements.
- Interactive dependency graphs require `plotly` and `streamlit-plotly-events` to be installed.

Future improvements
- Background initialization of heavy models to keep fast startup while enabling full semantics.
- Docker images for CPU / GPU reproducible runs.
- Expanded integration tests and CI to validate multi-agent consensus behaviors.
