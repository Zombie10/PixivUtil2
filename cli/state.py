# -*- coding: utf-8 -*-
"""
Runtime binding for CLI menus split out of PixivUtil2.

main() must call ``state.bind(sys.modules[__name__])`` before any menu runs.
Menus access process globals via this module (``state.config``, ``state.br``, …).
"""
from __future__ import annotations

from types import ModuleType
from typing import Any, Callable, Optional

_module: Optional[ModuleType] = None

_menu_fn: Optional[Callable[[], str]] = None
_read_lists_fn: Optional[Callable[[], None]] = None
_set_console_title_fn: Optional[Callable[..., None]] = None
_get_start_end_fn: Optional[Callable] = None
_get_list_file_fn: Optional[Callable] = None


def bind(module: ModuleType) -> None:
    global _module
    _module = module


def register_helpers(
    *,
    menu=None,
    read_lists=None,
    set_console_title=None,
    get_start_and_end_page_from_options=None,
    get_list_file_from_options=None,
) -> None:
    global _menu_fn, _read_lists_fn, _set_console_title_fn, _get_start_end_fn, _get_list_file_fn
    if menu is not None:
        _menu_fn = menu
    if read_lists is not None:
        _read_lists_fn = read_lists
    if set_console_title is not None:
        _set_console_title_fn = set_console_title
    if get_start_and_end_page_from_options is not None:
        _get_start_end_fn = get_start_and_end_page_from_options
    if get_list_file_from_options is not None:
        _get_list_file_fn = get_list_file_from_options


def _m() -> ModuleType:
    if _module is None:
        raise RuntimeError("cli.state.bind(module) was not called before using CLI menus")
    return _module


def __getattr__(name: str) -> Any:
    """Allow ``state.config`` / ``state.br`` style access on this module."""
    m = _m()
    mapping = {
        "config": "__config__",
        "log": "__log__",
        "br": "__br__",
        "db": "__dbManager__",
        "configfile": "configfile",
        "valid_options": "__valid_options",
        "error_list": "__errorList",
        "blacklist_tags": "__blacklistTags",
        "blacklist_members": "__blacklistMembers",
        "blacklist_titles": "__blacklistTitles",
        "suppress_tags": "__suppressTags",
        "series_downloaded": "__seriesDownloaded",
    }
    if name in mapping:
        return getattr(m, mapping[name])
    raise AttributeError(f"module 'cli.state' has no attribute {name!r}")


def get_caller():
    return _m().get_caller()


def set_error_code(code: int) -> None:
    _m().ERROR_CODE = code


def set_blacklist_tags(value) -> None:
    _m().__blacklistTags = value


def set_blacklist_members(value) -> None:
    _m().__blacklistMembers = value


def set_blacklist_titles(value) -> None:
    _m().__blacklistTitles = value


def set_suppress_tags(value) -> None:
    _m().__suppressTags = value


def menu():
    if _menu_fn is None:
        raise RuntimeError("menu helper not registered — import cli.helpers first")
    return _menu_fn()


def read_lists():
    if _read_lists_fn is None:
        raise RuntimeError("read_lists helper not registered")
    return _read_lists_fn()


def set_console_title(title: str = "") -> None:
    if _set_console_title_fn is not None:
        return _set_console_title_fn(title)
    return _m().set_console_title(title)


def get_start_and_end_page_from_options(options):
    if _get_start_end_fn is None:
        raise RuntimeError("get_start_and_end_page_from_options not registered")
    return _get_start_end_fn(options)


def get_list_file_from_options(options, default_list_file):
    if _get_list_file_fn is None:
        raise RuntimeError("get_list_file_from_options not registered")
    return _get_list_file_fn(options, default_list_file)
