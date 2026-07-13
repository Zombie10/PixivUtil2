# -*- coding: utf-8 -*-
"""Track per-run download statistics and print a final summary."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PixivRunStats:
    started_at: float = field(default_factory=time.time)
    mode: str = ""
    ok: int = 0
    skipped: int = 0
    restricted: int = 0
    errors: int = 0
    artists_ok: int = 0
    artists_error: int = 0
    artists_skipped: int = 0
    downloaded_bytes: int = 0
    error_details: List[str] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_ok(self, n: int = 1) -> None:
        self.ok += n

    def record_skip(self, n: int = 1) -> None:
        self.skipped += n

    def record_restricted(self, n: int = 1) -> None:
        self.restricted += n

    def record_error(self, detail: str = "", n: int = 1) -> None:
        self.errors += n
        if detail:
            # Keep only the most recent details to avoid huge memory use.
            if len(self.error_details) < 50:
                self.error_details.append(detail)

    def record_artist_ok(self) -> None:
        self.artists_ok += 1

    def record_artist_error(self, detail: str = "") -> None:
        self.artists_error += 1
        if detail and len(self.error_details) < 50:
            self.error_details.append(detail)

    def record_artist_skipped(self) -> None:
        self.artists_skipped += 1

    def bump(self, key: str, n: int = 1) -> None:
        self.counters[key] += n

    def elapsed_seconds(self) -> float:
        return max(0.0, time.time() - self.started_at)

    def format_summary(self) -> str:
        elapsed = self.elapsed_seconds()
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            elapsed_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes:
            elapsed_str = f"{minutes}m {seconds}s"
        else:
            elapsed_str = f"{seconds}s"

        lines = [
            "========== Run Summary ==========",
            f"Mode            : {self.mode or 'n/a'}",
            f"Elapsed         : {elapsed_str}",
            f"Artists OK      : {self.artists_ok}",
            f"Artists errors  : {self.artists_error}",
            f"Artists skipped : {self.artists_skipped}",
            f"Items OK        : {self.ok}",
            f"Items skipped   : {self.skipped}",
            f"Items restricted: {self.restricted}",
            f"Items errors    : {self.errors}",
        ]
        if self.counters:
            for key in sorted(self.counters):
                lines.append(f"{key:16}: {self.counters[key]}")
        if self.error_details:
            lines.append("Recent errors:")
            for detail in self.error_details[-10:]:
                lines.append(f"  - {detail}")
        lines.append("=================================")
        return "\n".join(lines)

    def print_and_log(self, print_and_log_fn) -> None:
        summary = self.format_summary()
        for line in summary.splitlines():
            print_and_log_fn("info", line)


# Process-wide stats instance (reset at the start of a run).
_active_stats: Optional[PixivRunStats] = None


def reset_stats(mode: str = "") -> PixivRunStats:
    global _active_stats
    _active_stats = PixivRunStats(mode=mode)
    return _active_stats


def get_stats() -> PixivRunStats:
    global _active_stats
    if _active_stats is None:
        _active_stats = PixivRunStats()
    return _active_stats


def finish_stats(print_and_log_fn) -> Optional[PixivRunStats]:
    stats = get_stats()
    if stats.mode or stats.ok or stats.errors or stats.artists_ok or stats.artists_error:
        stats.print_and_log(print_and_log_fn)
    return stats
