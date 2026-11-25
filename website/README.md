# MIRA website (SvelteKit)

Project site for MIRA (Machine Intelligence for Recycling Automation), a Jugend forscht 2027 project: a YOLO11n waste detector and the open-source `mira-ai` Python package. English and German.

SvelteKit 2, Svelte 5 (runes), Vite 8, Tailwind CSS 4 (`@tailwindcss/vite`), Three.js (`three` ^0.180) for the Home figure, pnpm, oxlint and oxfmt. The site is **fully static** (`@sveltejs/adapter-static`, output in `build/`): there is no server at runtime. Tooling follows the stack of the Orchard landing app; no Orchard code or assets are used (Orchard is AGPL-3.0, MIRA is MIT) and the look is MIRA's own.

> **Status: all pages are ported.** Home (the combined version, see "Home"), Research, Package and the Docs (index plus one page per guide, with search) exist here in English and German. This SvelteKit site **replaces the Next.js site after the owner approves it**. Until then `../website-next/` (the Next.js site) remains the reference for wording and numbers: do not edit it. The text of Research, Package and Docs matches it, apart from the German changes listed under "Voice". Home is a combined version on purpose.
>
> **Before the site is public**, an Impressum and a Datenschutzerklärung must be written (see "Not written yet: legal pages"). Neither exists.

## Run

```bash
pnpm install
pnpm dev            # http://localhost:5173  ("/" redirects to /en or /de in the browser)
pnpm check          # svelte-kit sync + svelte-check (types, a11y warnings)
pnpm test           # Vitest: i18n, docs content and search, experiments, figures, metadata, rich text, counter, video, sitemap
pnpm lint           # oxlint
pnpm format         # oxfmt (TypeScript, CSS, JSON; it does not format .svelte files)
pnpm build          # static site into ./build
npx serve build -l 4360   # preview the build (serve resolves /en to en.html because cleanUrls is on)
```

`pnpm` is not installed globally on every machine: `corepack pnpm <script>` works the same.

The build writes `en.html`, `de.html`, `en/research.html` and so on (no `index.html` per folder). A plain `python -m http.server` will not resolve `/en`; use `serve` or any host with clean URLs. Pages are listed as URLs without `.html`.

## Structure

```
src/
  app.html                 <html lang="%lang%">: hooks.server.ts fills the language at prerender time
  app.css                  ALL design tokens (palette, class colours, type scale, motion) and the contrast table
  hooks.server.ts          sets <html lang> from the first URL segment and preloads the three first-paint fonts
  params/lang.ts           route matcher: only "en" and "de" match, everything else is a 404
  i18n/                    typed dictionaries (en.ts defines the shape, de.ts must match), format.ts,
                           not-found.ts, docs/ research/ package/ (long copy, one parity test each)
  lib/
    site.ts                links, nav, CLASSES, FACTS, SITE_URL, FALLBACK_DOWNLOADS, PYPI_LATEST_VERSION
    metadata.ts            pageMetadata(): title, canonical, hreflang, Open Graph, Twitter (pure, tested)
    figures.ts             typed loader for src/lib/figures-data/detections.json (validates every entry)
    experiments.ts         the experiment data behind Research and the Home numbers
    hf-downloads.ts        pure counter logic (fetch, validate, cache); use-hf-downloads.svelte.ts is the Svelte state
    rich.ts                the safe inline-markup parser behind <Rich>
    docs-content*.ts       docs page lookup, search index and search
    components/            primitives (below); home/, research/, package/ and docs/ hold the parts of their
                           pages; scene/ holds the 3D code
  routes/
    +layout.svelte         fonts (self-hosted @fontsource-variable) and app.css
    +page.svelte           "/": client side language redirect, plain links and <noscript> text without JS
    404/+page.svelte       prerendered to build/404.html (both languages, own wordmark)
    +error.svelte          the same 404 for client side navigation outside a language
    [lang=lang]/           every real page. +layout.svelte: skip link, header, footer. +error.svelte: 404 inside a language
    sitemap.xml/, robots.txt/   prerendered endpoints
static/                    mira.svg, og-en.png, og-de.png, figures/ (real photos, CREDITS.md, charts)
  src/lib/figures-data/     detections.json, imported at build time (not a public asset)
vercel.json                clean URLs, redirects from the old .html URLs, security and cache headers
```

### Primitives (`src/lib/components/`)

