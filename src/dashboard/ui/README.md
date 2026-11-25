# MIRA dashboard UI (v2)

Svelte 5 (runes) + Vite + TypeScript. Plain CSS with the Orchard look from `docs/dashboard-v2/orchard-tokens.css`.
Light theme only. No chart library, no UI kit, no router library, no CDN: fonts are bundled.

The production build is written to `../frontend/dist/` (`src/dashboard/frontend/dist/`), which FastAPI serves at `/`.
That folder is gitignored and built in CI.

## Run it

Use pnpm through corepack (`corepack pnpm ...`). Node 22 or newer.

```bash
cd src/dashboard/ui
corepack pnpm install

corepack pnpm dev          # dev server on http://127.0.0.1:5173, proxies /api and /ws to the backend
corepack pnpm dev:mock     # same, but every API and WebSocket call is answered by the in-browser mock
corepack pnpm build        # type checks are separate; this writes ../frontend/dist
corepack pnpm preview      # serves the last build
corepack pnpm check        # svelte-check, fails on any error or warning
corepack pnpm test         # Vitest
```

- The dev proxy targets `http://127.0.0.1:8000` by default. Point it elsewhere with
  `MIRA_API_TARGET=http://127.0.0.1:8011 corepack pnpm dev` (PowerShell: `$env:MIRA_API_TARGET="..."`).
- `VITE_MOCK=1 corepack pnpm dev` is the same as `pnpm dev:mock`.
- The backend is started separately, for example `python -m uvicorn src.dashboard.backend.main:app --host 127.0.0.1 --port 8000`.

## Pages

| Route | Page | What it does |
|---|---|---|
| `#/detect` | Detect | Camera or image detection, live preview with boxes, session start and stop. |
| `#/sessions` | Sessions | Newest first list with Live and status badges, load more, and the Import panel (video, images or a folder). |
| `#/sessions/<id>` | Session detail | Totals, class bars, export (CSV, JSON, HTML report), rename and notes, delete with confirmation, replay. |
| `#/models` | Models | **Compare**: two to four models on one image, annotated results, winner hint, past comparisons. **Benchmark**: a run with live progress, results table, per-class details, errors, past runs. |
| `#/analytics` | Analytics | Session charts (objects over time, class mix), hardware (current tiles, 15 min to 24 h history), sorting arm (no-robot banner, accuracy, simulated test sort, event log with feedback). |
| `#/settings` | Settings | Camera and model settings with inline validation. |

### Sessions

- **List.** Sorted newest first by `started_at` (the page sorts; the server order is not relied on). A camera session
  that is still recording shows a **Live** badge. Active sessions cannot be deleted; the page says why.
- **Import.** Video (MP4, AVI, MOV, MKV, up to 500 MB, frame stride 1 to 120), image files (JPEG or PNG, up to 200),
  or a folder path (`recursive: false`). The job is polled every second. Cancel is available while it runs. When it
  finishes, the list reloads and the panel links to the session. An import started before the page opened is picked up
  from `/jobs`.
- **Detail.** Totals, class breakdown, and the export links. The report opens in a new tab; print it to save a PDF.
- **Replay.** The timeline buckets come from `/sessions/{id}/timeline`. The bucket width is chosen so the timeline has
  at most 240 columns. The detections are read in pages of 500, up to 5000 rows; a notice says when the replay is cut
  short. Play and pause, speeds 1x, 2x and 4x (1x is the recorded pace), a scrubber, stacked class bars, and the
  detections in the current bucket. Playback pauses when the page is hidden.

### Models

- **Compare.** Pick two to four models and one JPEG or PNG (drop it or choose it). The results show the annotated image,
  latency, objects, class counts and average confidence for each model. The winner hint is shown as plain sentences
  with the note the server sends. A saved comparison reopens with its numbers only: the server keeps no images, and
  the page says so.
- **Benchmark.** Pick one to six models, an optional dataset path, a confidence and a maximum image count. The run is
  polled every second and can be cancelled. Missing values (for example FPS, which the benchmark never measures) show
  as a dash, never as a number. Errors reported per model are shown above the table.

### Analytics

- **Session.** Choose a session (the latest by default). Objects over time is a line chart; the class mix is a bar list.
- **Hardware.** Current CPU, memory, temperature and load are refreshed every 5 seconds; the history every 30 seconds.
  Without a temperature sensor the tile reads "No temperature sensor" and the chart is replaced by that state. A Raspberry
  Pi gets a short note on where its temperature comes from.
- **Sorting arm.** Shows "No robot connected. Commands are simulated." while `connected` is false. Accuracy comes from
  `/arm/accuracy`. Correct and incorrect feedback is only offered on `sort_completed` events. The log updates from the
  events feed and is refreshed every 10 seconds as a fallback.

