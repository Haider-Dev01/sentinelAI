from __future__ import annotations

import logging
import shutil
import subprocess
import uuid
from pathlib import Path

from app.config import settings
from app.services.scanners.process import run_process, which_or_raise

logger = logging.getLogger(__name__)


class GitResolutionError(ValueError):
    """Invalid repository URL or local path."""


def resolve_repo(
    *,
    url: str | None,
    path: str | None,
    work_dir: Path | None = None,
) -> tuple[Path, str, bool]:
    """Return (local_path, repo_name, is_ephemeral).

    Ephemeral clones (from URL) must be deleted by the caller after the scan.
    """
    if url:
        dest_root = work_dir or Path(settings.scan_work_dir)
        dest_root.mkdir(parents=True, exist_ok=True)
        dest = dest_root / str(uuid.uuid4())
        clone_repository(url, dest)
        return dest, _name_from_url(url), True

    if not path:
        raise GitResolutionError("Provide a git URL or a local path")

    local = Path(path).expanduser().resolve()
    if not local.exists() or not local.is_dir():
        raise GitResolutionError(f"Local path does not exist or is not a directory: {local}")
    return local, local.name, False


def clone_repository(url: str, dest: Path) -> None:
    which_or_raise("git")
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = run_process(
        ["git", "clone", "--depth", str(settings.clone_depth), url, str(dest)],
        timeout=settings.scan_timeout_seconds,
    )
    if result.returncode != 0:
        shutil.rmtree(dest, ignore_errors=True)
        detail = (result.stderr or result.stdout or "").strip()
        raise GitResolutionError(f"git clone failed for {url}: {detail}")
    logger.info("Cloned %s into %s", url, dest)


def read_head_sha(repo_path: Path) -> str | None:
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def cleanup_ephemeral(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _name_from_url(url: str) -> str:
    cleaned = url.rstrip("/").removesuffix(".git")
    return cleaned.rsplit("/", 1)[-1] or "repository"
