# -*- coding: utf-8 -*-
"""Contract tests for FANBOX/Sketch client mixins extracted from PixivBrowser."""
import inspect
import unittest

from common.browser.fanbox_client import FanboxClientMixin
from common.browser.sketch_client import SketchClientMixin
from common.PixivBrowserFactory import PixivBrowser
from model.PixivModelFanbox import FanboxArtist


FANBOX_API = [
    "fanboxGetArtistList",
    "fanboxGetArtistById",
    "fanboxGetPostsFromArtist",
    "fanboxUpdatePost",
    "fanboxGetPostById",
    "fanboxGetPostJsonById",
    "fanboxLoginUsingCookie",
    "fanbox_is_logged_in",
    "updateFanboxCookie",
    "_use_browser_fanbox_cookies",
    "_get_fanbox_cookie_header",
    "_get_fanbox_cookies_from_browser",
    "_sync_fanbox_auth_from_browser",
]

SKETCH_API = [
    "sketch_get_post_by_post_id",
    "sketch_get_posts_by_artist_id",
    "getPixivSketchPage",
]


class TestBrowserClientContracts(unittest.TestCase):
    def test_mro_includes_mixins(self):
        names = [c.__name__ for c in PixivBrowser.__mro__]
        self.assertIn("FanboxClientMixin", names)
        self.assertIn("SketchClientMixin", names)
        self.assertIn("Browser", names)  # mechanize.Browser

    def test_fanbox_methods_owned_by_mixin(self):
        for name in FANBOX_API:
            self.assertTrue(hasattr(PixivBrowser, name), f"missing {name}")
            # Resolved from FanboxClientMixin, not accidentally left empty on PixivBrowser
            owner = None
            for cls in PixivBrowser.__mro__:
                if name in cls.__dict__:
                    owner = cls
                    break
            self.assertIs(owner, FanboxClientMixin, f"{name} owned by {owner}")

    def test_sketch_methods_owned_by_mixin(self):
        for name in SKETCH_API:
            self.assertTrue(hasattr(PixivBrowser, name), f"missing {name}")
            owner = None
            for cls in PixivBrowser.__mro__:
                if name in cls.__dict__:
                    owner = cls
                    break
            self.assertIs(owner, SketchClientMixin, f"{name} owned by {owner}")

    def test_fanbox_method_signatures_stable(self):
        # Guard against accidental renames/arg drops during moves.
        sig = inspect.signature(PixivBrowser.fanboxGetArtistById)
        params = list(sig.parameters)
        self.assertEqual(params[0], "self")
        self.assertIn("artist_id", params)
        self.assertIn("for_suspended", params)

        sig2 = inspect.signature(PixivBrowser.fanboxGetPostJsonById)
        params2 = list(sig2.parameters)
        self.assertIn("post_id", params2)

    def test_normalize_post_payload_used_by_client_path(self):
        # fanboxGetPostJsonById normalizes body.post; ensure helper still works.
        body = {"post": {"id": "1", "title": "t", "type": "text"}}
        normalized = FanboxArtist.normalize_post_payload(body)
        self.assertEqual(normalized["title"], "t")

    def test_package_exports(self):
        from common.browser import FanboxClientMixin as F
        from common.browser import SketchClientMixin as S
        from common.browser import get_browser
        self.assertIs(F, FanboxClientMixin)
        self.assertIs(S, SketchClientMixin)
        self.assertTrue(callable(get_browser))


if __name__ == "__main__":
    unittest.main()
