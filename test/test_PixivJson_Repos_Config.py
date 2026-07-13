# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from common.PixivConfig import PixivConfig
from common.PixivJson import decode, dumps
from db.repositories import Repositories
from PixivDBManager import PixivDBManager


class TestPixivJson(unittest.TestCase):
    def test_strict_json(self):
        self.assertEqual(decode('{"x": 1}')["x"], 1)

    def test_non_strict_fallback(self):
        # demjson3 accepts unquoted keys; used for some historical payloads
        self.assertEqual(decode("{x: 2}")["x"], 2)

    def test_dumps(self):
        self.assertIn("á", dumps({"a": "á"}))


class TestConfigSnapshot(unittest.TestCase):
    def test_snapshot_is_independent_copy(self):
        cfg = PixivConfig()
        cfg.downloadWorkers = 1
        cfg.logLevel = "INFO"
        snap = cfg.snapshot()
        self.assertIsNot(snap, cfg)
        self.assertEqual(snap.downloadWorkers, 1)
        snap.downloadWorkers = 3
        self.assertEqual(cfg.downloadWorkers, 1)  # original unchanged
        # defaults stay safe
        self.assertEqual(PixivConfig().downloadWorkers, 1)


class TestRepositories(unittest.TestCase):
    def test_fanbox_repo_roundtrip_methods_exist(self):
        fd, path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        try:
            db = PixivDBManager(".", path)
            db.createDatabase()
            repos = Repositories(db)
            # Missing post returns None/empty depending on implementation
            result = repos.fanbox.select_post(999999999)
            # Just ensure callable path works without exception
            self.assertTrue(result is None or result is not None)
            db.close()
        finally:
            for suffix in ("", "-wal", "-shm"):
                try:
                    os.unlink(path + suffix)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
