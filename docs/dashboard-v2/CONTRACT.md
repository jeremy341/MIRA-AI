# MIRA Dashboard v2: shared contract

This file is the single source of truth for the dashboard rebuild. Backend and UI agents work in
parallel in separate worktrees, so **do not change routes, JSON shapes or table names defined here
without telling the coordinator** (put the proposed change in your final report instead of making it).

Base branch: `dashboard-v2`. Every agent creates its own branch from it:
`git switch -c dashv2/<area> dashboard-v2`. Do not push, do not open PRs, do not touch `main`.

## 1. Goals

New dashboard with: **Sessions** (start, name, stop, review, replayable timeline), **Export** (CSV,
JSON, one-page HTML report that prints to PDF), **Model compare**, **Video and batch input** with
progress, **Benchmark** tab (wires in `mira benchmark`), **Hardware view** (CPU, memory,
temperature history, Raspberry Pi friendly) and **Sorting-arm hooks** (placeholder API plus event
log; the robot is not built yet). The UI is rebuilt in Svelte 5 + Vite with the Orchard look used by
the website.

## 2. Repository layout

```
src/dashboard/backend/          existing FastAPI app (main.py, camera_service.py, ...)
src/dashboard/backend/v1/       NEW. Everything below is v1 of the API
  __init__.py                   api_router: includes every router under /api/v1
  state.py                      process-wide singletons: get_db(), get_jobs(), get_events()
  storage.py                    SQLite (stdlib sqlite3) + migration runner
  migrations/NNNN_<area>.sql    one file per area, applied in filename order, idempotent
  jobs.py                       JobManager: background jobs with progress and cancel
  events.py                     EventBus: in-process pub/sub used by the events WebSocket
  routers/<area>.py             one router module per area (stubs exist; owners fill them)
src/dashboard/ui/               NEW. Svelte 5 + Vite source (owned by UI agents)
src/dashboard/frontend/dist/    NEW. Build output of src/dashboard/ui (gitignored, built in CI)
docs/dashboard-v2/              this contract, Orchard tokens reference
tests/dashboard_v2/             tests for the new code (one file per area)
```

The existing flat routes (`/api/status`, `/api/stream/start`, `/ws/video`, ...) stay working for
now. New work goes under `/api/v1` and `/ws/v1`. The old UI files in `src/dashboard/frontend/`
(`dashboard.html/css/js`) stay until the coordinator swaps in the new UI.

## 3. Conventions (all agents)

- Python 3.11/3.12, type hints, `from __future__ import annotations` is fine.
- **No new third-party dependencies** without asking. Use stdlib `sqlite3`, FastAPI, pydantic,
  numpy, opencv, psutil, ultralytics (all already required). PDF is **not** generated server-side:
  the report is an HTML page with print CSS.
- Quality gate (CI runs exactly this; all must pass before you report done):
  `ruff check src/ tests/`, `ruff format --check src/ tests/` (ruff **0.12.1**, line length 120),
  `pytest tests/ -q`. Mypy skips `src/dashboard/`, but keep types clean anyway.
  A ruff 0.12.1 binary is at `C:\Users\jerem\AppData\Local\Temp\ruffenv\Scripts\ruff.exe`;
  Python 3.11 with all deps is `C:\Users\jerem\AppData\Local\Programs\Python\Python311\python.exe`
  (the default `python` is 3.9 and will not work). If those paths are gone, `pip install ruff==0.12.1`
  into a Python 3.11 venv.
- Tests: pytest + FastAPI `TestClient`; never need a camera, GPU or network. Fake models and
  frames. Use a temp SQLite file (`MIRA_DASHBOARD_DB` env var).
- JSON is snake_case. Timestamps are ISO-8601 UTC strings (`2026-11-25T12:00:00+00:00`) in API
  payloads and REAL epoch seconds in SQLite columns named `ts`, `started_at_ts`, and so on.
- Errors: `HTTPException` with a human-readable `detail` string. 404 unknown id, 409 wrong state,
  413 too large, 415 wrong type, 422 invalid input.
