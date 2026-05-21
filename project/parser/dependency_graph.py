"""Dependency graph extraction using networkx."""
from pathlib import Path
from typing import List, Tuple
import networkx as nx
import ast
from .ast_parser import parse_file
from ..logging_config import get_logger

logger = get_logger("sentinelai.parser.depgraph")


def build_dependency_graph(paths: List[Path]) -> nx.DiGraph:
    """Build a dependency graph across given python files.

    Nodes are module:file, classes and functions. Edges represent imports and calls.
    """
    g = nx.DiGraph()
    for p in paths:
        try:
            tree = parse_file(p)
        except Exception:
            logger.exception("Failed to parse %s", p)
            continue

        module_name = p.stem
        g.add_node(module_name, type="module", path=str(p))

        for node in tree.body:
            # Try to capture defs
            if hasattr(node, "name"):
                node_name = f"{module_name}.{getattr(node, 'name')}"
                g.add_node(node_name, type=node.__class__.__name__)
                g.add_edge(module_name, node_name, type="defines")

        # Imports
        for n in parse_imports(tree):
            g.add_edge(module_name, n, type="imports")

    logger.info("Built dependency graph with %d nodes", g.number_of_nodes())
    return g


def parse_imports(tree) -> List[str]:
    imports = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.append(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.append(n.module.split(".")[0])
    return sorted(set(imports))
