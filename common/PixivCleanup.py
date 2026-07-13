# -*- coding: utf-8 -*-
"""Housekeeping helpers for url dumps and rotated log files."""
from __future__ import annotations

import glob
import os
import time
from pathlib import Path
from typing import Iterable, List, Tuple


def _safe_unlink(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except OSError:
        return False


def cleanup_url_lists(
    directory: str | os.PathLike,
    keep_days: int = 30,
    pattern: str = "url_list_*.txt",
) -> Tuple[int, List[str]]:
    """Delete url_list_*.txt files older than keep_days. Returns (count, paths)."""
    if keep_days is None or keep_days < 0:
        return 0, []
    base = Path(directory)
    if not base.is_dir():
        return 0, []

    cutoff = time.time() - (keep_days * 86400)
    removed: List[str] = []
    for path in base.glob(pattern):
        if not path.is_file():
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            if _safe_unlink(path):
                removed.append(str(path))
    return len(removed), removed


def cleanup_old_logs(
    directory: str | os.PathLike,
    keep_count: int = 10,
    patterns: Iterable[str] = ("pixivutil.log.*", "run_z.log.*", "run_f1.log.*"),
) -> Tuple[int, List[str]]:
    """
    Keep the newest `keep_count` rotated log files matching each pattern.
    Does not delete the active log (e.g. pixivutil.log without suffix).
    """
    if keep_count is None or keep_count < 0:
        return 0, []
    base = Path(directory)
    if not base.is_dir():
        return 0, []

    removed: List[str] = []
    for pattern in patterns:
        files = [p for p in base.glob(pattern) if p.is_file()]
        # Sort by mtime descending (newest first).
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files[keep_count:]:
            if _safe_unlink(path):
                removed.append(str(path))
    return len(removed), removed


def run_startup_cleanup(
    directory: str | os.PathLike,
    url_list_keep_days: int = 30,
    log_keep_count: int = 10,
) -> dict:
    """Run standard cleanup and return a small report dict."""
    url_count, url_paths = cleanup_url_lists(directory, keep_days=url_list_keep_days)
    log_count, log_paths = cleanup_old_logs(directory, keep_count=log_keep_count)
    return {
        "url_lists_removed": url_count,
        "url_list_paths": url_paths,
        "logs_removed": log_count,
        "log_paths": log_paths,
    }
