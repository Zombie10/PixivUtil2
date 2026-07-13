# -*- coding: utf-8 -*-
"""
Application context for handlers.

Historically every handler received `sys.modules[__name__]` (the CLI main module)
as `caller` and poked globals like `caller.__dbManager__`. That tightly couples
library code to the entrypoint.

AppContext is a thin, explicit facade:

1. Today it proxies attribute access to the main module (zero behaviour change).
2. Call sites can depend on AppContext instead of the main module type.
3. Later we can move state onto AppContext fields without touching every handler.

Usage in main:
    ctx = AppContext.bind(sys.modules[__name__])
    PixivFanboxHandler.process_...(ctx, config, ...)
"""
from __future__ import annotations

from typing import Any, Optional


class AppContext:
    """Facade over runtime state used by handlers."""

    __slots__ = ("_module",)

    def __init__(self, module: Any):
        object.__setattr__(self, "_module", module)

    # --- proxy protocol -------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_module"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_module":
            object.__setattr__(self, name, value)
            return
        setattr(object.__getattribute__(self, "_module"), name, value)

    def __repr__(self) -> str:
        mod = object.__getattribute__(self, "_module")
        return f"<AppContext module={getattr(mod, '__name__', type(mod).__name__)}>"

    # --- explicit helpers (optional, non-breaking) ----------------------
    @property
    def config(self):
        return getattr(self, "__config__", None)

    @property
    def db(self):
        return getattr(self, "__dbManager__", None)

    @property
    def browser(self):
        return getattr(self, "__br__", None)

    def module(self) -> Any:
        return object.__getattribute__(self, "_module")

    @classmethod
    def bind(cls, module: Any) -> "AppContext":
        """Create context and register it as the process-wide active context."""
        ctx = cls(module)
        set_app_context(ctx)
        return ctx

    @classmethod
    def from_main_module(cls, module: Any) -> "AppContext":
        return cls.bind(module)


_active_context: Optional[AppContext] = None


def set_app_context(ctx: Optional[AppContext]) -> None:
    global _active_context
    _active_context = ctx


def get_app_context() -> Optional[AppContext]:
    return _active_context