## Charts and shared pieces

- `lib/components/charts/LineChart.svelte`, `StackedBars.svelte`, `BarList.svelte`: hand-drawn SVG (or HTML for the bar
  list). Each one is sized in pixels from its container, has a title and a text description, shows gaps for missing
  values, and offers a **Show data table** toggle where a table helps.
- `lib/charts/scale.ts`: linear scales, nice ticks, line paths with gaps. Pure, tested.
- `lib/poll.ts`: `startPolling(task, { intervalMs })`. It never overlaps a call, reports errors and keeps going, and
  pauses while the page is hidden. Every page uses it for refreshes.
- `lib/jobs/job-progress.ts`: applies `job_progress` and `job_finished` events to a job, and labels its progress.

## Mock mode

`VITE_MOCK=1` (or `dev:mock`) replaces `fetch` and the WebSocket with an in-browser stand-in (`src/lib/mock/`):

- Every route in `src/lib/api/endpoints.ts` is answered with the status codes and error shapes of the backend
  (409 with `missing` for the stream, 415 and 413 for images and videos, 422 validation lists and detail strings,
  404 `Not Found` for an unknown route, 404 with a message for an unknown id).
- **Sessions** (eight, about 100 to 700 detections each). Detections and timelines are generated from the class counts,
  so the totals always agree. One import is still running, and its progress and counts move with time.
- **Jobs and runs move with time.** A job's progress is computed from the clock when it is read; there are no timers
  to drift. Benchmark results appear model by model. Import sessions fill up as the job moves. Cancel works.
- **Compare** results carry annotated JPEGs drawn on a canvas (the browser draws the boxes). The stored record has no
  images, as on the server.
- **Arm.** A simulated sort completes about 1.2 seconds after the request and arrives on the events socket.
- **Events socket.** `/ws/v1/events` sends the hello and pings, job progress and completion, session start and stop,
  arm events, and a hardware sample every 5 seconds. The clock ticks once a second.
- **Starting the stream** makes the fake `/ws/video` send generated JPEG frames (about 4 per second) with random boxes,
  and metrics once a second.
- Developer hooks in the browser console: `__miraMock.dropSockets()` closes the mock sockets to test the reconnect
  states; `__miraMock.hardwareSensor(false)` removes the temperature reading, to see the no-sensor state.
- Export links (`export.csv`, `export.json`, `report.html`) are real navigations, so they need the real server.

The mock is excluded from the production build. Check: `grep -r mira-mock-layer-v1 ../frontend/dist` finds nothing.

## Against the real server

| Route | Status |
|---|---|
| `GET /api/status`, `GET /api/models` | used, works |
| `POST /api/camera/initialize`, `POST /api/model/load` | used by Settings and the Detect steps |
| `POST /api/stream/start`, `POST /api/stream/stop` | used; a 409 with `missing` shows the steps still to do |
| `POST /api/detect/image` | used; raw body with `image/jpeg` or `image/png` |
| `GET /api/statistics`, `GET /api/detections/recent`, `GET /api/metrics/history` | used (metrics history is typed and tested; the Detect statistics panel does not draw it yet) |
| `WS /ws/video` | used for the live preview and the status bar connection state |
| `WS /ws/v1/events` | used by the shell and the arm log |
| `/api/v1/sessions*` | the Sessions page. Built against CONTRACT section 7; the sessions router on this branch is still a stub, so these routes answer 404 until it lands and the pages show "not available yet" |
| `/api/v1/compare*`, `/api/v1/benchmark/runs*`, `/api/v1/batch/*`, `/api/v1/jobs*` | the Models and Sessions import pages. Types follow the routers on this branch |
| `/api/v1/hardware/*`, `/api/v1/arm/*` | the Analytics page |

Routes that answer 404 `Not Found`, 405 or 501 show "not available yet" instead of an error.

## Structure

