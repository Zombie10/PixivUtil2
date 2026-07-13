# -*- coding: utf-8 -*-
"""
JSON helpers with a safe fallback stack.

Prefer stdlib ``json`` (faster, maintained). Fall back to ``demjson3`` only when
the payload is non-strict (historical Pixiv/FANBOX edge cases).
"""
from __future__ import annotations

import json
from typing import Any, Union

try:
    import demjson3
except ImportError:  # pragma: no cover
    demjson3 = None


def decode(text: Union[str, bytes], *, encoding: str = "utf-8") -> Any:
    if isinstance(text, bytes):
        text = text.decode(encoding, errors="replace")
    if text is None:
        raise ValueError("Cannot decode empty JSON payload")
    text = text.strip()
    if not text:
        raise ValueError("Cannot decode empty JSON payload")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if demjson3 is None:
            raise
        return demjson3.decode(text)


def decode_file(path: str, *, encoding: str = "utf-8") -> Any:
    with open(path, "r", encoding=encoding) as fh:
        return decode(fh.read())


def dumps(obj: Any, **kwargs) -> str:
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(obj, **kwargs)
