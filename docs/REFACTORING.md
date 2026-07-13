# Refactoring roadmap

PixivUtil2 grew for ~15 years as a CLI script. A full rewrite is possible but high-risk for a production tool with multi‑GB SQLite DBs. This document describes **what is wrong**, **what we already fixed**, and **safe next waves**.

## Goals

1. Keep behaviour stable for daily `run_z` / `run_f1` automation.
2. Remove clear bad practices when the fix is localized.
3. Make the hot paths (DB, FANBOX, downloads) faster and easier to test.
4. Avoid a big-bang rewrite of 15k+ lines in one PR.

## Known bad practices (legacy)

| Issue | Where | Why it hurts |
|-------|--------|--------------|
| `except BaseException` | DB / CLI / handlers | Swallows `KeyboardInterrupt` / `SystemExit` |
| Silent `try/except ALTER` | `createDatabase` | Hides real DB errors |
| Global module state | `PixivUtil2.py` | Hard to test; hidden coupling |
| `caller = sys.modules[__name__]` | all handlers | Handlers depend on CLI entrypoint |
| God files | `PixivUtil2`, `PixivDBManager`, `PixivBrowserFactory` | Hard to navigate and review |
| Few indexes (historical) | SQLite | Full scans on multi‑million image DBs |
| DEBUG logs dumping full JSON | browser factory | Huge logs, slow I/O, privacy risk |
| No DI / interfaces | everywhere | Mocks and unit tests are painful |

## Wave 1 (done in this fork)

- [x] FANBOX error isolation + API normalize + checkpoint
- [x] SQLite indexes + connection pragmas (`WAL`, cache, mmap)
- [x] Schema upgrades via `ensure_column()` instead of blind `ALTER` try/except
- [x] `except BaseException` → `except Exception` in `PixivDBManager` / `PixivUtil2`
- [x] `AppContext` facade + `get_caller()` (handlers no longer receive the raw module object at call sites)
- [x] Retry backoff, run summary, startup cleanup
- [x] Docs: `docs/FORK.md`, this file

## Wave 2 (recommended next)

Priority order:

1. **Split `PixivUtil2.py` menu layer**  
   Move each `menu_*` function into `cli/commands_*.py`. Keep `main()` as composition root only.

2. **Explicit handler signatures**  
   Change handlers from `process_*(caller, config, ...)` to `process_*(ctx: AppContext, ...)` and stop reading `caller.__config__` when `config` is already passed.

3. **Repository layer for SQLite**  
   Group `select*` / `insert*` by domain (`MemberRepo`, `ImageRepo`, `FanboxRepo`) inside `db/`. Keep `PixivDBManager` as a façade temporarily.

4. **Narrow browser factory**  
   Split Pixiv / FANBOX / Sketch clients. Inject `session` instead of subclassing `mechanize.Browser` forever.

5. **Structured logging**  
   Never log full API bodies at INFO; gate raw JSON behind DEBUG and a size limit.

6. **Type hints + mypy on `common/` and `handler/`**  
   Gradual, file by file.

## Wave 3 (larger architecture)

- Optional async or bounded thread pool for **metadata** fetches only (downloads already support `downloadWorkers`).
- Config as immutable snapshot per run (reload creates new object).
- Plugin-style download sources (Pixiv / FANBOX / Sketch).
- Replace demjson3 with stdlib `json` where possible.

## What not to do

- Do not rewrite models against live HTML scraping that still works via AJAX JSON.
- Do not remove SQLite compatibility for existing multi‑GB `db.sqlite` files.
- Do not force concurrent downloads default > 1 (ban risk).
- Do not “clean” by deleting experimental batch/ranking features without a deprecation path.

## How to contribute a safe refactor

1. Add/adjust a unit test in `test/` first when behaviour is subtle.
2. Keep a thin compatibility shim if you rename symbols handlers import.
3. Run:

```bash
python -m unittest discover -s test -p 'test_PixivModel_fanbox.py'
python -m unittest discover -s test -p 'test_PixivRunStats_Checkpoint_Cleanup.py'
python -m unittest discover -s test -p 'test_PixivHelper.py'
python -m py_compile PixivUtil2.py PixivDBManager.py common/*.py handler/*.py
```

4. Prefer many small PRs over one mega-diff.

## Performance notes (already applied)

| Change | Effect |
|--------|--------|
| `PRAGMA journal_mode=WAL` | Better concurrent read/write |
| `PRAGMA cache_size=-65536` | ~64MB page cache |
| `PRAGMA mmap_size=256MB` | Faster reads on large DB files |
| Indexes on `member_id` / dates | Avoid full table scans |
| `checkUpdatedLimit*` defaults | Stop early on daily syncs |
| `logLevel=INFO` | Less I/O during long runs |