```
src/
  main.ts                 mounts App, loads fonts and styles
  App.svelte              shell: sidebar, status bar, page switch, realtime start-up
  styles/
    tokens.css            Orchard design tokens (copied from docs/dashboard-v2, Tailwind glue removed)
    base.css              base elements, focus rings, touch targets, reduced motion
  lib/
    api/                  typed client: client.ts (HTTP), errors.ts (ApiError, 404 handling), endpoints.ts, index.ts (api)
    realtime/             reconnecting WebSocket (backoff), /ws/video state reducer, /ws/v1/events feed
    mock/                 mock fetch, fake sockets, in-memory backend, fixtures, job clock, canvas annotation
    stores/               Svelte 5 stores: system (status, models, session), live (video), settings, detect, router, toasts
    components/           design system (Button, Card, Field, Select, Slider, Toggle, Table, Dialog, ...)
    components/charts/    LineChart, StackedBars, BarList
    charts/scale.ts       chart geometry (pure)
    jobs/job-progress.ts  job progress and labels (pure)
    layout/               Sidebar, StatusBar
    types.ts              wire types (legacy routes and CONTRACT section 7, checked against the v1 routers)
    poll.ts               visibility-aware polling
    status-summary.ts, settings-model.ts, router.ts, format.ts, classes.ts, toast-queue.ts
  pages/
    Detect/               readiness steps, live preview, image panel, sessions, statistics (+ detect-logic.ts, detect-actions.ts)
    Sessions/             Sessions.svelte (list or detail), SessionList, ImportPanel, SessionView, SessionReplay
                          (+ import-logic.ts, replay-logic.ts, session-list.ts)
    Models/               Models.svelte (tabs), CompareTab, BenchmarkTab (+ models-logic.ts)
    Analytics/            Analytics.svelte, SessionAnalytics, HardwarePanel, ArmPanel (+ analytics-logic.ts)
    Settings/             camera and model settings with inline validation
```

Tests sit next to the code (`*.test.ts`): API client and errors, endpoints, the router, chart scales, polling, job progress,
the replay maths, session and import rules, model and benchmark rules, analytics rules, the mock fixtures and routes,
the stores, and the Detect logic.

## Add a page

1. Make a folder `src/pages/<Name>/` with `<Name>.svelte` as the default export. Start from `pages/Sessions/Sessions.svelte`.
2. Add the route name to `ROUTES` and its title to `ROUTE_TITLES` in `src/lib/router.ts`.
3. Map the route to the component in `pages` in `src/App.svelte`.
4. Add a nav icon in `src/lib/layout/Sidebar.svelte` (`ICONS`) and, if the item needs a status dot, its rule in `dotFor`.
5. Call the API through `api.legacy` or `api.v1` from `src/lib/api`. Use `describeError` for messages, and
   `isRouteMissing` to show "not available yet" when a v1 route is not there yet.

Use the components in `src/lib/components/`: `PageHeader`, `Card`, `EmptyState`, `Notice`, `Table`, `Tabs`,
`SegmentedControl`, `StatTile`, `Sparkline`, `Dialog`, `Field` with `TextInput`, `Select`, `Slider`, `Toggle`, and the charts.
Every Svelte file that uses TypeScript needs `<script lang="ts">`, or svelte-check cannot resolve `.svelte` imports.

## Conventions

- Plain, specific English copy. No em dashes anywhere (use commas, periods or colons).
- Colours only as tokens. Text uses `--ink` and `--ink-soft` or `--accent-strong`. `--ink-faint` and the accent colour
  itself fail AA as text on the app background. Bin colours are for fills, boxes and chips.
- Every icon-only button has an `aria-label`. Status dots always come with words.
- Motion is opacity and transform only. `prefers-reduced-motion` removes it.
- Touch targets are at least 44 px on coarse pointers.
- Below 900 px the sidebar becomes a bottom tab bar, `--tabbar-height` (4 rem). Toasts sit just above it. Check that
  `document.documentElement.scrollWidth` equals the viewport width at 360 px on every page.
- Toasts: bottom right on desktop, above the tab bar on phones, at most three at once, each dismissed after a few seconds.
- Forms validate on submit with the same limits as the server. The server stays the authority.

## Open questions for the contract (not changed here)

- `/api/status` has no model name and there is no GET for the camera or model configuration. The UI keeps the
  last applied settings in the browser (`localStorage`) and shows the saved model name in the status bar.
  Proposal: add `model_name` and the current `camera` and `model` configs to `/api/status`.
- `/ws/control` is not in the contract. The status bar shows the state of `/ws/video` as the connection.
- `POST /api/v1/sessions` is typed as the session detail shape. The contract says "session" without listing its fields,
  and the sessions router is still a stub.
- Compare records keep no annotated image, so reopened comparisons show numbers only. Proposal: store the annotated JPEG
  (or the input image) with the comparison.
- The session detections list has no time window. The replay pages through the list and filters in the browser.
  Proposal: `from_offset` and `to_offset` on `GET /sessions/{id}/detections`.
- A job does not say which session it writes to until it finishes (`result.session_id` is assumed). Proposal: add
  `session_id` to the job payload while it runs.
- `hardware_sample` events carry `ts` as an epoch number, while the envelope and HTTP payloads use ISO strings. The UI
  does not use the event for charts; it polls `/hardware/*` instead.
- `job_progress` and `job_finished` data are keyed by `job_id`, not `id`. The UI handles that.
- The result of `Job` for batch jobs is not specified (`result` is typed loosely).
