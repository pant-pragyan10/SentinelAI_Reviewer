#!/usr/bin/env bash
set -euo pipefail

echo "Running startup checks..."
python project/scripts/startup_check.py || true

echo "Starting Streamlit UI (http://localhost:8501)"
streamlit run project/ui/dashboard.py
