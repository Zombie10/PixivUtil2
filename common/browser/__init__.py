# -*- coding: utf-8 -*-
"""
Browser client package (Wave 2–3).

Today ``PixivBrowser`` in ``common.PixivBrowserFactory`` remains the concrete
implementation for Pixiv, FANBOX, and Sketch to avoid a risky behavioural split.

This package documents the intended seam and re-exports the factory for new code:

    from common.browser import get_browser

Future work can move FANBOX/Sketch methods into dedicated clients without
changing call sites that already import from here.
"""
from common.PixivBrowserFactory import getBrowser as get_browser

__all__ = ["get_browser"]
