from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Semgrep/gitleaks/osv-scanner use 0 (clean) and 1 (findings) as success.
_SUCCESS_CODES = {0, 1}


class ScannerExecutionError(RuntimeError):
    """Raised when a scanner binary is missing or exits with an unexpected error."""


def which_or_raise(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise ScannerExecutionError(
            f"{binary} is not installed or not on PATH. "
            "Install the scanner or run the API in the project Docker image."
        )
    return path


def run_process(
    command: list[str],
    *,
    cwd: str | Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = timeout or settings.scan_timeout_seconds
    logger.info("Running scanner command: %s", " ".join(command))
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScannerExecutionError(
            f"Command timed out after {timeout}s: {' '.join(command)}"
        ) from exc


def ensure_success(result: subprocess.CompletedProcess[str], scanner: str) -> None:
    if result.returncode in _SUCCESS_CODES:
        return
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    detail = stderr or stdout or f"exit {result.returncode}"
    raise ScannerExecutionError(f"{scanner} failed: {detail}")


def load_json(payload: str) -> Any:
    text = payload.strip()
    if not text:
        return None
    return json.loads(text)


def load_json_file(path: Path) -> Any:
    if not path.exists() or path.stat().st_size == 0:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def relativize(file_path: str, repo_root: Path) -> str:
    raw = Path(file_path)
    try:
        resolved = raw.resolve() if raw.is_absolute() else (repo_root / raw).resolve()
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except (OSError, ValueError):
        return Path(file_path).as_posix()
