"""AST parsing utilities for Python source analysis."""
from __future__ import annotations
import ast
from pathlib import Path
from typing import Dict, List, Tuple
from ..logging_config import get_logger
from .models import NodeMetadata

logger = get_logger("sentinelai.parser.ast")


DANGEROUS_CALLS = {"eval", "exec", "os.system", "subprocess.Popen", "subprocess.call"}


def parse_file(path: Path) -> ast.AST:
    """Parse a Python file into an AST.

    Raises SyntaxError on invalid code.
    """
    text = path.read_text(encoding="utf-8")
    return ast.parse(text, filename=str(path))


def _extract_imports(node: ast.AST) -> List[str]:
    imports = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.append(n.module.split(".")[0])
    return sorted(set(imports))


def _cyclomatic_hint(node: ast.AST) -> int:
    # crude heuristic: count branching and boolean ops
    count = 0
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp, ast.And, ast.Or, ast.IfExp)):
            count += 1
    return max(1, count + 1)


class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self, tree: ast.AST):
        self.tree = tree
        self.metadata: List[NodeMetadata] = []

    def analyze(self) -> List[NodeMetadata]:
        self.visit(self.tree)
        return self.metadata

    def visit_FunctionDef(self, node: ast.FunctionDef):
        md = self._node_to_metadata(node, "function")
        self.metadata.append(md)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        md = self._node_to_metadata(node, "async_function")
        self.metadata.append(md)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        md = self._node_to_metadata(node, "class")
        md.inheritance = [self._expr_to_str(b) for b in node.bases]
        self.metadata.append(md)
        self.generic_visit(node)

    def _node_to_metadata(self, node: ast.AST, typ: str) -> NodeMetadata:
        start = getattr(node, "lineno", 0)
        end = getattr(node, "end_lineno", start)
        imports = _extract_imports(node)
        doc = ast.get_docstring(node)
        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
        nested_loop_depth = self._nested_loop_depth(node)
        dangerous = self._find_dangerous_calls(node)
        cyclomatic = _cyclomatic_hint(node)
        decorators = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            decorators = [self._expr_to_str(d) for d in getattr(node, "decorator_list", [])]

        return NodeMetadata(
            name=getattr(node, "name", "<module>"),
            type=typ,
            line_start=start,
            line_end=end,
            imports_used=imports,
            has_try_except=has_try,
            nested_loop_depth=nested_loop_depth,
            dangerous_calls=dangerous,
            cyclomatic_hint=cyclomatic,
            docstring=doc,
            decorators=decorators,
        )

    def _nested_loop_depth(self, node: ast.AST) -> int:
        max_depth = 0

        def helper(n: ast.AST, depth: int):
            nonlocal max_depth
            if isinstance(n, (ast.For, ast.While)):
                depth += 1
                max_depth = max(max_depth, depth)
            for c in ast.iter_child_nodes(n):
                helper(c, depth)

        helper(node, 0)
        return max_depth

    def _find_dangerous_calls(self, node: ast.AST) -> List[str]:
        found = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                func = self._expr_to_str(n.func)
                for d in DANGEROUS_CALLS:
                    if func and d in func:
                        found.add(d)
        return sorted(found)

    def _expr_to_str(self, expr: ast.AST) -> str:
        try:
            if isinstance(expr, ast.Name):
                return expr.id
            elif isinstance(expr, ast.Attribute):
                return self._expr_to_str(expr.value) + "." + expr.attr
            elif isinstance(expr, ast.Call):
                return self._expr_to_str(expr.func)
            elif isinstance(expr, ast.Constant):
                return repr(expr.value)
            elif isinstance(expr, ast.Subscript):
                return self._expr_to_str(expr.value)
            else:
                return ast.unparse(expr) if hasattr(ast, "unparse") else type(expr).__name__
        except Exception:
            return "<expr>"


def analyze_python_source(path: Path) -> List[NodeMetadata]:
    """Parse and analyze a python source file, returning metadata for top-level nodes."""
    tree = parse_file(path)
    analyzer = ASTAnalyzer(tree)
    try:
        metadata = analyzer.analyze()
        logger.debug("Analyzed %s -> %d metadata nodes", path, len(metadata))
        return metadata
    except Exception:
        logger.exception("Failed to analyze %s", path)
        raise