- Class names are exactly `glass`, `metal`, `paper`, `plastic`, `trash` (`src.config.CLASS_NAMES`).
- Local-first and private: the server binds to 127.0.0.1, never phones home, stores data only in
  the SQLite file (`MIRA_DASHBOARD_DB`, default `~/.mira/dashboard.db`).
- Commit on your branch with clear messages, in small steps. Leave the worktree clean.
- Do not edit files owned by another area (section 4). If you need a change there, describe it in
  your report. Shared files (`v1/__init__.py`, `main.py`, `state.py`, `storage.py`, `jobs.py`,
  `events.py`, `model_runner.py`, `0001_core.sql`) are coordinator-owned: only the areas that say so may touch them.

## 4. Ownership

| Area | Owner | Files |
|---|---|---|
| **core** | B1 | `camera_service.py` refactor, `v1/routers/sessions.py`, `v1/recorder.py`, `migrations/0010_sessions.sql`, `tests/dashboard_v2/test_sessions.py` |
| **export** | B2 | `v1/routers/exports.py`, `v1/reports/`, `migrations/0020_export.sql` (only if needed), `tests/dashboard_v2/test_exports.py` |
| **compare + benchmark** | B3 | `v1/routers/compare.py`, `v1/routers/benchmark.py`, `migrations/0030_compare_benchmark.sql`, `tests/dashboard_v2/test_compare.py`, `test_benchmark.py` |
| **batch** | B4 | `v1/routers/batch.py`, `v1/routers/jobs.py`, `v1/batch_runner.py`, `migrations/0040_batch.sql` (only if needed), `tests/dashboard_v2/test_batch.py`, `test_jobs.py` |
| **hardware + arm + events** | B5 | `v1/routers/hardware.py`, `v1/routers/arm.py`, `v1/routers/events.py`, `v1/hardware_sampler.py`, `v1/arm.py`, `migrations/0050_hardware_arm.sql`, `tests/dashboard_v2/test_hardware.py`, `test_arm.py`, `test_events.py` |
| **UI shell** | U1 | `src/dashboard/ui/` (everything) until U2 starts |
| **UI pages** | U2 | `src/dashboard/ui/src/pages/{Sessions,Models,Analytics}/` |

Shared-file rule: a backend agent that must register its router **adds one `include_router` line
for its own router in `v1/__init__.py`** (stubs are already included, so normally no edit is
needed) and, if it needs a table, **adds its own migration file**. Never edit another agent's
migration. Base tables live in `0001_core.sql`; extend them with `ALTER TABLE` in your own
migration, never by editing `0001`.

## 5. Shared primitives (already implemented in the skeleton)

- `get_db()` returns a `Database`: `db.execute(sql, params)`, `db.executemany`, `db.query(sql, params)
  -> list[sqlite3.Row]`, `db.query_one`, and `with db.transaction():`. Thread-safe (one lock,
  `check_same_thread=False`, WAL mode). Row access by column name.
- `get_jobs()` returns a `JobManager`: `submit(kind, fn, *, title="") -> Job` where
  `fn(ctx)` receives a `JobContext` with `ctx.progress(fraction, message="")`, `ctx.cancelled`
  (a `threading.Event`) and returns a JSON-serialisable result dict. Also `get(id)`, `list()`,
  `cancel(id)`. Jobs are mirrored into the `jobs` table. Job `status` is
  `queued | running | completed | failed | cancelled`; `progress` is 0.0 to 1.0.
- `get_events()` returns an `EventBus`: `publish(type, data)` is thread-safe; the WebSocket router
  (B5) fans events out to clients as `{"type", "ts", "data"}`.

Event types (publish these exactly): `session_started`, `session_stopped`, `job_progress`,
`job_finished`, `arm_event`, `hardware_sample`, `detection_batch`.

## 6. Data model (base tables, `0001_core.sql`)

