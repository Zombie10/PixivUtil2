# -*- coding: utf-8 -*-
import os
import tempfile
import time
import unittest
from pathlib import Path

from common.PixivCheckpoint import PixivCheckpoint
from common.PixivCleanup import cleanup_old_logs, cleanup_url_lists, run_startup_cleanup
from common.PixivRunStats import reset_stats


class TestRunStats(unittest.TestCase):
    def test_summary_counts(self):
        stats = reset_stats(mode="unit")
        stats.record_ok(2)
        stats.record_skip()
        stats.record_restricted()
        stats.record_error("boom")
        stats.record_artist_ok()
        stats.record_artist_error("artist fail")
        text = stats.format_summary()
        self.assertIn("Mode            : unit", text)
        self.assertIn("Items OK        : 2", text)
        self.assertIn("Items skipped   : 1", text)
        self.assertIn("Items restricted: 1", text)
        self.assertIn("Items errors    : 1", text)
        self.assertIn("boom", text)


class TestCheckpoint(unittest.TestCase):
    def test_mark_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cp.json"
            cp = PixivCheckpoint(path, mode="fanbox_supporting")
            cp.mark_done("a1")
            cp.mark_done("a2")
            cp.mark_failed("a3")

            cp2 = PixivCheckpoint(path, mode="fanbox_supporting")
            self.assertTrue(cp2.is_done("a1"))
            pending = cp2.filter_pending(["a1", "a2", "a3", "a4"])
            self.assertEqual(pending, ["a3", "a4"])


class TestCleanup(unittest.TestCase):
    def test_cleanup_url_lists_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            old = base / "url_list_20000101.txt"
            new = base / "url_list_20990101.txt"
            old.write_text("x", encoding="utf-8")
            new.write_text("y", encoding="utf-8")
            # Force old mtime
            old_time = time.time() - (60 * 86400)
            os.utime(old, (old_time, old_time))

            count, paths = cleanup_url_lists(base, keep_days=30)
            self.assertEqual(count, 1)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists())

            logs = [base / f"pixivutil.log.{i}" for i in range(1, 6)]
            for i, p in enumerate(logs):
                p.write_text(f"log{i}", encoding="utf-8")
                os.utime(p, (time.time() - i * 100, time.time() - i * 100))
            removed, _ = cleanup_old_logs(base, keep_count=2, patterns=("pixivutil.log.*",))
            self.assertEqual(removed, 3)
            remaining = list(base.glob("pixivutil.log.*"))
            self.assertEqual(len(remaining), 2)

            report = run_startup_cleanup(base, url_list_keep_days=0, log_keep_count=0)
            self.assertIn("url_lists_removed", report)


if __name__ == "__main__":
    unittest.main()
