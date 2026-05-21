"""Repository file discovery and language detection."""
from pathlib import Path
from typing import List, Iterable
from ..logging_config import get_logger

logger = get_logger("sentinelai.github.scanner")


IGNORE_DIRS = {".git", "venv", "node_modules", "dist", "build", "__pycache__"}


PY_EXTENSIONS = {".py"}


def is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    return False


def discover_source_files(root: Path, extensions: Iterable[str] = PY_EXTENSIONS) -> List[Path]:
    """Recursively discover source files under `root`, respecting ignore rules."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            if is_ignored(p):
                continue
            if p.suffix in extensions:
                files.append(p)
    logger.info("Discovered %d source files under %s", len(files), root)
    return sorted(files)


def detect_languages(files: Iterable[Path]) -> List[str]:
    langs = set()
    for f in files:
        ext = f.suffix.lower()
        if ext == ".py":
            langs.add("python")
        elif ext in {".js", ".ts"}:
            langs.add("javascript/typescript")
        elif ext == ".java":
            langs.add("java")
        # extendable
    return sorted(langs)
