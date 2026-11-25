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

## Mock mode

`VITE_MOCK=1` (or `dev:mock`) replaces `fetch` and the WebSocket with an in-browser stand-in (`src/lib/mock/`):

- Every route in `src/lib/api/endpoints.ts` is answered with the same status codes and error shapes as the
  contract: 409 with `missing` for the stream, 415 and 413 for images, 422 validation lists, 404 `Not Found` for
  an unknown route and 404 with a message for an unknown id.
- Starting the stream makes the fake `/ws/video` send generated JPEG frames (about 4 per second) with random boxes,
  and metrics once a second. The UI draws the boxes over the frames.
- `/ws/v1/events` sends a hello, pings and a hardware sample every 5 seconds.
- Sessions, comparisons, benchmarks, batch jobs, hardware and the arm are held in memory and reset on reload.
- Developer hook: in the browser console, `__miraMock.dropSockets()` closes the mock sockets to test the reconnect states.
- Export links (`export.csv`, `export.json`, `report.html`) are real navigations, so they need the real server.

The mock is excluded from the production build. Check: `grep -r mira-mock-layer-v1 ../frontend/dist` finds nothing.

## Against the real server

What the UI calls today and what it expects:

| Route | Status with the current backend |
|---|---|
| `GET /api/status`, `GET /api/models` | used, works |
| `POST /api/camera/initialize`, `POST /api/model/load` | used by Settings and the Detect steps |
| `POST /api/stream/start`, `POST /api/stream/stop` | used; a 409 with `missing` shows the steps still to do |
| `POST /api/detect/image` | used; raw body with `image/jpeg` or `image/png` |
| `GET /api/statistics`, `GET /api/detections/recent`, `GET /api/metrics/history` | statistics and recent detections are used; metrics history is typed and tested but not drawn yet |
| `WS /ws/video` | used for the live preview and the status bar connection state |
| `WS /ws/v1/events` | opened by the shell; the feed is available for the pages that need events |
| `/api/v1/*` | used for sessions. While a route is missing (404 `Not Found`, 405 or 501) the pages show "not available yet" and the session controls stay disabled |

Real backend check run while building this UI: `/api/status` and `/api/models` answer 200, and `/api/v1/*` answers
404 `{"detail":"Not Found"}` until the v1 routers land.

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
    mock/                 mock fetch, fake sockets, in-memory backend, fixtures, generated frames
    stores/               Svelte 5 stores: system (status, session), live (video), settings, detect, router, toasts
    components/           design system (Button, Card, Field, Select, Slider, Toggle, Table, Dialog, ...)
    layout/               Sidebar, StatusBar
    types.ts              wire types (legacy routes and CONTRACT section 7)
    status-summary.ts     status bar wording, pure
    settings-model.ts     settings defaults, validation, storage parsing, pure
    router.ts             hash routes, pure
    format.ts, classes.ts formatting helpers, class names and colours
  pages/
    Detect/               readiness steps, live preview, image panel, sessions, statistics (+ detect-logic.ts, detect-actions.ts)
    Settings/             camera and model settings with inline validation
    Sessions/ Models/ Analytics/   placeholders for U2
```

Tests sit next to the code (`*.test.ts`): API client and errors, endpoints, reconnect backoff, video reducer,
settings and status rules, the mock fixtures and routes, the stores, and the Detect logic.

## Add a page

1. Make a folder `src/pages/<Name>/` with `<Name>.svelte` as the default export. Start from `pages/Sessions/Sessions.svelte`.
2. Add the route name to `ROUTES` and its title to `ROUTE_TITLES` in `src/lib/router.ts`.
3. Map the route to the component in `pages` in `src/App.svelte`.
4. Add a nav icon in `src/lib/layout/Sidebar.svelte` (`ICONS`) and, if the item needs a status dot, its rule in `dotFor`.
5. Call the API through `api.legacy` or `api.v1` from `src/lib/api`. Use `describeError` for messages, and
   `isRouteMissing` to show "not available yet" when a v1 route is not there yet.

Use the components in `src/lib/components/`: `PageHeader`, `Card`, `EmptyState`, `Notice`, `Table`, `Tabs`,
`SegmentedControl`, `StatTile`, `Sparkline`, `Dialog`, `Field` with `TextInput`, `Select`, `Slider`, `Toggle`.
Every Svelte file that uses TypeScript needs `<script lang="ts">`, or svelte-check cannot resolve `.svelte` imports.

## Conventions

- Plain, specific English copy. No em dashes anywhere (use commas, periods or colons).
- Colours only as tokens. Text uses `--ink` and `--ink-soft` or `--accent-strong`. `--ink-faint` and the accent colour
  itself fail AA as text on the app background. Bin colours are for fills, boxes and chips.
- Every icon-only button has an `aria-label`. Status dots always come with words.
- Motion is opacity and transform only. `prefers-reduced-motion` removes it.
- Touch targets are at least 44 px on coarse pointers.
- Below 900 px the sidebar becomes a bottom tab bar. Check that `document.documentElement.scrollWidth` equals the
  viewport width at 360 px on every page.

## Open questions for the contract (not changed here)

- `/api/status` has no model name and there is no GET for the camera or model configuration. The UI keeps the
  last applied settings in the browser (`localStorage`) and shows the saved model name in the status bar.
  Proposal: add `model_name` and the current `camera` and `model` configs to `/api/status`.
- `/ws/control` is not in the contract. The status bar shows the state of `/ws/video` as the connection.
- Compare and benchmark list endpoints: the UI accepts a bare array or a wrapped object (`comparisons`, `runs`).
- `winner_hint`, the compare detection shape, `per_class` and `errors` in benchmark results, and the arm event JSON
  (`payload`) are typed loosely (`OPEN:` markers in `src/lib/types.ts`).
- `ts` in hardware and event payloads is typed as an ISO string.
- Benchmark status values are assumed to match the job statuses.
