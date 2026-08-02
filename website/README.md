# MIRA website

Static project website for MIRA. It contains a public overview, the research record, and task-focused documentation. It intentionally does not run model inference in the browser.

## Run locally

From the repository root:

```powershell
py -3 -m http.server 4173 --directory website
```

Open `http://localhost:4173/`.

## Pages

- `index.html`: project overview
- `research.html`: experiment progression, current charts, metrics, and limitations
- `docs.html`: quickstart, how-to guides, explanations, and reference
- `styles.css`: shared visual system and responsive layouts
- `app.js`: navigation, accessible research charts, reveal effects, copy buttons, and documentation search

Research charts are generated from the recorded EXP-001 through EXP-019 metrics in `app.js`. Each chart includes a screen-reader-accessible data table.
