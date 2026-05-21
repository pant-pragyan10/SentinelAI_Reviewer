"""Lightweight similarity engine stub with lazy loading.

This module avoids importing heavy dependencies at import-time. Callers should
use `get_engine()` to obtain an object that exposes `encode(texts)`.
"""
from typing import List, Optional
import os


class _StubEngine:
    def encode(self, texts: List[str], **kwargs):
        # naive fallback: return zero vectors
        return [[0.0] * 8 for _ in texts]


_ENGINE = None


def get_engine(model_name: str = "all-MiniLM-L6-v2"):
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    # By default, prefer the safe stub implementation to avoid importing heavy
    # libraries at runtime in demo/offline mode. Set ENABLE_HEAVY_EMBEDDINGS=1
    # in the environment to attempt loading SentenceTransformer (may be slow).
    enable = os.environ.get("ENABLE_HEAVY_EMBEDDINGS", "0") == "1"
    if not enable:
        _ENGINE = _StubEngine()
        return _ENGINE

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)

        class Engine:
            def __init__(self, m):
                self.m = m

            def encode(self, texts, **kwargs):
                return self.m.encode(texts, **kwargs)

        _ENGINE = Engine(model)
        return _ENGINE
    except Exception:
        # fallback to stub if anything fails
        _ENGINE = _StubEngine()
        return _ENGINE
