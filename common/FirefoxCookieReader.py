# -*- coding: utf-8 -*-
import configparser
import os
import platform
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

FANBOX_HOST_SUFFIX = "fanbox.cc"
FANBOX_COOKIE_ORDER = (
    "FANBOXSESSID",
    "cf_clearance",
    "__cf_bm",
    "p_ab_id",
    "p_ab_id_2",
    "p_ab_d_id",
    "privacy_policy_agreement",
    "privacy_policy_notification",
)

_cache: Dict[str, object] = {
    "cookies": None,
    "cookie_header": "",
    "profile_path": "",
    "expires_at": 0.0,
}

CACHE_TTL_SECONDS = 300


def get_firefox_base_dir() -> Optional[Path]:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Firefox"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Mozilla/Firefox"
        return None
    return Path.home() / ".mozilla/firefox"


def _normalize_profile_path(base_dir: Path, profile_entry: str) -> Optional[Path]:
    profile_path = Path(profile_entry)
    if not profile_path.is_absolute():
        profile_path = base_dir / profile_entry
    if profile_path.is_dir():
        return profile_path
    return None


def _collect_profile_candidates(base_dir: Path):
    profiles_ini = base_dir / "profiles.ini"
    candidates = []
    seen = set()

    if profiles_ini.is_file():
        parser = configparser.ConfigParser()
        parser.read(profiles_ini, encoding="utf-8")

        for section in parser.sections():
            if section.startswith("Install") and parser.has_option(section, "Default"):
                profile_path = _normalize_profile_path(base_dir, parser.get(section, "Default"))
                if profile_path and profile_path not in seen:
                    candidates.append(profile_path)
                    seen.add(profile_path)

        for section in parser.sections():
            if section.startswith("Profile") and parser.has_option(section, "Path"):
                profile_path = _normalize_profile_path(base_dir, parser.get(section, "Path"))
                if profile_path and profile_path not in seen:
                    candidates.append(profile_path)
                    seen.add(profile_path)

    profiles_dir = base_dir / "Profiles"
    if profiles_dir.is_dir():
        for profile_path in sorted(profiles_dir.iterdir()):
            if profile_path.is_dir() and profile_path not in seen:
                candidates.append(profile_path)
                seen.add(profile_path)

    return candidates


def _get_fanbox_session_score(profile_path: Path) -> int:
    profile_path = Path(profile_path)
    cookies_db = profile_path / "cookies.sqlite"
    if not cookies_db.is_file():
        return -1

    temp_db = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as temp_file:
            temp_db = temp_file.name
        shutil.copy2(cookies_db, temp_db)

        conn = sqlite3.connect(temp_db)
        try:
            row = conn.execute(
                """SELECT MAX(lastAccessed)
                   FROM moz_cookies
                   WHERE host LIKE ? AND name = 'FANBOXSESSID'""",
                (f"%{FANBOX_HOST_SUFFIX}%",),
            ).fetchone()
        finally:
            conn.close()

        if row and row[0]:
            return int(row[0])
        return 0
    except BaseException:
        return -1
    finally:
        if temp_db and os.path.exists(temp_db):
            os.unlink(temp_db)


def find_default_profile_path(profile_override: str = "") -> Optional[Path]:
    if profile_override:
        override_path = Path(profile_override).expanduser()
        if override_path.is_dir():
            return override_path
        return None

    base_dir = get_firefox_base_dir()
    if base_dir is None or not base_dir.is_dir():
        return None

    candidates = _collect_profile_candidates(base_dir)
    best_profile = None
    best_score = -1
    for profile_path in candidates:
        score = _get_fanbox_session_score(profile_path)
        if score > best_score:
            best_score = score
            best_profile = profile_path

    if best_profile is not None and best_score >= 0:
        return best_profile

    return candidates[0] if candidates else None


def build_cookie_header(cookies: Dict[str, str], cookie_order=FANBOX_COOKIE_ORDER) -> str:
    parts = []
    for name in cookie_order:
        value = cookies.get(name)
        if value:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


def read_fanbox_cookies(profile_path) -> Dict[str, str]:
    profile_path = Path(profile_path)
    cookies_db = profile_path / "cookies.sqlite"
    if not cookies_db.is_file():
        return {}

    temp_db = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as temp_file:
            temp_db = temp_file.name
        shutil.copy2(cookies_db, temp_db)

        conn = sqlite3.connect(temp_db)
        try:
            rows = conn.execute(
                """SELECT name, value FROM moz_cookies
                   WHERE host LIKE ?
                   ORDER BY name""",
                (f"%{FANBOX_HOST_SUFFIX}%",),
            ).fetchall()
        finally:
            conn.close()

        return {name: value for name, value in rows}
    finally:
        if temp_db and os.path.exists(temp_db):
            os.unlink(temp_db)


def get_fanbox_cookies(profile_override: str = "", force_refresh: bool = False) -> Dict[str, str]:
    now = time.time()
    if (
        not force_refresh
        and _cache["cookies"] is not None
        and now < float(_cache["expires_at"])
    ):
        return dict(_cache["cookies"])

    profile_path = find_default_profile_path(profile_override)
    if profile_path is None:
        _cache["cookies"] = {}
        _cache["cookie_header"] = ""
        _cache["profile_path"] = ""
        _cache["expires_at"] = now + CACHE_TTL_SECONDS
        return {}

    cookies = read_fanbox_cookies(profile_path)
    _cache["cookies"] = cookies
    _cache["cookie_header"] = build_cookie_header(cookies)
    _cache["profile_path"] = str(profile_path)
    _cache["expires_at"] = now + CACHE_TTL_SECONDS
    return dict(cookies)


def get_fanbox_cookie_header(profile_override: str = "", force_refresh: bool = False) -> str:
    get_fanbox_cookies(profile_override=profile_override, force_refresh=force_refresh)
    return str(_cache["cookie_header"])


def get_cached_profile_path() -> str:
    return str(_cache.get("profile_path", ""))


def clear_cache():
    _cache["cookies"] = None
    _cache["cookie_header"] = ""
    _cache["profile_path"] = ""
    _cache["expires_at"] = 0.0