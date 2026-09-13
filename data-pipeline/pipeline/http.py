from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from pipeline.config import raw_dir, settings

logger = logging.getLogger(__name__)


class HttpError(RuntimeError):
    pass


def request_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    cache_name: str | None = None,
) -> Any:
    cached = _read_cache(cache_name) if cache_name else None
    if cached is not None:
        return cached
    payload = request_text(url, params=params, headers=headers)
    data = json.loads(payload)
    if cache_name:
        _write_cache(cache_name, payload)
    return data


def request_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    merged = {"User-Agent": settings.user_agent}
    if headers:
        merged.update(headers)
    try:
        response = httpx.get(
            url,
            params=params,
            headers=merged,
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        )
    except httpx.HTTPError as exc:
        raise HttpError(f"HTTP request failed for {url}: {exc}") from exc
    if response.status_code >= 400:
        raise HttpError(f"{url} returned {response.status_code}: {response.text[:300]}")
    return response.text


def throttle_nvd() -> None:
    delay = settings.nvd_request_delay_seconds
    if delay > 0:
        logger.debug("NVD throttle: sleeping %.1fs", delay)
        time.sleep(delay)


def _cache_path(name: str) -> Path:
    return raw_dir() / name


def _read_cache(name: str) -> Any | None:
    path = _cache_path(name)
    if not path.exists():
        return None
    logger.info("Using cached raw file %s", path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cache(name: str, payload: str) -> None:
    path = _cache_path(name)
    path.write_text(payload, encoding="utf-8")
