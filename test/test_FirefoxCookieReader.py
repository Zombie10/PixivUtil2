# -*- coding: utf-8 -*-
import os
import sqlite3
import tempfile
import unittest

from common.FirefoxCookieReader import (
    build_cookie_header,
    clear_cache,
    get_fanbox_cookie_header,
    get_fanbox_cookies,
    read_fanbox_cookies,
)


class TestFirefoxCookieReader(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def tearDown(self):
        clear_cache()

    def test_build_cookie_header_orders_known_cookies(self):
        cookies = {
            "privacy_policy_notification": "0",
            "FANBOXSESSID": "abc123",
            "cf_clearance": "cf-value",
            "__cf_bm": "bm-value",
        }
        header = build_cookie_header(cookies)
        self.assertEqual(
            header,
            "FANBOXSESSID=abc123; cf_clearance=cf-value; __cf_bm=bm-value; privacy_policy_notification=0",
        )

    def test_read_fanbox_cookies_from_sqlite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = os.path.join(temp_dir, "profile")
            os.makedirs(profile_path)
            cookies_db = os.path.join(profile_path, "cookies.sqlite")

            conn = sqlite3.connect(cookies_db)
            conn.execute(
                """CREATE TABLE moz_cookies (
                       id INTEGER PRIMARY KEY,
                       originAttributes TEXT,
                       name TEXT,
                       value TEXT,
                       host TEXT,
                       path TEXT,
                       expiry INTEGER,
                       lastAccessed INTEGER,
                       creationTime INTEGER,
                       isSecure INTEGER,
                       isHttpOnly INTEGER,
                       inBrowserElement INTEGER,
                       sameSite INTEGER,
                       rawSameSite INTEGER,
                       schemeMap INTEGER
                   )"""
            )
            conn.execute(
                "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
                ("FANBOXSESSID", "sess123", ".fanbox.cc"),
            )
            conn.execute(
                "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
                ("cf_clearance", "clear123", ".fanbox.cc"),
            )
            conn.execute(
                "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
                ("PHPSESSID", "pixiv-only", ".pixiv.net"),
            )
            conn.commit()
            conn.close()

            cookies = read_fanbox_cookies(profile_path)
            self.assertEqual(cookies["FANBOXSESSID"], "sess123")
            self.assertEqual(cookies["cf_clearance"], "clear123")
            self.assertNotIn("PHPSESSID", cookies)

    def test_get_fanbox_cookie_header_uses_profile_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = os.path.join(temp_dir, "profile")
            os.makedirs(profile_path)
            cookies_db = os.path.join(profile_path, "cookies.sqlite")

            conn = sqlite3.connect(cookies_db)
            conn.execute(
                """CREATE TABLE moz_cookies (
                       id INTEGER PRIMARY KEY,
                       originAttributes TEXT,
                       name TEXT,
                       value TEXT,
                       host TEXT,
                       path TEXT,
                       expiry INTEGER,
                       lastAccessed INTEGER,
                       creationTime INTEGER,
                       isSecure INTEGER,
                       isHttpOnly INTEGER,
                       inBrowserElement INTEGER,
                       sameSite INTEGER,
                       rawSameSite INTEGER,
                       schemeMap INTEGER
                   )"""
            )
            conn.execute(
                "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
                ("FANBOXSESSID", "override-session", ".fanbox.cc"),
            )
            conn.commit()
            conn.close()

            header = get_fanbox_cookie_header(profile_override=profile_path)
            self.assertIn("FANBOXSESSID=override-session", header)

            cookies = get_fanbox_cookies(profile_override=profile_path)
            self.assertEqual(cookies["FANBOXSESSID"], "override-session")


if __name__ == "__main__":
    unittest.main()