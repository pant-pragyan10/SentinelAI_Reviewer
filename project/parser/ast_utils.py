"""Utilities to build an AST tree representation with metadata for the UI."""
from pathlib import Path
import ast
from typing import Any, Dict, List, Tuple
from collections import deque
from .ast_parser import _cyclomatic_hint, DANGEROUS_CALLS


def _node_id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx}"


def build_ast_tree(path: Path) -> List[Dict[str, Any]]:
    """Parse python file and build a hierarchical AST node list suitable for UI exploration.

    Returns a list of node dicts with keys: id, type, name, line_start, line_end, depth, children, cyclomatic_hint, dangerous_calls, decorators, child_count
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))

    nodes: List[Dict[str, Any]] = []
    counter = 0

    def add_node(n_type: str, name: str, node_obj: ast.AST, depth: int, children: List[Dict]):
        nonlocal counter
        nid = _node_id(n_type.lower(), counter)
        counter += 1
        start = getattr(node_obj, "lineno", None)
        end = getattr(node_obj, "end_lineno", start)
        decorators = []
        if hasattr(node_obj, "decorator_list"):
            decorators = [ast.unparse(d) if hasattr(ast, "unparse") else "<decorator>" for d in node_obj.decorator_list]
        cyclo = _cyclomatic_hint(node_obj)
        dangerous = []
        for c in ast.walk(node_obj):
            if isinstance(c, ast.Call):
                try:
                    func = ast.unparse(c.func) if hasattr(ast, "unparse") else ""
                except Exception:
                    func = ""
                for d in DANGEROUS_CALLS:
                    if d in func:
                        dangerous.append(d)
        node = {
            "id": nid,
            "type": n_type,
            "name": name,
            "line_start": start,
            "line_end": end,
            "depth": depth,
            "cyclomatic_hint": cyclo,
            "dangerous_calls": sorted(set(dangerous)),
            "decorators": decorators,
            "child_count": len(children),
            "children": children,
        }
        return node

    # Build top-level categories
    imports = []
    classes = []
    functions = []
    others = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            name = ast.unparse(node) if hasattr(ast, "unparse") else "import"
            imports.append(add_node("Import", name, node, 1, []))
        elif isinstance(node, ast.ClassDef):
            # build methods
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(add_node("Method", getattr(child, "name", "<anon>"), child, 2, []))
            classes.append(add_node("Class", getattr(node, "name", "<anon>"), node, 1, methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(add_node("Function", getattr(node, "name", "<anon>"), node, 1, []))
        else:
            others.append(add_node(node.__class__.__name__, node.__class__.__name__, node, 1, []))

    # Dangerous calls at module level
    dangerous_calls = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            try:
                func = ast.unparse(n.func) if hasattr(ast, "unparse") else ""
            except Exception:
                func = ""
            for d in DANGEROUS_CALLS:
                if d in func:
                    start = getattr(n, "lineno", None)
                    end = getattr(n, "end_lineno", start)
                    dangerous_calls.append({"id": _node_id("danger", len(dangerous_calls)), "type": "DangerousCall", "name": func, "line_start": start, "line_end": end, "depth": 1, "cyclomatic_hint": 0, "dangerous_calls": [d], "decorators": [], "child_count": 0, "children": []})

    root = [
        {"id": "imports", "type": "Category", "name": "Imports", "children": imports},
        {"id": "classes", "type": "Category", "name": "Classes", "children": classes},
        {"id": "functions", "type": "Category", "name": "Functions", "children": functions},
        {"id": "others", "type": "Category", "name": "Others", "children": others},
        {"id": "dangerous", "type": "Category", "name": "Dangerous Calls", "children": dangerous_calls},
    ]
    return root


def build_ast_tree_cached(path_str: str) -> List[Dict[str, Any]]:
    """Cached wrapper around build_ast_tree using file path string."""
    return _build_ast_tree_cached(path_str)


from functools import lru_cache


@lru_cache(maxsize=64)
def _build_ast_tree_cached(path_str: str) -> List[Dict[str, Any]]:
    return build_ast_tree(Path(path_str))
