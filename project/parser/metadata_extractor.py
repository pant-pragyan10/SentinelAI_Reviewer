"""High-level metadata extraction using AST parser outputs."""
from pathlib import Path
from typing import List
from .ast_parser import analyze_python_source
from .models import NodeMetadata
from ..logging_config import get_logger

logger = get_logger("sentinelai.parser.metadata")


def extract_metadata_for_file(path: Path) -> List[NodeMetadata]:
    """Extract metadata for all top-level nodes in a python source file."""
    try:
        meta = analyze_python_source(path)
        return meta
    except Exception:
        logger.exception("Error extracting metadata for %s", path)
        return []


def extract_metadata_for_files(paths: List[Path]) -> dict:
    results = {}
    for p in paths:
        results[str(p)] = extract_metadata_for_file(p)
    return results
