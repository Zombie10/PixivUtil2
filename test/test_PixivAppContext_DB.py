# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from common.PixivAppContext import AppContext, get_app_context, set_app_context
from PixivDBManager import PixivDBManager


class DummyMain:
    __config__ = object()
    __dbManager__ = object()
    __br__ = None
    configfile = "./config.ini"
    ERROR_CODE = 0
    UTF8_FS = None
    dfilename = "x.txt"

    def set_console_title(self, title=""):
        self.last_title = title


class TestAppContext(unittest.TestCase):
    def tearDown(self):
        set_app_context(None)

    def test_proxy_reads_and_writes(self):
        main = DummyMain()
        ctx = AppContext.bind(main)
        self.assertIs(get_app_context(), ctx)
        self.assertIs(ctx.__config__, main.__config__)
        ctx.ERROR_CODE = 42
        self.assertEqual(main.ERROR_CODE, 42)
        ctx.UTF8_FS = True
        self.assertTrue(main.UTF8_FS)
        ctx.set_console_title("hi")
        self.assertEqual(main.last_title, "hi")
        self.assertIs(ctx.config, main.__config__)
        self.assertIs(ctx.db, main.__dbManager__)


class TestDBEnsureColumnAndPragmas(unittest.TestCase):
    def test_ensure_column_and_wal(self):
        fd, path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        try:
            db = PixivDBManager(root_directory=".", target=path, optimize=True)
            db.createDatabase()
            c = db.conn.cursor()
            mode = c.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(str(mode).lower(), "wal")

            # Column already exists after createDatabase
            cols = db.table_columns(c, "pixiv_master_member")
            self.assertIn("is_deleted", cols)
            self.assertIn("member_token", cols)

            added = db.ensure_column(c, "pixiv_master_member", "refactor_test_col", "TEXT")
            self.assertTrue(added)
            added_again = db.ensure_column(c, "pixiv_master_member", "refactor_test_col", "TEXT")
            self.assertFalse(added_again)
            cols2 = db.table_columns(c, "pixiv_master_member")
            self.assertIn("refactor_test_col", cols2)
            c.close()
            db.close()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
            for suffix in ("-wal", "-shm"):
                try:
                    os.unlink(path + suffix)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
