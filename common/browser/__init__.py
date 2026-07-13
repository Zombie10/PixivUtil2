# -*- coding: utf-8 -*-
"""
Browser client package.

``PixivBrowser`` composes domain mixins:

- ``FanboxClientMixin``  (common.browser.fanbox_client)
- ``SketchClientMixin``  (common.browser.sketch_client)
- core Pixiv methods remain on ``PixivBrowser`` in PixivBrowserFactory

Public entry:

    from common.browser import get_browser, FanboxClientMixin, SketchClientMixin
"""
from common.browser.fanbox_client import FanboxClientMixin
from common.browser.sketch_client import SketchClientMixin


def get_browser(*args, **kwargs):
    """Lazy re-export to avoid circular import with PixivBrowserFactory."""
    from common.PixivBrowserFactory import getBrowser
    return getBrowser(*args, **kwargs)


__all__ = [
    "get_browser",
    "FanboxClientMixin",
    "SketchClientMixin",
]