```
sessions(id TEXT PK, name TEXT, source TEXT, model_name TEXT, status TEXT,
         started_at_ts REAL, ended_at_ts REAL, config_json TEXT, notes TEXT)
  source in camera|image|video|batch ; status in active|completed|failed
detections(id INTEGER PK, session_id TEXT, ts REAL, frame_index INTEGER, class_name TEXT,
           confidence REAL, x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER, track_id INTEGER)
metrics(id INTEGER PK, session_id TEXT NULL, ts REAL, fps REAL, latency_ms REAL,
        cpu_percent REAL, memory_percent REAL, temperature_c REAL NULL)
hardware_samples(id INTEGER PK, ts REAL, cpu_percent REAL, memory_percent REAL,
                 temperature_c REAL NULL, load_1m REAL NULL)
jobs(id TEXT PK, kind TEXT, title TEXT, status TEXT, progress REAL, message TEXT,
     created_at_ts REAL, finished_at_ts REAL NULL, result_json TEXT NULL, error TEXT NULL)
comparisons(id TEXT PK, created_at_ts REAL, input_name TEXT, models_json TEXT, results_json TEXT)
benchmark_runs(id TEXT PK, created_at_ts REAL, status TEXT, config_json TEXT,
               results_json TEXT NULL, job_id TEXT NULL)
arm_events(id INTEGER PK, ts REAL, kind TEXT, class_name TEXT NULL, track_id INTEGER NULL,
           payload_json TEXT, correct INTEGER NULL)
```

Indexes exist on `detections(session_id, ts)`, `metrics(session_id, ts)`, `hardware_samples(ts)`,
`arm_events(ts)`.

## 7. HTTP API v1 (prefix `/api/v1`)

### Sessions (B1)
- `POST /sessions` body `{name?: str, source: "camera"|"image"|"video"|"batch", model_name?: str}`
  -> `201` session. While a session is `active` and the stream runs, the recorder stores every
  detection and metrics sample against it. Only one `camera` session may be active (409).
  Auto-name when empty: `Session YYYY-MM-DD HH:MM`.
- `POST /sessions/{id}/stop` -> session (sets `completed`, `ended_at`).
- `GET /sessions?limit=50&offset=0&status=` -> `{sessions: [...], total}`; each item has
  `id, name, source, model_name, status, started_at, ended_at, duration_seconds, total_detections,
  class_counts: {glass: n, ...}, avg_confidence`.
- `GET /sessions/{id}` -> that object plus `config`, `notes`.
- `PATCH /sessions/{id}` body `{name?, notes?}` -> session.
- `DELETE /sessions/{id}` -> `204` (cascades detections and metrics; 409 if active).
- `GET /sessions/{id}/detections?limit=500&offset=0&class_name=&min_confidence=` ->
  `{detections: [{ts, offset_seconds, frame_index, class_name, confidence, bbox:[x1,y1,x2,y2],
  track_id}], total}`.
- `GET /sessions/{id}/timeline?bucket_seconds=1` -> `{duration_seconds, bucket_seconds,
  buckets: [{start_offset, objects, class_counts, avg_confidence, fps, latency_ms}]}`. This powers
  the replay scrubber.
- Also in this area: split `camera_service.py` into smaller modules (input source, inference
  worker, tracker) **without changing behaviour**; existing tests must keep passing. Add the
  recorder that attaches to the existing detection and metrics callbacks. Verify that
  `src/dashboard/backend` is included in a built wheel (`python -m build --wheel`, inspect the zip;
  the package dirs have no `__init__.py`, so `packages.find` may skip them): fix the packaging if
  it does not, and make `[tool.setuptools.package-data]` include `src/dashboard/frontend/dist/**`.

### Export (B2)
- `GET /sessions/{id}/export.csv` -> `text/csv`, header
  `ts,offset_seconds,frame_index,class_name,confidence,x1,y1,x2,y2,track_id`; streamed, with
  `Content-Disposition: attachment; filename="<slug>-<id8>.csv"`.
- `GET /sessions/{id}/export.json` -> `application/json` attachment: `{session, class_counts,
  detections: [...], metrics: [...]}`.
- `GET /sessions/{id}/report.html` -> a self-contained HTML page (inline CSS and inline SVG charts,
  no external requests) that fits **one A4 page** when printed (`@media print`, `@page { size: A4;
  margin: 12mm }`): title, name, date, model, duration, totals, class table, per-class bar chart,
  detections-over-time chart, average confidence, a notes block, and the line "Session counts describe this run only and are not real-world sorting accuracy."
  Escape all user text.
