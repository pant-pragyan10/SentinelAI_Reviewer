"""Repository ingestion using GitPython."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import shutil
import re
import git
from git import Repo, GitCommandError
from . import __name__ as _mod
from ..logging_config import get_logger
from ..config import settings

logger = get_logger("sentinelai.github.clone")


GITHUB_URL_RE = re.compile(r"^(https?://)?(www\.)?github\.com/[^/]+/[^/]+(?:(?:\.git))?$")


@dataclass
class CloneResult:
    path: Path
    repo: Optional[Repo]


def validate_github_url(url: str) -> bool:
    return bool(GITHUB_URL_RE.match(url.strip()))


def get_repo_path(url: str) -> Path:
    name = url.rstrip("/\n").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    base = settings.REPO_BASE_PATH
    base.mkdir(parents=True, exist_ok=True)
    return base / name


def clone_repo(url: str, force: bool = False, timeout: Optional[int] = None) -> CloneResult:
    """Clone a public GitHub repository to the local `REPO_BASE_PATH`.

    - Validates the URL.
    - Avoids re-cloning unless `force` is True.
    - Returns a CloneResult with local path and Repo object.
    """
    timeout = timeout or settings.CLONE_TIMEOUT
    if not validate_github_url(url):
        logger.error("Invalid GitHub URL: %s", url)
        raise ValueError("Invalid GitHub URL")

    dest = get_repo_path(url)
    if dest.exists():
        if force:
            logger.info("Removing existing repo at %s", dest)
            shutil.rmtree(dest)
        else:
            try:
                repo = Repo(dest)
                logger.info("Repository already cloned at %s", dest)
                return CloneResult(dest, repo)
            except Exception:
                logger.warning("Path exists but is not a git repo, cleaning: %s", dest)
                shutil.rmtree(dest)

    try:
        logger.info("Cloning %s -> %s", url, dest)
        repo = Repo.clone_from(url, dest, multi_options=[f"--depth=1"], timeout=timeout)
        logger.info("Clone complete: %s", dest)
        return CloneResult(dest, repo)
    except GitCommandError as e:
        logger.exception("Git clone failed: %s", e)
        raise


def cleanup_repo(path: Path) -> bool:
    """Remove a local repo clone. Returns True when removed."""
    try:
        if path.exists():
            shutil.rmtree(path)
            logger.info("Removed %s", path)
            return True
        return False
    except Exception:
        logger.exception("Failed to remove %s", path)
        return False
