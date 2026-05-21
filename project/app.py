"""Entrypoint scripts and small helpers for repository inspection."""
from pathlib import Path
from .github.clone_repo import clone_repo
from .github.repo_scanner import discover_source_files
from .parser.metadata_extractor import extract_metadata_for_files
from .parser.chunk_builder import build_chunks_for_file
from .parser.dependency_graph import build_dependency_graph
from .logging_config import get_logger
from .config import settings

logger = get_logger("sentinelai.app")


def inspect_repository(url: str, force: bool = False):
    res = clone_repo(url, force=force)
    repo_path = res.path
    py_files = discover_source_files(repo_path)
    metadata = extract_metadata_for_files(py_files)
    chunks = {str(p): build_chunks_for_file(p) for p in py_files}
    graph = build_dependency_graph(py_files)
    return {
        "repo_path": str(repo_path),
        "files": [str(p) for p in py_files],
        "metadata_summary": {k: len(v) for k, v in metadata.items()},
        "chunks_summary": {k: len(v) for k, v in chunks.items()},
        "graph_nodes": graph.number_of_nodes(),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="GitHub repository URL to inspect")
    args = parser.parse_args()
    out = inspect_repository(args.url)
    print(out)