- `GET /sessions/{id}/report.html?download=1` sets an attachment header.

### Compare (B3)
- `POST /compare` multipart: `image` (JPEG/PNG, max 8 MB), `models` (comma separated, 2 to 4
  names from `GET /api/models`), `confidence` (0.05-1, default 0.25). Runs each model on the same
  image, **sequentially** (no shared mutable model state) and returns
  `{id, input_name, models: [{name, latency_ms, objects, class_counts, avg_confidence,
  detections: [...], annotated_image: "data:image/jpeg;base64,..."}], winner_hint: {...}}`.
  Stored in `comparisons`.
- `GET /compare?limit=20` -> list (no images). `GET /compare/{id}` -> full record.
- `DELETE /compare/{id}` -> 204.

### Benchmark (B3)
- `POST /benchmark/runs` body `{models: [name,...], dataset?: str (path to a YOLO dataset.yaml or
  folder; default: the project default), confidence: 0.25, max_images?: int}` -> `202
  {run_id, job_id}`. Runs `src.pipeline.benchmark.ModelBenchmark` in a job with progress.
- `GET /benchmark/runs?limit=20` -> list. `GET /benchmark/runs/{id}` -> `{id, status, config,
  results: [{model, map50, map50_95, precision, recall, f1, avg_latency_ms, fps, per_class: {...},
  errors}] | null, job_id}` (use whatever `BenchmarkResult` provides; document the exact fields).
- `DELETE /benchmark/runs/{id}` -> 204.

### Batch and jobs (B4)
- `POST /batch/video` multipart: `video` (mp4/avi/mov/mkv, max 500 MB), `model_name`,
  `confidence` (default 0.25), `frame_stride` (default 5, 1 to 120), `name?` -> `202
  {job_id, session_id}`. Decodes with OpenCV, runs the model on every Nth frame, records detections
  to a new `video` session with `ts = start + frame_time`, reports progress, supports cancel.
- `POST /batch/images` either multipart `images` (up to 200 files) or JSON `{directory: str,
  recursive: false}` (local folder, must exist, JPEG/PNG only, max 2000 files, no symlink
  following), plus `model_name`, `confidence`, `name?` -> `202 {job_id, session_id}`; creates a
  `batch` session.
- `GET /jobs?limit=50` -> `{jobs: [...]}`; `GET /jobs/{id}` -> `{id, kind, title, status, progress,
  message, created_at, finished_at, result, error}`; `POST /jobs/{id}/cancel` -> job (409 if
  finished).

### Hardware (B5)
- A background sampler (started in the app lifespan, every `MIRA_HARDWARE_INTERVAL` seconds,
  default 2) stores CPU, memory, load and temperature to `hardware_samples`; keep 24 h
  (`MIRA_HARDWARE_RETENTION_HOURS`), prune hourly. Temperature: `psutil.sensors_temperatures()`,
  then `/sys/class/thermal/thermal_zone0/temp`, then `vcgencmd measure_temp` (Raspberry Pi); `null`
  when unavailable. Publish a `hardware_sample` event every 5th sample.
- `GET /hardware/current` -> `{ts, cpu_percent, memory_percent, memory_used_mb, memory_total_mb,
  temperature_c, load_1m, platform, is_raspberry_pi, cpu_count}`.
- `GET /hardware/history?minutes=60&points=240` -> `{points: [{ts, cpu_percent, memory_percent,
  temperature_c}], minutes}` downsampled by averaging into at most `points` buckets.

### Sorting arm (B5): placeholder, no real hardware
- `GET /arm/status` -> `{connected: false, mode: "simulated", state: "idle"|"busy", queue_length,
  last_event_at, accuracy: float|null, total_feedback: int}`.
- `POST /arm/commands` body `{action: "sort"|"home"|"stop", class_name?, track_id?}` -> `202`
  event. Simulated: log an `arm_events` row (`kind` = `sort_requested`/`sort_completed`, ...) and
  publish `arm_event`. Reject unknown classes with 422. **Nothing here may talk to hardware.** Put
  the simulator behind an `ArmDriver` protocol (`send(command) -> result`) with a `SimulatedArm`
  implementation, so a real driver can replace it later.
