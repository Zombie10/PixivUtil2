# PixivUtil2 fork (Zombie10)

Operational fork of [Nandaka/PixivUtil2](https://github.com/Nandaka/PixivUtil2) focused on daily automation, FANBOX reliability, and large local databases.

Upstream version base: `20251112` (`common/PixivConstant.py`).

---

## Quick start

```bash
# Virtualenv (once)
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Configure cookies / paths in config.ini (see Authentication section)

# Daily: bookmarked artists → download
./run_z.sh 5 4

# Daily: FANBOX supporting list (resumable)
./run_f1.sh 1
```

Interactive menu:

```bash
python PixivUtil2.py
```

Useful CLI modes:

| Mode | Description |
|------|-------------|
| `-s z` | Export bookmarked user IDs + download |
| `-s f1` | FANBOX supporting list |
| `-s f2` | FANBOX by creator id |
| `-s f4` | FANBOX following list |
| `-s f5` | FANBOX custom list file |

---

## Local scripts

### `run_z.sh [bookmark_pages] [artist_pages]`

1. Exports public bookmarked artists (`-s z`).
2. Downloads each artist for pages `1..artist_pages`.
3. Appends output to `run_z.log`.
4. Shows a macOS notification when finished.
5. Exit code is non-zero on failure.

Defaults: `bookmark_pages=5`, `artist_pages=4`.

### `run_f1.sh [end_page]`

1. Downloads FANBOX supporting list (`-s f1`).
2. Appends output to `run_f1.log`.
3. Resumes from `checkpoint_fanbox_supporting.json` when enabled.
4. macOS notification + exit code.

Default: `end_page=1` (only newest page per creator). Use `0` for no page limit.

Restart without resume:

```bash
python PixivUtil2.py -s f1 -x --ep=1 --no-resume
```

---

## FANBOX robustness

| Feature | Detail |
|---------|--------|
| Per-post isolation | One bad post no longer aborts the whole artist list |
| Per-artist isolation | One bad artist no longer aborts `f1`/`f4`/`f5` |
| Payload normalize | Handles `body.post` wrappers from `post.info` |
| List formats | Supports `plans` / `supportingPlans` wrappers and bare id lists |
| Checkpoint | JSON checkpoint of completed creator ids |
| Summary | End-of-run counters (ok / skip / restricted / error) |

Checkpoint files (gitignored):

- `checkpoint_fanbox_supporting.json`
- `checkpoint_fanbox_following.json`
- `checkpoint_fanbox_custom.json`

---

## Database performance

On every `createDatabase()` call the app ensures indexes such as:

- `idx_pixiv_image_member`
- `idx_pixiv_image_member_updated`
- `idx_fanbox_post_member`
- `idx_fanbox_post_updated`
- …

Large DBs may take ~1 minute the first time indexes are built. Subsequent starts are fast (`IF NOT EXISTS`).

---

## Network & downloads

| Setting | Default | Meaning |
|---------|---------|---------|
| `retry` | `3` | Max download retries |
| `retryWait` | `5` | Base wait seconds |
| `retryBackoff` | `True` | Exponential backoff (5, 10, 20… capped at 300s) |
| `downloadWorkers` | `1` | Parallel files inside multi-file FANBOX posts (1–8) |
| `downloadDelay` | config | Delay between items (keep ≥3 to reduce bans) |

HTTP **429 / 503 / 5xx** trigger retry with backoff. **404** is treated as permanent failure.

---

## Maintenance

| Setting | Default | Meaning |
|---------|---------|---------|
| `logLevel` | `INFO` | Prefer INFO daily; DEBUG only while diagnosing |
| `enableStartupCleanup` | `True` | Prune old dumps/logs at start |
| `urlListKeepDays` | `30` | Delete `url_list_*.txt` older than N days |
| `logKeepCount` | `10` | Keep newest N rotated log files |
| `enableRunSummary` | `True` | Print run summary when applicable |
| `checkUpdatedLimit` | `5` | Stop artist after N already-downloaded items (0 = never) |
| `checkUpdatedLimitFanbox` | `5` | Same for FANBOX |

---

## Authentication (FANBOX cookies from Firefox)

```ini
[Authentication]
cookieFanboxFromBrowser = True
firefoxProfilePath =
userAgentImpersonation = firefox135
```

- Leave `firefoxProfilePath` empty to auto-detect the default Firefox profile.
- Firefox must be logged into FANBOX (and preferably closed or unlocked enough to copy cookies).
- Cloudflare cookies (`cf_clearance`, `__cf_bm`) are refreshed when the API returns non-JSON HTML.

Pixiv login still expects a valid `cookie` / `PHPSESSID` in `config.ini` (username/password login is broken upstream).

---

## Recommended `config.ini` snippet

```ini
[Debug]
logLevel = INFO
enableRunSummary = True
enableStartupCleanup = True
urlListKeepDays = 30
logKeepCount = 10

[Network]
retry = 3
retryWait = 5
retryBackoff = True
downloadWorkers = 1
downloadDelay = 3

[FANBOX]
checkUpdatedLimitFanbox = 5
enableCheckpoint = True
checkpointPathFanbox =
cookieFanboxFromBrowser = True

[DownloadControl]
checkUpdatedLimit = 5
verifyImage = True
```

Set `checkUpdatedLimit*` to `0` only when you intentionally want a full re-scan.

---

## New modules

| Module | Role |
|--------|------|
| `common/PixivRunStats.py` | Per-run counters + summary |
| `common/PixivCheckpoint.py` | JSON checkpoint/resume |
| `common/PixivCleanup.py` | url_list / log housekeeping |
| `common/FirefoxCookieReader.py` | Read FANBOX cookies from Firefox |
| `common/PixivAppContext.py` | Handler context façade (replaces passing `sys.modules`) |
| `common/PixivJson.py` | stdlib JSON + demjson3 fallback |
| `cli/` | Menus / option parser / main loop (split from entrypoint) |
| `db/repositories.py` | Domain repos over PixivDBManager (no schema break) |
| `common/browser/` | Stable import seam for the browser client |

Architecture / waves: **[docs/REFACTORING.md](REFACTORING.md)**

---

## Tests

```bash
source env/bin/activate
python -m unittest discover -s test -p 'test_PixivModel_fanbox.py'
python -m unittest discover -s test -p 'test_PixivRunStats_Checkpoint_Cleanup.py'
python -m unittest discover -s test -p 'test_FirefoxCookieReader.py'
```

---

## GUI

`python PixivUtilGUI.py` includes modes for:

- `z` — export + download bookmarked artists  
- `f1` / `f2` / `f3` / `f4` / `f5` — FANBOX modes  

The GUI shells out to `PixivUtil2.py`; CLI remains the primary path for automation.

---

## Upstream sync

This repo tracks upstream Nandaka changes periodically. When merging upstream:

1. Prefer keeping fork modules under `common/Pixiv{RunStats,Checkpoint,Cleanup,FirefoxCookieReader}.py`.
2. Re-check FANBOX parsers if API shapes change again.
3. Re-run the unittest subset above.

---

## Warning

Heavy usage can get your IP temporarily blocked by Pixiv/FANBOX. Prefer moderate `downloadDelay`, `checkUpdatedLimit*`, and avoid parallel workers higher than 2–3 unless you know the risk.