`Canvas` (wide, nearly edge-to-edge canvas with Orchard page gutters), `Prose` (66ch column), `Chapter` (rule + display h2 + content), `Heading`, `Figure` and `FigureCaption`, `DetectionFigure` (photo with boxes; 2D fallback and 3D host), `MarginNote` (a `div role="note"`, never an `aside`), `Stat`, `ClassChip`, `Rich` (markers, code spans and links from dictionary strings), `ExtLink`, `CopyCommand`, `DemoVideo` and `YouTubeEmbed`, `DownloadsStat`, `Seo`, `SiteHeader`, `SiteFooter`, `LanguageSwitch`, `NotFoundView`, `GlobalNotFound`.

Svelte differs from the React site in three ways: there is no `cn()` / type-scale gotcha (class strings are plain, so keep conflicting utilities out of one element), text-with-markup props are Snippets (`{#snippet caption()}...{/snippet}`), and page language reaches deep components through `page.params.lang` (`Rich`) or an explicit `lang` prop.

## Design rules

Adapted from the Hack Club Orchard UI system (visual language only; Orchard is AGPL-3.0, MIRA is MIT). Light theme only: app `#f5f5f5`, surface `#fefefe`, raised `#ffffff`, sunken `#ececec`, rule `#e3e3e3`, ink `#1f1f1f`, soft ink `#535253`, faint `#7c7c7c`. The accent is Orchard blue `#5173c5` (`#395cb8` for text, `#eef0f5` tint, `#4565b6` hover). The former highlighter yellow is gone: emphasis is a black stroke, primary buttons are black, secondary buttons are blue on a blue tint. Class colours (German bin colours) remain data-only on detections, chips and charts. Plus Jakarta Sans for text and display, Space Mono for numbers and commands. Orchard's radius scale (control 10px, card 14px, panel 18px, widget 22px, sheet 28px, buttons 12px) and spacing scale; page gutter 20px, 58px from `md`. Hairlines, numbered figures, margin notes; no gradients or emoji. Motion is opacity and transform at 140/220ms, off with `prefers-reduced-motion`. Tokens are at the top of `src/app.css`.

Research and Package use `research/ResearchShell.svelte`: an Orchard-style docs shell with a filterable section pane on the left, the article in the middle and an "on this page" list on the right. Below `lg` the section pane becomes a native dialog. Section labels come from the existing research and package dictionaries, so no copy is duplicated. The Docs section keeps its own `DocsShell`, which follows the same layout pattern.