- `GET /arm/events?limit=100&kind=` -> `{events: [...]}`.
- `POST /arm/events/{id}/feedback` body `{correct: bool}` -> event; `GET /arm/accuracy` ->
  `{accuracy: float|null, correct: int, total: int}`. Use this to fill the existing
  `Statistics.sorting_accuracy` field in `GET /api/statistics`.

### Events WebSocket (B5)
- `WS /ws/v1/events`: on connect sends `{"type":"hello","ts":...,"data":{"version":1}}`, then every
  `EventBus` event as `{"type","ts","data"}`. Slow clients get dropped events, never block
  publishers. Heartbeat `{"type":"ping"}` every 20 s.

## 8. UI

- Location `src/dashboard/ui/`: Svelte 5 (runes) + Vite + TypeScript, **pnpm** (use
  `corepack pnpm ...`), no Tailwind needed (plain CSS with the Orchard tokens). Build output goes
  to `src/dashboard/frontend/dist/`, served by FastAPI at `/` (coordinator wires this up).
- Look: **light theme only**, Orchard tokens from `docs/dashboard-v2/orchard-tokens.css`
  (`--app #f5f5f5`, `--surface #fefefe`, `--accent #5173c5`, radii 10/14/18/22 px, Plus Jakarta
  Sans, Space Mono for numbers/labels, class colours `--class-*`). Copy the tokens into
  `src/dashboard/ui/src/styles/tokens.css`; do not import from `website/`. Do not copy Orchard
  source or assets (AGPL); the look is MIRA's own, as on the website.
- Layout: left sidebar (Detect, Sessions, Models, Analytics, Settings, with small status dots), a
  compact top status bar (model, connection, stream state, current session), content area.
  Keyboard accessible, visible focus rings, WCAG AA contrast, `prefers-reduced-motion` respected.
- Talks only to `/api/v1`, the existing `/api/*` routes and `/ws/video`, `/ws/v1/events`.
  Route table for the old API: `/api/status`, `/api/models`, `/api/camera/initialize`,
  `/api/model/load`, `/api/stream/start|stop`, `/api/detect/image`, `/api/statistics`,
  `/api/metrics/history`, `/api/detections/recent`.
- All API calls go through one typed client (`src/lib/api.ts`) so a mock layer (`VITE_MOCK=1`) can
  replace the server during UI work. Mock fixtures follow section 7 exactly.
- Pages: **Detect** (camera or image, live preview with boxes, start/stop session, session name),
  **Sessions** (list, detail, replay scrubber, export buttons), **Models** (compare, benchmark),
  **Analytics** (session and hardware charts, arm event log), **Settings** (camera, model,
  thresholds). Charts are hand-rolled SVG or a tiny dependency-free helper; no chart library.
- Copy: plain, specific, no marketing tone, no em dashes. English only for now.

## 9. Skeleton notes (what exists after the coordinator commit)

- `v1/model_runner.py` (coordinator-owned): `list_models()`, `resolve_model_path(name)`,
  `load_model(name)` (cached, 2 models), `predict_frame(name, frame_bgr, confidence, iou) ->
  RunnerResult(detections: list[RunnerDetection], latency_ms)`, `set_model_factory(fn)` for tests.
  **Compare, benchmark and batch must load and run models through it**, not through
  `camera_service` (which core is refactoring) and not by calling `YOLO(...)` directly.
- Routers use paths relative to their prefix: `/api/v1` for HTTP routers, `/ws/v1` for
  `routers/events.py`. Write `@router.get("/sessions")`, not `"/api/v1/sessions"`.
- A router module may define `async def on_startup()` / `async def on_shutdown()`; `v1.startup()`
  and `v1.shutdown()` call them from the FastAPI lifespan. Use this for background workers.
- `tests/conftest.py` points `MIRA_DASHBOARD_DB` at a temp file for every test and resets the
  singletons, so tests never touch `~/.mira`. Use `TestClient(app)` as a context manager so the
  lifespan runs.
- Tests: `tests/dashboard_v2/test_skeleton.py` shows how storage, jobs and events are exercised.
