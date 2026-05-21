"""Semantic chunking: group code by function, class, and module-level logical units."""
from pathlib import Path
from typing import List, Dict, Any
from .ast_parser import parse_file
from ..logging_config import get_logger

logger = get_logger("sentinelai.parser.chunks")


def build_chunks_for_file(path: Path) -> List[Dict[str, Any]]:
    tree = parse_file(path)
    chunks = []
    # Module-level chunk
    module_chunk = {
        "type": "module",
        "name": path.stem,
        "start": 1,
        "end": getattr(tree, "end_lineno", None) or None,
        "code": path.read_text(encoding="utf-8"),
    }
    chunks.append(module_chunk)

    for node in tree.body:
        if hasattr(node, "lineno"):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            code_lines = path.read_text(encoding="utf-8").splitlines()
            snippet = "\n".join(code_lines[start - 1 : end]) if end and start else ""
            kind = node.__class__.__name__
            chunks.append({
                "type": kind,
                "name": getattr(node, "name", f"{kind}@{start}"),
                "start": start,
                "end": end,
                "code": snippet,
            })

    logger.debug("Built %d chunks for %s", len(chunks), path)
    return chunks
