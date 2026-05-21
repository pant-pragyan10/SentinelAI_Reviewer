from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from ..schemas import ReviewIssue, ASTEvidence
from ..logging_config import get_logger
from ..embeddings.similarity_engine import get_engine

logger = get_logger("sentinelai.dedup.deduplicator")


class Deduplicator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.85):
        # lazy-load heavy model only when needed
        self._model_name = model_name
        self.model = None
        self.threshold = threshold

    def deduplicate(self, issues: List[ReviewIssue]) -> List[ReviewIssue]:
        if not issues:
            return []
        texts = [f.title + "\n" + f.description for f in issues]
        if self.model is None:
            try:
                self.model = get_engine(self._model_name)
            except Exception:
                logger.warning("Failed to load embedding engine, skipping deduplication")
                return issues

        # use engine.encode; ensure numpy arrays expected by cosine_similarity
        embeds = self.model.encode(texts, convert_to_numpy=True) if hasattr(self.model, "encode") else self.model.encode(texts)
        sim = cosine_similarity(embeds)
        merged = []
        used = set()
        for i, issue in enumerate(issues):
            if i in used:
                continue
            group = [i]
            for j in range(i + 1, len(issues)):
                if sim[i, j] >= self.threshold:
                    group.append(j)
                    used.add(j)
            if len(group) == 1:
                merged.append(issue)
            else:
                # merge group
                base = issues[group[0]]
                for idx in group[1:]:
                    other = issues[idx]
                    base.ast_evidence.extend(other.ast_evidence or [])
                    base.confidence = max(base.confidence, other.confidence)
                    base.tags = list(set(base.tags + other.tags))
                merged.append(base)
        logger.info("Deduplicated %d -> %d issues", len(issues), len(merged))
        return merged
