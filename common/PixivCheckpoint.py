# -*- coding: utf-8 -*-
"""Simple JSON checkpoint for resumable batch jobs (FANBOX f1/f4/f5, etc.)."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional, Set


class PixivCheckpoint:
    def __init__(self, path: str | os.PathLike, mode: str = "fanbox"):
        self.path = Path(path)
        self.mode = mode
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self.meta: dict = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("mode") and data.get("mode") != self.mode:
                # Different mode on same path — start clean but keep file backup semantics simple.
                return
            self.completed = set(str(x) for x in data.get("completed", []))
            self.failed = set(str(x) for x in data.get("failed", []))
            self.meta = data.get("meta", {}) or {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.completed = set()
            self.failed = set()
            self.meta = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "mode": self.mode,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "completed": sorted(self.completed),
            "failed": sorted(self.failed),
            "meta": self.meta,
        }
        fd, tmp_name = tempfile.mkstemp(prefix=".checkpoint_", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def is_done(self, artist_id) -> bool:
        return str(artist_id) in self.completed

    def mark_done(self, artist_id, persist: bool = True) -> None:
        key = str(artist_id)
        self.completed.add(key)
        self.failed.discard(key)
        if persist:
            self.save()

    def mark_failed(self, artist_id, persist: bool = True) -> None:
        key = str(artist_id)
        self.failed.add(key)
        if persist:
            self.save()

    def filter_pending(self, ids: Iterable) -> List[str]:
        pending = []
        for item in ids:
            key = str(item)
            if key not in self.completed:
                pending.append(key)
        return pending

    def clear(self) -> None:
        self.completed.clear()
        self.failed.clear()
        self.meta = {}
        if self.path.is_file():
            try:
                self.path.unlink()
            except OSError:
                pass

    def remaining_count(self, ids: Iterable) -> int:
        return len(self.filter_pending(ids))
