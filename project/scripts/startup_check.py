"""Lightweight startup/env validation checks.

This script validates required environment variables and reports friendly
messages. It intentionally avoids importing heavy libraries.
"""
import os
from pathlib import Path

REQUIRED = [
    ("LLM_PROVIDER", "Primary LLM provider (groq|openai)"),
    ("MODEL_NAME", "Model to use for LLM requests"),
]


def check_env():
    print("Startup environment checks:")
    ok = True
    for var, desc in REQUIRED:
        val = os.environ.get(var)
        if not val:
            print(f" - MISSING: {var} ({desc})")
            ok = False
        else:
            print(f" - OK: {var} = {val}")

    # check for GROQ key optionally
    if not os.environ.get("GROQ_API_KEY"):
        print(" - WARN: GROQ_API_KEY not set. Demo/offline mode will be used.")

    # check cache dir
    cd = Path(os.environ.get("CACHE_DIR", ".cache"))
    try:
        cd.mkdir(parents=True, exist_ok=True)
        print(f" - OK: cache dir {cd.resolve()}")
    except Exception as e:
        print(f" - FAIL: cannot create cache dir {cd}: {e}")
        ok = False

    if ok:
        print("Startup checks passed (non-exhaustive).")
    else:
        print("Startup checks found issues. Set required env vars listed above.")


if __name__ == "__main__":
    check_env()