Voice: first person ("ich") where honest, on Home and Research (the author's own statements). On Package and Docs the English keeps "I" as in the reference, but the German is formal "Sie" or neutral wording with no "ich" (six lines were rewritten, in `i18n/package/de.ts` and `i18n/docs/de.ts`, facts unchanged); no em or en dashes (the dictionary tests fail on them); never claim real-world accuracy; the robot is not built and there is no real-camera evaluation. PyPI latest is 1.0.2 (`PYPI_LATEST_VERSION`); the repository's 1.0.3 is unreleased and must never be shown as current.

### The artwork rule (owner instruction)

Do **not** draw, generate or hand-author illustrations, icon sets or decorative art. The only visuals are: the real TrashNet photos and the model's real boxes (`static/figures`, `detections.json`), charts built from the recorded numbers, typography, and real CLI command text. That is why there is no icon library and no decorative SVG in the project (`static/mira.svg` is the MIRA logo mark, used as the favicon and in the header and footer).

## Home (the combined version)

Order of `routes/[lang=lang]/+page.svelte`; all copy comes from `src/i18n/{en,de}.ts` (`home.*`):

1. **Hero** (`home/Hero.svelte`): h1 "Waste detection with MIRA" (DE "Abfallerkennung mit MIRA"), the lede, the copy command, "Try a demo" (`#demo`), "See the results" (`#results`) and the three-example switcher (`home/DemoExamples.svelte`): a glass bottle (hit), a crushed plastic bottle (miss) and cardboard called paper (out of scope). The photos and boxes are real, from `static/figures/detections.json` (`DEMO_FIGURE_FILES` in `lib/figures.ts`). The captions carry `{conf}` and `{threshold}`, filled from the JSON, so no number is typed twice. The demo text is the Next.js text.
2. **Result strip** (`home/ResultStrip.svelte`, `#results`): 90.58% mAP50 with the honesty line, linked to Research.
3. **The problem, and what I tried** (`home/Problem.svelte`).
4. **The evidence** (`home/Evidence.svelte`): chart, per-class table, the plastic note and the caveat. The two mistake photos that used to sit here are gone, because the switcher shows the same photos.
5. **Try it** (`home/TryIt.svelte`): install steps and the live download counter.
6. **What works, what is open, who made it** (`home/Status.svelte`).

Figure numbers: the example switcher is always Figure 1 (only one example is shown at a time), the chart is Figure 2, the table is Table 1.

## The 3D element and its fallback

The active example of the hero switcher is shown through `<DetectionFigure scene />`.

- **What it draws:** the real photo of the active example as a textured plane, and the model's real EXP-019 boxes from `detections.json` as wireframe prisms (12 thin bars each) standing 0.1 plane-heights in front of it, each with a class-coloured tag showing the class name and confidence. The miss example has no boxes, so it shows only the photo. The rig tilts gently with the pointer (window `pointermove`, up to about 20 degrees) and sways slowly when the pointer is idle for 2.5 s or on touch (touch pointers are ignored, no device orientation). Switching the example re-creates the figure (`{#key}`): the old scene is disposed and the new one gets its own canvas.
- **Lazy, in this order:** `three` lives only in `components/scene/detection-scene.ts`, loaded with a dynamic `import()` once ALL of these hold: the page has finished loading (`load`) and the browser is idle (`afterLoadAndIdle` in `scene/support.ts`: `requestIdleCallback` with a 2 s timeout, a 200 ms timer where it does not exist), the figure is in view, WebGL is available and reduced motion is off. The chunk is not referenced from the page HTML or any `modulepreload` (checked in `build/en.html`).
- **Fresh canvas:** every start creates a new `<canvas>` element, because a canvas whose WebGL context was lost or force-released cannot be reused. So a visitor who turns reduced motion off while the page is open gets the scene back. After a lost context or a failed import the figure stays 2D until reduced motion changes.
- **Performance:** the canvas follows its container (`ResizeObserver`), pixel ratio capped at 2, rendering pauses when the figure is off screen (`IntersectionObserver`) or the tab is hidden, and everything is disposed on teardown or context loss.
- **Fallback:** the static `<figure>` (photo plus the same boxes as positioned HTML) stays for no WebGL, reduced motion (also if it changes while the page is open), a lost context, a failed import, and no JavaScript.
- **Accessibility:** the `<img>` with its alt text and the visually hidden detection list stay in the page in both modes (the image is only made transparent in 3D mode); the canvas is `aria-hidden`. The "Detection boxes" toggle has a fixed name and `aria-pressed`; it hides the boxes in both modes. Home has exactly one toggle (it is absent on the miss example, which has no boxes).

## Fonts

Self-hosted fonts, no request to Google: `@fontsource-variable/plus-jakarta-sans` for text and display, `@fontsource/space-mono` for commands and numbers. `hooks.server.ts` adds `<link rel="preload">` for the two latin files that paint the first screen. Every other subset and weight stays lazy.

## Languages (i18n)

Pages live under `src/routes/[lang=lang]/` (`en` or `de`). The matcher makes every other first segment a 404, and each page exports `entries()` so both languages are prerendered. `/` is a client redirect page (`pickLocale` over `navigator.languages`, `window.location.replace`), with both languages as plain links and `<noscript>` text.

Visible copy lives only in the dictionaries (`src/i18n/en.ts`, `de.ts`, and `docs/`, `research/`, `package/`, `not-found.ts`). `en.ts` defines the shape and `de.ts` is typed `Dictionary`, so a missing key fails `pnpm check`; the parity tests also check placeholders, markers, code spans, empty strings and dashes. Use `fmt()`, `formatScoreLocale()`, `formatInt()` for numbers and `localePath(lang, "/research")` for links. `<Rich text={...} />` renders `==marker==`, `` `code` `` and `[label](href)` (internal links get the language prefix); it never uses `{@html}`.

To add a language: add the code to `LOCALES` (`src/i18n/config.ts`), copy `de.ts` to the new file and translate (and the same for `docs/`, `research/`, `package/`, `not-found.ts`), register it in the `index.ts` files, add `og-<lang>.png` to `static/` and the Open Graph locale in `src/lib/metadata.ts`, check the `lang === "de"` number formats, then add `common.languageNames` everywhere.

The language switch keeps the URL `#hash` (read from `location` on the client, updated on `hashchange` and after navigation). `<html lang>` is set at build time by `hooks.server.ts` and updated on the client after a client-side language switch.

## Metadata, sitemap, robots

Every page renders `<Seo lang path title description />` once. It is the only place that writes title, description, canonical, hreflang (`en`, `de`, `x-default`), Open Graph (type, site name, title, description, url, locale, image with size and alt) and Twitter card tags, from `pageMetadata()`. Home keeps its title, other pages get ` | MIRA`. Share cards are `static/og-en.png` and `og-de.png` (1200 x 630); the HTML sources for them are in `scripts/og/` (render each at 1200 x 630 in a browser). `SITE_URL` in `src/lib/site.ts` is the single place for the domain. `sitemap.xml` and `robots.txt` are prerendered from `src/lib/sitemap-data.ts`.

## 404

`build/404.html` is the prerendered `src/routes/404/+page.svelte`: both languages, `noindex`, links to `/en` and `/de`. Vercel serves it for unknown URLs. `[lang=lang]/+error.svelte` handles a 404 inside a language (header and footer stay) and the root `+error.svelte` handles client-side navigation to unknown URLs.

## Download counter

`DownloadsStat` (Home "Try it" and the links list of the Package page) shows the Hugging Face download count. The static HTML contains `FALLBACK_DOWNLOADS` (10176); in the browser `hf-downloads.ts` asks `https://huggingface.co/api/models/Jeremy341/MIRA-AI?expand[]=downloads&expand[]=downloadsAllTime` (5 s timeout) and shows `live`, `cached` (last good value in `localStorage`, every access in try/catch) or `fallback` ("built-in value"); the 30-day figure appears only for a live answer. This browser request to huggingface.co is deliberate (owner decision): no consent banner. The label says it counts file fetches, not people, and not PyPI installs. Update the fallback in `src/lib/site.ts`.

## Demo video

`DemoVideo` renders nothing until a video exists (the "Try it" section closes up). Fill `DEMO_VIDEO` at the top of `components/home/TryIt.svelte`: either a self-hosted `src` under `static/media/` (optional poster and WebVTT captions) or an 11-character `youtubeId` (click to load: the `youtube-nocookie.com` iframe is created only after the press, and focus moves into it). `src` wins when both are set.

## Docs

`routes/[lang=lang]/docs/` has the index and one page per guide (`/en/docs/<slug>`, all listed in `sitemap.xml`). `DocsSearch` follows the Next.js behaviour (Alt + `/` and a Slash code match, German folding, combobox ARIA, arrow keys, Enter and Escape, the "First 8 results" cap at `SEARCH_LIMIT`); the logic is in `components/docs/search-logic.ts` and `src/lib/docs-content.ts`, both tested. The contents drawer on small screens uses the text buttons "Contents" and "Close" (owner decision: no icon library).

## Deployment (Vercel)

`vercel.json` sets `framework: null`, `outputDirectory: "build"`, clean URLs, no trailing slash, redirects from the old `/research.html`, `/docs.html`, `/index.html`, the usual security headers, immutable caching for `/_app/immutable/*` and 30-day caching for `/figures/*`. Not verified here: that Vercel serves `/en` from `en.html`, `/en/research` from `en/research.html` and `404.html` for unknown URLs. Check `/en`, `/de/docs`, an unknown URL and the response headers on the first deployment. There is no Content Security Policy yet; the site contacts huggingface.co (counter) and, if a YouTube video is set, youtube-nocookie.com after a click.

### Not written yet: legal pages

A public German site needs an Impressum and a Datenschutzerklärung (the Hugging Face request is a third-party call). Neither exists yet.

## What is ported, and how it differs from the Next.js site

Everything in `website-next/src/app/[lang]/` has a counterpart here: Home, Research, Package, Docs (index and sub pages), 404, sitemap and robots. For Research, Package and Docs the visible text of the built pages was compared with `website-next/out/`. It is identical, except:

- German on Package and Docs has no "ich" (six neutral rewrites, see "Voice").
- The docs contents drawer closes with a text button ("Close", "Schließen"), and the docs search group carries an extra `aria-label`.

Home differs on purpose: it is the combined version (hero with the example switcher, result strip, problem, evidence, try it with the live counter, status). The Next.js Home has only the switcher, try it and status, and its demo copy sits in the component; here it is in the dictionaries.
