# Refactoring roadmap

PixivUtil2 grew for ~15 years as a CLI script. Refactors are applied in **waves** that preserve behaviour for daily `run_z` / `run_f1` automation and multi‑GB SQLite DBs.

## Hard constraints (do not violate)

1. **No incompatible SQLite schema changes** — only additive columns/indexes via `ensure_column` / `CREATE INDEX IF NOT EXISTS`.
2. **Do not raise `downloadWorkers` default** — stays `1` (ban risk).
3. **Do not remove experimental features** without an explicit deprecation path (batch job `b`, rankings, etc. stay).

## Wave 1 — done

- FANBOX isolation / checkpoint / normalize  
- SQLite indexes + WAL pragmas + `ensure_column`  
- `except BaseException` → `Exception`  
- `AppContext` + `get_caller()`  
- Run summary, cleanup, retry backoff  
- Docs: `docs/FORK.md`

## Wave 2 — done (this fork)

| Item | Implementation |
|------|----------------|
| Split CLI menus | Package `cli/` (`helpers`, `menus_*`, `main_loop`, `option_parser`) |
| Runtime binding | `cli.state.bind(main_module)` — menus never import PixivUtil2 |
| Thin entrypoint | `PixivUtil2.py` ~400 lines (globals + `main` + re-exports) |
| Repository façade | `db/repositories.py` — `Member` / `Image` / `Fanbox` / `Sketch` over existing DB API |
| Explicit handler context | FANBOX handler uses `Repositories.from_caller(caller)` |
| Structured log limits | `PixivHelper.log_payload()` truncates large API bodies |
| Browser seam | `common/browser/` re-exports `get_browser` (full split deferred safely) |

## Wave 3 — done (partial, safe subset)

| Item | Implementation |
|------|----------------|
| Config snapshot | `PixivConfig.snapshot()` for per-run frozen views |
| Safer JSON | `common/PixivJson.decode()` — stdlib `json` first, `demjson3` fallback |
| FANBOX/Browser decode | Hot paths use `PixivJson.decode` + truncated logging |
| Metadata thread pool | **Not enabled by default** (would change rate-limit behaviour) — left as future opt-in |
| Plugin sources | Deferred (experimental features kept as-is) |

## Layout after waves 1–3

```
PixivUtil2.py          # entrypoint + process globals
cli/
  state.py             # bind() + accessors for menus
  helpers.py           # menu UI, read_lists, page options
  option_parser.py
  main_loop.py
  menus_download.py
  menus_fanbox.py
  menus_sketch.py
  menus_export.py
common/
  PixivAppContext.py
  PixivJson.py
  PixivRunStats.py / Checkpoint / Cleanup
  browser/             # stable import seam
db/
  repositories.py      # domain façade (no schema change)
handler/               # download orchestration
model/                 # response models
```

## Future waves (optional)

1. Move FANBOX/Sketch HTTP methods from `PixivBrowserFactory` into `common/browser/fanbox.py` / `sketch.py` with the same public methods (behaviour-preserving cut/paste + tests).
2. Handler signatures: `process_*(ctx: AppContext, config: PixivConfig, ...)` with type hints end-to-end.
3. Optional `metadataWorkers` config (default 1) for parallel **metadata only**, never changing default download concurrency.
4. Gradual mypy on `common/` and `cli/`.

## Tests to run after refactors

```bash
source env/bin/activate
python -m unittest discover -s test -p 'test_PixivModel_fanbox.py'
python -m unittest discover -s test -p 'test_PixivAppContext_DB.py'
python -m unittest discover -s test -p 'test_PixivRunStats_Checkpoint_Cleanup.py'
python -m unittest discover -s test -p 'test_PixivJson_Repos_Config.py'
python -m unittest discover -s test -p 'test_PixivHelper.py'
python -m unittest discover -s test -p 'test_PixivModel.py'
python PixivUtil2.py --help
```

## What not to do

- Rewrite models against live HTML that still works via AJAX JSON.
- Force concurrent downloads default > 1.
- Delete batch/ranking/sketch features without deprecation.
- Change primary keys or drop columns on existing user databases.
