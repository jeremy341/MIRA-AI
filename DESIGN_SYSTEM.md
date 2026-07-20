# Ultralytics Platform Design System

> Extracted from [platform.ultralytics.com](https://platform.ultralytics.com) (deployment `dpl_Cr424wupaWY2oQPQz4btyTUwVEbf`) on 2026-07-19.
>
> **Source of truth:** live CSS custom properties + compiled Tailwind v4 theme layer + component `cva` class strings from JS bundles.
>
> **Auth note:** `/home` redirects to `/signin`. Color tokens, typography, cards, buttons, inputs, badges, glass overlays, charts, and brand palettes were extracted from public pages + shared CSS/JS. Authenticated sidebar/header layout is reconstructed from shadcn/ui sidebar utilities present in the stylesheet and `OVERLAY`/`GRID_DEFAULTS` constants in the theme module (same component system). Values marked **(inferred from CSS utilities / shadcn sidebar)** were not measured on a logged-in DOM.

---

## Stack & Conventions

| Layer | Technology |
|---|---|
| Framework | Next.js (App Router) + Turbopack |
| CSS | Tailwind CSS v4 (`@layer theme/base/components/utilities`) |
| Components | shadcn/ui-style (`data-slot="..."`), Radix primitives, `cva` |
| Theme mode | `html` class: `light` \| `dark` |
| Color space | Hex tokens in CSS; browsers may resolve to `lab()`/`oklab()` |
| Spacing base | `--spacing: 0.25rem` (4px) — Tailwind v4 spacing unit |
| Radius base | `--radius: 0.625rem` (10px) |

---

## 1. CSS Variables

### 1.1 Light mode (`:root` / `.light`)

Exact hex definitions from stylesheet:

```css
:root {
  --radius: .625rem;                          /* 10px */
  --background: #fff;
  --foreground: #0a0a0a;
  --card: #fff;
  --card-foreground: #0a0a0a;
  --popover: #fff;
  --popover-foreground: #0a0a0a;
  --primary: #171717;
  --primary-foreground: #fafafa;
  --secondary: #f5f5f5;
  --secondary-foreground: #171717;
  --muted: #f5f5f5;
  --muted-foreground: #737373;
  --section: #f8f8f8;
  --accent: #f5f5f5;
  --accent-foreground: #171717;
  --destructive: #e40014;
  --success: #3ac530;
  --border: #e5e5e5;
  --input: #e5e5e5;
  --ring: #a1a1a1;

  /* Charts */
  --chart-1: #f05100;
  --chart-2: #009588;
  --chart-3: #104e64;
  --chart-4: #fcbb00;
  --chart-5: #f99c00;
  --chart-6: #e40014;
  --chart-7: #1447e6;
  --chart-8: #00bb7f;
  --chart-9: #ac4bff;
  --chart-10: #ff2357;
  --chart-11: #147900;
  --chart-12: #e18528;

  /* Sidebar */
  --sidebar: #fafafa;
  --sidebar-foreground: #0a0a0a;
  --sidebar-primary: #171717;
  --sidebar-primary-foreground: #fafafa;
  --sidebar-accent: #f5f5f5;
  --sidebar-accent-foreground: #171717;
  --sidebar-border: #e5e5e5;
  --sidebar-ring: #a1a1a1;

  /* Links */
  --link: #155dfc;
  --link-hover: #1447e6;

  /* Brand / partner logos */
  --ultralytics-logo-text: #0b23a9;
  --ultralytics-logo-mark: #0b23a9;
  --ultralytics-logo-gradient-start: #09dbf0;
  --ultralytics-logo-gradient-end: #0b23a9;
  --hub-logo-accent: #00a2f3;
  --roboflow-logo: #6706ce;
  --wandb-logo: #fcbc32;

  --announcement-banner-height: 0px;
}
```

Derived radius tokens:

```css
--radius-xs: .125rem;                 /* 2px */
--radius-xl: calc(var(--radius) + 4px); /* 14px */
--radius-2xl: 1rem;                   /* 16px */
```

### 1.2 Dark mode (`.dark`)

```css
.dark {
  --background: #0a0a0a;
  --foreground: #fafafa;
  --card: #171717;
  --card-foreground: #fafafa;
  --popover: #171717;
  --popover-foreground: #fafafa;
  --primary: #e5e5e5;
  --primary-foreground: #171717;
  --secondary: #262626;
  --secondary-foreground: #fafafa;
  --muted: #262626;
  --muted-foreground: #a1a1a1;
  --section: #171717;
  --accent: #262626;
  --accent-foreground: #fafafa;
  --destructive: #ff6568;
  --success: #7bf1a8;
  --border: #ffffff1a;                /* white @ 10% */
  --input: #ffffff26;                 /* white @ 15% */
  --ring: #737373;

  /* Charts (reordered / brightened for dark surfaces) */
  --chart-1: #1447e6;
  --chart-2: #00bb7f;
  --chart-3: #f99c00;
  --chart-4: #ac4bff;
  --chart-5: #ff2357;
  --chart-6: #ff6568;
  --chart-7: #6d61ff;
  --chart-8: #40cc6d;
  --chart-9: #d433f5;
  --chart-10: #ff5c47;
  --chart-11: #008674;
  --chart-12: #e6b816;

  /* Sidebar */
  --sidebar: #171717;
  --sidebar-foreground: #fafafa;
  --sidebar-primary: #1447e6;         /* blue accent in dark */
  --sidebar-primary-foreground: #fafafa;
  --sidebar-accent: #262626;
  --sidebar-accent-foreground: #fafafa;
  --sidebar-border: #ffffff1a;
  --sidebar-ring: #737373;

  /* Links */
  --link: #3080ff;
  --link-hover: #155dfc;

  /* Logos flatten to white in dark mode */
  --ultralytics-logo-text: #fff;
  --ultralytics-logo-mark: #fff;
  --ultralytics-logo-gradient-start: #fff;
  --ultralytics-logo-gradient-end: #fff;
  --hub-logo-accent: #fff;
  --roboflow-logo: #fff;
  --wandb-logo: #fff;
}
```

### 1.3 Token → Tailwind color bridge

```css
--color-border: var(--border);
--color-link: var(--link);
--color-link-hover: var(--link-hover);
```

### 1.4 Quick reference table

| Token | Light | Dark |
|---|---|---|
| `--background` | `#ffffff` | `#0a0a0a` |
| `--foreground` | `#0a0a0a` | `#fafafa` |
| `--card` | `#ffffff` | `#171717` |
| `--primary` | `#171717` | `#e5e5e5` |
| `--secondary` / `--muted` / `--accent` | `#f5f5f5` | `#262626` |
| `--muted-foreground` | `#737373` | `#a1a1a1` |
| `--section` | `#f8f8f8` | `#171717` |
| `--destructive` | `#e40014` | `#ff6568` |
| `--success` | `#3ac530` | `#7bf1a8` |
| `--border` | `#e5e5e5` | `#ffffff1a` |
| `--input` | `#e5e5e5` | `#ffffff26` |
| `--ring` | `#a1a1a1` | `#737373` |
| `--sidebar` | `#fafafa` | `#171717` |
| `--sidebar-primary` | `#171717` | `#1447e6` |
| `--link` | `#155dfc` | `#3080ff` |

---

## 2. Layout Structure

### 2.1 App shell (authenticated dashboard)

**(Inferred from CSS utilities + theme `Z` / `OVERLAY` / `GRID_DEFAULTS` — not measured on logged-in DOM.)**

```
┌──────────┬────────────────────────────────────────────┐
│          │  Topbar / Header (frosted)                 │
│ Sidebar  ├────────────────────────────────────────────┤
│          │                                            │
│ 16rem    │  Main content (@container/main)            │
│ (icon:   │  padding + card grids                      │
│  3rem)   │                                            │
└──────────┴────────────────────────────────────────────┘
```

#### Sidebar

| Property | Value | Notes |
|---|---|---|
| Width (expanded) | `var(--sidebar-width)` → **16rem (256px)** | Standard shadcn; utility `.w-(--sidebar-width)` |
| Width (icon/collapsed) | `var(--sidebar-width-icon)` → **3rem (48px)** | `.data-[collapsible=icon]:w-(--sidebar-width-icon)` |
| Background | `var(--sidebar)` | Light `#fafafa` / Dark `#171717` |
| Foreground | `var(--sidebar-foreground)` | |
| Border | `1px solid var(--sidebar-border)` | Dark: white @ 10% |
| Z-index | `z-[60]` (`Z.sidebar`) | Above main overlay `z-50` |
| Collapsible modes | `offcanvas` \| `icon` \| `none` | Present in CSS group selectors |

**Nav item (sidebar menu button) — from utility classes in CSS:**

| State | Styles |
|---|---|
| Base | `flex w-full items-center gap-2 overflow-hidden rounded-md` text `sm`, ring `sidebar-ring` |
| Padding | `p-2` (8px); icon mode forces `p-2!` / `size-8!`; compact override `!p-1.5` |
| Hover | `hover:bg-sidebar-accent` + `hover:text-sidebar-accent-foreground` |
| Active | `data-[active=true]:bg-sidebar-accent` + `data-[active=true]:font-medium` + `data-[active=true]:text-sidebar-accent-foreground` |
| Focus | `focus-visible:ring-2` (sidebar-ring) |
| Icon | `[&>svg]:size-4` (16px), shrink-0 |
| Label | truncate last span |

#### Header / topbar (frosted glass)

Frosted surfaces use the shared `OVERLAY` / `BLUR` constants from the theme module:

```js
BLUR = "backdrop-blur backdrop-saturate-[1.2] backdrop-brightness-[1.01]"
// Resolved:
//   backdrop-filter: blur(8px) saturate(1.2) brightness(1.01)
```

| Overlay variant | Classes | Use |
|---|---|---|
| `default` | `bg-background/60` | Soft scrim |
| `blur` / `glass` | `bg-background/60` + `BLUR` (+ `border border-border/50` for glass) | Panels / dropzones |
| `dialog` | `bg-background/80` + `BLUR` | Modal overlay |
| `fullscreen` | `bg-background/70` + `BLUR` | Full-screen chrome |
| `floating` | `bg-background/95` + `BLUR` | Floating bars |
| **`bar`** | **`bg-background/90` + `BLUR`** | **Primary topbar / sticky chrome** |
| `viewer` | `bg-black/85` + `BLUR` | Media viewer |
| `hero` | `bg-gradient-to-r from-black/75 via-black/50 to-black/25` | Hero media overlay |
| `processing` | `blur-sm opacity-60 pointer-events-none` | Disabled processing state |

**Recommended header implementation for rebuild:**

```
sticky top-0 z-50 flex h-14 items-center gap-2 border-b
bg-background/90 backdrop-blur backdrop-saturate-[1.2] backdrop-brightness-[1.01]
```

| Property | Value |
|---|---|
| Height | `h-14` = `calc(var(--spacing) * 14)` = **56px** (common); `h-16` = 64px also available |
| Backdrop | `blur(8px) saturate(1.2) brightness(1.01)` |
| Background | `color-mix(in oklab, var(--background) 90%, transparent)` |
| Border bottom | `1px solid var(--border)` |

#### Main content

| Property | Value |
|---|---|
| Container query | `@container/main` |
| Max widths available | `max-w-sm` 24rem → `max-w-7xl` 80rem (`--container-*`) |
| Auth page content | `max-w-sm` (384px), centered |
| Page padding (auth) | `p-6 md:p-10` (24px / 40px) |
| Page bg (auth) | `bg-muted` |

#### Card grid / dashboard grid

From `GRID_DEFAULTS`:

```js
GRID_DEFAULTS = { columns: 6, cellHeight: 175, gap: 8 }
```

| Property | Value |
|---|---|
| Default columns | **6** |
| Cell height | **175px** |
| Gap | **8px** (`gap-2`) |
| Responsive pattern | CSS grid / container queries (`@container/card`, `@container/card-header`) |
| Typical card gaps | `gap-6` (24px) inside cards; section stacks `gap-6`–`gap-8` |

**Suggested responsive card columns for rebuild:**

```
1 col  < sm
2 cols sm–md
3 cols md–lg
4–6 cols xl+  (dashboard widgets; GRID_DEFAULTS uses 6)
```

---

## 3. Typography

### 3.1 Font families

| Role | Family | Variable | Files |
|---|---|---|---|
| Sans (UI) | **geistSans** | `--font-geist-sans` / `--default-font-family` | Variable WOFF2, weight 100–900 |
| Mono | **geistMono** | `--font-geist-mono` / `--font-mono` | Variable WOFF2, weight 100–900 |
| Fallback | Arial (metric-adjusted) | `geistSans Fallback` / `geistMono Fallback` | `local(Arial)` |

**CDN / asset URLs (from live deployment):**

```
https://platform.ultralytics.com/_next/static/media/GeistVF-s.p.2j89mul915j5u.woff2
https://platform.ultralytics.com/_next/static/media/GeistMonoVF-s.2exfgd61hn2an.woff2
```

Equivalent public fonts: [Geist](https://vercel.com/font) / `geist` npm package (same Vercel typeface).

```css
.font-sans { font-family: var(--font-geist-sans, ui-sans-serif, system-ui, sans-serif); }
.font-mono { font-family: var(--font-geist-mono, ui-monospace, monospace); }
```

Body: `font-sans antialiased`, base `16px / 24px` (line-height 1.5), weight 400.

### 3.2 Type scale (theme tokens)

| Token | Size | Line-height token | Computed LH |
|---|---|---|---|
| `--text-xs` | 0.75rem (12px) | `calc(1 / 0.75)` | 1.333 → 16px |
| `--text-sm` | 0.875rem (14px) | `calc(1.25 / 0.875)` | 1.429 → 20px |
| `--text-base` | 1rem (16px) | `calc(1.5 / 1)` | 1.5 → 24px |
| `--text-lg` | 1.125rem (18px) | `calc(1.75 / 1.125)` | 1.556 → 28px |
| `--text-xl` | 1.25rem (20px) | `calc(1.75 / 1.25)` | 1.4 → 28px |
| `--text-2xl` | 1.5rem (24px) | `calc(2 / 1.5)` | 1.333 → 32px |
| `--text-3xl` | 1.875rem (30px) | `calc(2.25 / 1.875)` | 1.2 → 36px |
| `--text-4xl` | 2.25rem (36px) | `calc(2.5 / 2.25)` | 1.111 → 40px |
| `--text-5xl` | 3rem (48px) | `1` | 48px |
| `--text-6xl` | 3.75rem (60px) | `1` | 60px |

Also used: `text-[0.8rem]`, `text-[8px]`, `text-[9px]`.

### 3.3 Font weights

| Token | Value | Typical use |
|---|---|---|
| `--font-weight-normal` | 400 | Body, descriptions |
| `--font-weight-medium` | 500 | Buttons, labels, nav |
| `--font-weight-semibold` | 600 | Card titles, headings |
| `--font-weight-bold` | 700 | Strong emphasis |

### 3.4 Letter-spacing

| Token / class | Value | Use |
|---|---|---|
| `--tracking-tight` / `.tracking-tight` | **-0.025em** | Headings (`text-2xl font-semibold tracking-tight` → ~−0.6px at 24px) |
| `--tracking-wide` | 0.025em | |
| `--tracking-wider` | 0.05em | |
| `--tracking-widest` | 0.1em | |
| Custom | `0.18em`, `0.2em`, `2px` | Rare specialty |

### 3.5 Line-height helpers

| Token | Value |
|---|---|
| `--leading-tight` | 1.25 |
| `--leading-snug` | 1.375 |
| `--leading-relaxed` | 1.625 |
| Card title | `leading-none` + `font-semibold` |
| Label | `leading-none` + `text-sm` + `font-medium` |

### 3.6 Heading / body recipes (observed)

| Element | Classes | Computed |
|---|---|---|
| Page / card title | `text-2xl font-semibold tracking-tight` | 24px / 32px / w600 / −0.025em |
| Card title (default slot) | `leading-none font-semibold` | |
| Card description | `text-muted-foreground text-sm` | 14px / 20px / `#737373` |
| Body | `text-base` / default | 16px / 24px / w400 |
| Small / meta | `text-xs` | 12px / 16px |
| Button / label | `text-sm font-medium` | 14px / 20px / w500 |
| Mono | `font-mono` | geistMono |

---

## 4. Component Patterns

### 4.1 Card

**Base classes** (`data-slot="card"`):

```
bg-card text-card-foreground isolate flex min-w-0 flex-col gap-6
rounded-xl border py-6 shadow-sm group/card
+ CARD_HOVER
```

**Hover animation (`CARD_HOVER`):**

```
transition duration-200
hover:-translate-y-[2px] hover:shadow-lg
motion-reduce:transition-none
motion-reduce:hover:translate-y-0
motion-reduce:hover:shadow-sm
```

**Image hover (`CARD_IMAGE`):**

```
transition-transform duration-300 group-hover/card:scale-105
motion-reduce:transition-none
```

| Property | Value |
|---|---|
| Border radius | `rounded-xl` = `calc(var(--radius) + 4px)` = **14px** |
| Border | `1px solid var(--border)` |
| Padding | vertical `py-6` (24px); horizontal via children `px-6` |
| Gap | `gap-6` (24px) |
| Shadow default | `shadow-sm` |
| Shadow hover | `shadow-lg` |
| Lift | `translateY(-2px)` over **200ms** |
| Width (auth card) | 384px (`max-w-sm`) |

**Subcomponents:**

| Slot | Classes |
|---|---|
| `card-header` | `@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-2 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6` + padding variant |
| Header padding | `default: px-6` · `compact: px-6 pb-2` · `flush: px-0` |
| `card-content` | `default: px-6` · `inset: px-4 pb-4` · `flush: px-0` |
| `card-footer` | `flex flex-wrap items-center gap-2 px-6 [.border-t]:pt-6` |
| `card-description` | `text-muted-foreground text-sm` |
| `card-title` | `leading-none font-semibold` |
| `card-action` | `col-start-2 row-span-2 row-start-1 self-start justify-self-end` |

**Semantic card tones (`SEMANTIC_CARD_TONE_CLASSES`):**

| Tone | Classes |
|---|---|
| success | `border-success/20 bg-success/5 dark:bg-success/10` |
| warning | `border-amber-400/50 bg-amber-50/60 text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100` |
| error | `border-destructive/30 bg-destructive/5 dark:border-destructive/20 dark:bg-destructive/10` |
| info | `border-sky-500/30 bg-sky-500/5 dark:border-sky-500/20 dark:bg-sky-500/10` |
| purple | `border-violet-500/30 bg-violet-500/5 dark:border-violet-500/20 dark:bg-violet-500/10` |

**Stat card variants (`STAT_CARD_VARIANTS`):**

```
default.card: border-primary/10 bg-gradient-to-br from-primary/5 via-background to-background
+ decorative before/after primary/10 circles (size-52 / size-32)
warning: border-amber-500/50 bg-amber-500/5 dark:bg-amber-500/10
error:   border-red-500/50 bg-red-500/5 dark:bg-red-500/10
```

### 4.2 Button

**Base (`data-slot="button"`):**

```
inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md
text-sm font-medium transition-all
disabled:pointer-events-none disabled:opacity-50
[&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0
outline-none
focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40
aria-invalid:border-destructive
```

**Focus ring:** `3px` ring at `color-mix(ring 50%, transparent)`, border becomes `--ring`.

#### Variants

| Variant | Classes |
|---|---|
| **default** (primary) | `bg-primary text-primary-foreground hover:bg-primary/90` |
| **destructive** | `bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60` |
| **destructive-outline** | `border bg-background shadow-xs text-destructive hover:bg-destructive/10 hover:text-destructive … dark:bg-input/30 dark:border-input dark:hover:bg-destructive/10` |
| **destructive-ghost** | `text-muted-foreground hover:bg-accent hover:text-destructive …` |
| **outline** | `border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50` |
| **secondary** | `bg-secondary text-secondary-foreground hover:bg-secondary/80` |
| **ghost** | `hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50` |
| **icon-ghost** | `text-muted-foreground hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50` |
| **link** | `text-primary underline-offset-4 hover:underline` |
| **success** | `bg-success text-white hover:bg-success/90 focus-visible:ring-success/20 dark:focus-visible:ring-success/40` |
| **warning** | `bg-amber-600 text-white hover:bg-amber-700 … dark:bg-amber-600 dark:hover:bg-amber-500` |
| **error** | `bg-red-600 text-white hover:bg-red-700 …` |
| **info** | `bg-sky-600 text-white hover:bg-sky-700 …` |

#### Sizes

| Size | Classes | Computed height |
|---|---|---|
| default | `h-9 px-4 py-2 has-[>svg]:px-3` | **36px** |
| xs | `h-6 gap-1 rounded-md px-2 text-xs has-[>svg]:px-1.5 [&_svg…]:size-3` | 24px |
| sm | `h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5` | 32px |
| lg | `h-10 rounded-md px-6 has-[>svg]:px-4` | 40px |
| icon | `size-9` | 36×36 |
| icon-xs | `size-6 rounded-md [&_svg…]:size-3` | 24×24 |
| icon-sm | `size-8` | 32×32 |
| icon-lg | `size-10` | 40×40 |

**Border radius on buttons:** `rounded-md` = `calc(var(--radius) - 2px)` = **8px**.

**Transition:** `transition-all` → **0.15s** `cubic-bezier(0.4, 0, 0.2, 1)`.

### 4.3 Input / Select

**Input (`data-slot="input"`):**

```
file:text-foreground placeholder:text-muted-foreground
selection:bg-primary selection:text-primary-foreground
dark:bg-input/30 border-input
h-9 w-full min-w-0 rounded-md border bg-transparent
px-3 py-1 text-base shadow-xs
transition-[color,box-shadow] outline-none
file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium
disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50
md:text-sm
focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40
aria-invalid:border-destructive
```

| Property | Value |
|---|---|
| Height | `h-9` = **36px** |
| Padding | `4px 12px` (`py-1 px-3`) |
| Radius | **8px** (`rounded-md`) |
| Background | transparent (light); `input/30` (dark) |
| Border | `1px solid var(--input)` |
| Shadow | `shadow-xs` |
| Font | 16px mobile → `md:text-sm` (14px) desktop |
| Focus | border `--ring` + **3px** ring at 50% opacity |
| Transition | `color, box-shadow` @ **0.15s** ease |

**Label (`data-slot="label"`):**

```
flex items-center gap-2 text-sm leading-none font-medium select-none
group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50
peer-disabled:cursor-not-allowed peer-disabled:opacity-50
```

**Select:** Follows same radius/height/border/focus-ring language as Input (shadcn SelectTrigger pattern: `h-9 rounded-md border border-input …`).

### 4.4 Badge

**Base (`data-slot="badge"`):**

```
inline-flex items-center justify-center rounded-full border
px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0
[&>svg]:size-3 gap-1 [&>svg]:pointer-events-none
focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
aria-invalid:… transition-[color,box-shadow] overflow-hidden
[button&]:cursor-pointer
```

| Property | Value |
|---|---|
| Radius | `rounded-full` (pill) |
| Padding | `px-2 py-0.5` (8px × 2px) |
| Font | `text-xs font-medium` (12px / 500) |
| Icon | 12px (`size-3`) |

#### Variants

| Variant | Classes |
|---|---|
| default | `border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90 [button&]:hover:opacity-80` |
| secondary | `border-transparent bg-secondary text-secondary-foreground …` |
| destructive | `border-transparent bg-destructive text-white … dark:bg-destructive/60` |
| outline | `text-foreground [a&]/[button&]:hover:bg-accent hover:text-accent-foreground` |
| success | `border-transparent bg-success/10 text-success` |
| warning | `border-transparent bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400` |
| error | `border-transparent bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400` |
| info | `border-transparent bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-400` |
| purple | `border-transparent bg-violet-100 text-violet-700 dark:bg-violet-500/20 dark:text-violet-400` |

### 4.5 Separator

```
bg-border shrink-0
data-[orientation=horizontal]:h-px data-[orientation=horizontal]:w-full
data-[orientation=vertical]:h-full data-[orientation=vertical]:w-px
```

### 4.6 Tooltip

```
bg-foreground text-background
rounded-md px-3 py-1.5 text-xs text-balance
+ enter/exit animations (fade + zoom + slide by side)
z-index: Z.tooltip = z-[90]
```

### 4.7 Dialog

```
relative flex min-h-0 w-full max-w-[95vw] max-h-[85vh] flex-col
overflow-hidden rounded-lg border bg-background shadow-lg duration-200
+ animate-in/out fade
```

Sizes: `sm:max-w-sm` → `sm:max-w-3xl` / `full: sm:max-w-[95vw]`.

Overlay: `PageOverlay` variant `blur` → `bg-background/80` + frosted `BLUR`.

Body: `min-h-0 flex-1 overflow-y-auto px-6 py-4`.

### 4.8 Links (global base)

```css
a:not([data-slot=button]):not([data-slot=sidebar-menu-button]):…
  { cursor: pointer; color: var(--color-link); transition: color 0.15s; }
a:…:hover { color: var(--color-link-hover); }
[data-slot=sidebar-wrapper] a { color: inherit; }
```

### 4.9 Nav items (summary)

| Context | Padding | Hover | Active |
|---|---|---|---|
| Sidebar menu button | `p-2` (8px) | `bg-sidebar-accent` | `bg-sidebar-accent` + `font-medium` |
| Ghost button / icon-ghost | size-based | `bg-accent` | — |
| Tabs / active state utilities | — | — | `data-[active=true]:bg-sidebar-accent` |

---

## 5. Spacing System

### 5.1 Base unit

```css
--spacing: 0.25rem; /* 4px */
```

Tailwind v4: `p-N` / `gap-N` / `h-N` = `calc(var(--spacing) * N)`.

| Token | Rem | Px |
|---|---|---|
| 0.5 | 0.125rem | 2px |
| 1 | 0.25rem | 4px |
| 1.5 | 0.375rem | 6px |
| 2 | 0.5rem | 8px |
| 3 | 0.75rem | 12px |
| 4 | 1rem | 16px |
| 6 | 1.5rem | 24px |
| 8 | 2rem | 32px |
| 10 | 2.5rem | 40px |
| 14 | 3.5rem | 56px |

### 5.2 Common patterns

| Context | Gap / padding |
|---|---|
| Card internal stack | `gap-6` (24px) |
| Card header grid | `gap-2` (8px) |
| Card header / content X padding | `px-6` (24px) |
| Card content inset | `px-4 pb-4` (16px) |
| Section stack (auth) | `gap-6`–`gap-8` (24–32px) |
| Form fields | `space-y-3` / `space-y-4` (12–16px) |
| Inline icon + text | `gap-2` (8px) buttons; SSO buttons observed `gap-3` (12px) |
| Page padding | `p-6 md:p-10` |
| Button default | `px-4 py-2` |
| Badge | `px-2 py-0.5` |
| Dashboard grid | `gap: 8` (`GRID_DEFAULTS`) |

### 5.3 Container widths

| Token | Value |
|---|---|
| `--container-xs` | 20rem (320px) |
| `--container-sm` | 24rem (384px) |
| `--container-md` | 28rem |
| `--container-lg` | 32rem |
| `--container-xl` | 36rem |
| `--container-2xl` | 42rem |
| `--container-3xl` | 48rem |
| `--container-4xl` | 56rem |
| `--container-5xl` | 64rem |
| `--container-7xl` | 80rem |

---

## 6. Shadows

Resolved from utility layer (`--tw-shadow-color` defaults shown):

| Class | Value |
|---|---|
| **shadow-xs** | `0 1px 2px 0 #0000000d` (black 5%) |
| **shadow-sm** / **shadow** | `0 1px 3px 0 #0000001a, 0 1px 2px -1px #0000001a` |
| **shadow-md** | `0 4px 6px -1px #0000001a, 0 2px 4px -2px #0000001a` |
| **shadow-lg** | `0 10px 15px -3px #0000001a, 0 4px 6px -4px #0000001a` |
| **shadow-xl** | `0 20px 25px -5px #0000001a, 0 8px 10px -6px #0000001a` |
| **shadow-2xl** | `0 25px 50px -12px #00000040` |

Drop shadows:

| Class | Value |
|---|---|
| drop-shadow-sm | `0 1px 2px #00000026` |
| drop-shadow-md | `0 3px 3px #0000001f` |

**Usage:** inputs/outline buttons → `shadow-xs`; cards → `shadow-sm` → hover `shadow-lg`; dialogs → `shadow-lg`.

---

## 7. Transitions & Motion

### 7.1 Defaults (theme)

```css
--default-transition-duration: .15s;
--default-transition-timing-function: cubic-bezier(.4, 0, .2, 1); /* ease-in-out */
--ease-out: cubic-bezier(0, 0, .2, 1);
--ease-in-out: cubic-bezier(.4, 0, .2, 1);
```

### 7.2 Common durations

| Class / use | Duration |
|---|---|
| Default (`transition`, `transition-all`) | **150ms** |
| Card hover (`duration-200`) | **200ms** |
| Card image scale (`duration-300`) | **300ms** |
| Dialog | `duration-200` |
| Link color | **150ms** |
| Chart animation | **500ms** (`CHART_STYLE.animationDuration`) |

### 7.3 Signature motions to recreate

1. **Card lift:** 200ms ease → `translateY(-2px)` + `shadow-lg` (respect `prefers-reduced-motion`)
2. **Card image zoom:** 300ms → `scale(1.05)` on `group-hover/card`
3. **Frosted chrome:** static `backdrop-filter: blur(8px) saturate(1.2) brightness(1.01)`
4. **Focus rings:** 3px soft ring on interactive controls
5. **Button / color transitions:** 150ms on `all` or `color, box-shadow`

---

## 8. Brand Colors

### 8.1 Logo CSS variables

| Token | Light | Dark |
|---|---|---|
| `--ultralytics-logo-gradient-start` | `#09dbf0` (cyan) | `#ffffff` |
| `--ultralytics-logo-gradient-end` | `#0b23a9` (deep blue) | `#ffffff` |
| `--ultralytics-logo-mark` / `-text` | `#0b23a9` | `#ffffff` |

Logo gradient (light): **cyan `#09dbf0` → deep blue `#0b23a9`**.

### 8.2 `BRAND_COLORS` (JS theme module)

```js
{
  darkBlue:    "#111F68",
  brightBlue:  "#042AFF",
  neonYellow:  "#E1FF25",
  neonPink:    "#FF64DA",
  lightGrey:   "#F3F3F3",
  white:       "#FFFFFF",
  black:       "#0b0b0f",
  aquaBlue:    "#00FFFF",
  lightBlue:   "#ACF9FF",
  neonGreen:   "#76FFD6",
  grey:        "#CCCCCC",
  darkGrey:    "#9E9E9E",
  cyan:        "#63D7EB",
  logoDarkBlue:"#1323A5",
  logoGrey:    "#EAEDF4",
  bbox: [
    "#0BDBEB", "#00DFB7", "#FF6FDD", "#CCED00",
    "#00F344", "#BD00FF", "#00B4FF", "#DD00BA"
  ]
}
```

### 8.3 Brand gradients

**`BRAND_GRADIENT`:**

```css
linear-gradient(105deg, #111F68 0%, #042AFF 45%, #76FFD6 100%)
```

**`BRAND_HERO_GRADIENT`:**

```css
radial-gradient(at 0% 100%, #00FFFF55 0%, transparent 45%),
radial-gradient(at 100% 0%, #FF64DA55 0%, transparent 45%),
radial-gradient(at 50% 50%, #ACF9FF66 0%, transparent 60%)
```

**`OG_COLORS.gradient` (social / OG image):**

```css
linear-gradient(135deg, #FF64DA 0%, #042AFF 50%, #0BDBEB 100%)
```

**`OG_COLORS.photoOverlay`:**

```css
linear-gradient(90deg,
  rgba(0,0,0,0.82) 0%,
  rgba(0,0,0,0.58) 38%,
  rgba(0,0,0,0.24) 68%,
  rgba(0,0,0,0.08) 100%)
```

### 8.4 Accent highlights (marketing / charts)

| Name | Hex | Role |
|---|---|---|
| Neon pink | `#FF64DA` | Hero / OG accent |
| Bright blue | `#042AFF` | Brand primary accent |
| Cyan / aqua | `#0BDBEB` / `#00FFFF` / `#09dbf0` | Logo + detection boxes |
| Neon yellow | `#E1FF25` | High-energy accent |
| Neon green | `#76FFD6` | Brand gradient end |
| Magenta bbox | `#FF6FDD` / `#DD00BA` | Annotation palette |
| Lime bbox | `#CCED00` / `#00F344` | Annotation palette |

### 8.5 Theme chart palette (`THEME_COLORS`)

Per-hue `{ light, dark }` used for analytics series:

| Name | Light | Dark |
|---|---|---|
| indigo | `#6366f1` | `#a5b4ff` |
| green | `#22c55e` | `#86efac` |
| orange | `#f97316` | `#fdba74` |
| cyan | `#06b6d4` | `#67e8f9` |
| yellow | `#eab308` | `#fde047` |
| red | `#ef4444` | `#fca5a5` |
| violet | `#8b5cf6` | `#c4b5fd` |
| sky | `#0ea5e9` | `#7dd3fc` |
| pink | `#f472b6` | `#f9a8d4` |
| teal | `#14b8a6` | `#5eead4` |
| blue | `#3b82f6` | `#60a5fa` |
| emerald | `#10b981` | `#34d399` |
| amber | `#f59e0b` | `#fbbf24` |
| rose | `#f43f5e` | `#fb7185` |
| purple | `#a855f7` | `#c084fc` |
| fuchsia | `#c026d3` | `#e879f9` |
| lime | `#84cc16` | `#a3e635` |
| slate | `#64748b` | `#94a3b8` |
| stone | `#78716c` | `#a8a29e` |
| zinc | `#71717a` | `#a1a1aa` |

### 8.6 Chart.js theme text/grid

```js
CHARTJS_THEME = {
  light: { title: "#1f2937", axis: "#6b7280", grid: "rgba(209, 213, 219, 0.4)" },
  dark:  { title: "#f9fafb", axis: "#9ca3af", grid: "rgba(55, 65, 81, 0.25)" },
  crosshair: "rgba(107, 114, 128, 0.5)"
}
```

### 8.7 Chart style radii

```js
CHART_STYLE = {
  radius: 6,
  barRadius: 6,
  barRadiusStart: [0, 6, 6, 0],
  pieCornerRadius: 6,
  animationDuration: 500,
  animationDurationUpdate: 500
}
```

### 8.8 UI chrome colors (`UI_COLORS`) — charts/tooltips

```js
{
  text:        { light: "#1f2937", dark: "#f9fafb" },
  textMuted:   { light: "#6b7280", dark: "#9ca3af" },
  border:      { light: "#e5e7eb", dark: "#374151" },
  borderStrong:{ light: "#d1d5db", dark: "#4b5563" },
  bg:          { light: "#ffffff", dark: "#1f2937" },
  bgMuted:     { light: "#f9fafb", dark: "#111827" },
  bgDeep:      { light: "#f1f5f9", dark: "#020617" },
  tooltip: {
    bg: "rgba(0, 0, 0, 0.85)",
    text: "rgba(255, 255, 255, 1)",
    textMuted: "rgba(255, 255, 255, 0.7)",
    textFaint: "rgba(255, 255, 255, 0.5)"
  }
}
```

### 8.9 Detection / class palettes

**`ULTRALYTICS_CLASS_PALETTE` (sample):**

`#042aff, #0bdbeb, #f3f3f3, #00dfb7, #111f68, #ff6fdd, #ff444f, #cced00, #00f344, #bd00ff, #00b4ff, #dd00ba, #00ffff, #26c000, #01ffb3, #7d24ff, #7b0068, #ff1b6c, #fc6d2f, #a2ff0b`

**`MODEL_CHART_PALETTE`:**

`#2563eb, #dc2626, #16a34a, #9333ea, #ea580c, #0891b2, #be123c, #4f46e5, #ca8a04, #0d9488, #7c3aed, #db2777, #65a30d, #0284c7, #c2410c, #7e22ce, #059669, #b91c1c, #1d4ed8, #a16207`

---

## 9. Radius Scale (resolved)

Given `--radius: 0.625rem` (10px):

| Class | Formula | Px |
|---|---|---|
| `rounded-xs` | `var(--radius-xs)` | 2px |
| `rounded-sm` | `calc(var(--radius) - 4px)` | **6px** |
| `rounded-md` | `calc(var(--radius) - 2px)` | **8px** (buttons, inputs) |
| `rounded-lg` | `var(--radius)` | **10px** (dialogs) |
| `rounded-xl` | `calc(var(--radius) + 4px)` | **14px** (cards) |
| `rounded-2xl` | `1rem` | 16px |
| `rounded-full` | pill | badges |

---

## 10. Z-Index Scale (`Z`)

| Token | Value | Use |
|---|---|---|
| overlay | `z-50` | Page overlays |
| sidebar | `z-[60]` | Sidebar above content |
| cookieBanner | `z-[65]` | |
| popover | `z-[70]` | |
| banner | `z-[80]` | |
| chatWidget | `z-[85]` | |
| tooltip | `z-[90]` | |
| lightbox | `z-[100]` | |

---

## 11. Tailwind Extended Color Scales (theme layer excerpts)

Useful for semantic badge/button variants beyond CSS variables:

| Scale | Key stops |
|---|---|
| red | 100 `#ffe2e2` · 400 `#ff6568` · 500 `#fb2c36` · 600 `#e40014` · 700 `#bf000f` |
| amber | 50 `#fffbeb` · 100 `#fef3c6` · 400 `#fcbb00` · 500 `#f99c00` · 600 `#dd7400` · 700 `#b75000` |
| green | 50 `#f0fdf4` · 200 `#b9f8cf` · 400 `#05df72` · 500 `#00c758` · 600 `#00a544` |
| emerald | 400 `#00d294` · 500 `#00bb7f` · 600 `#009767` |
| sky | 100 `#dff2fe` · 400 `#00bcfe` · 500 `#00a5ef` · 600 `#0084cc` |
| blue | 300 `#90c5ff` · 400 `#54a2ff` · 500 `#3080ff` · 600 `#155dfc` |
| violet | 100 `#ede9fe` · 400 `#a685ff` · 500 `#8d54ff` · 600 `#7f22fe` · 700 `#7008e7` |
| purple | 200 `#e9d5ff` · 500 `#ac4bff` · 800 `#6e11b0` |
| pink | 100 `#fce7f3` · 400 `#fb64b6` · 500 `#f6339a` · 700 `#c4005c` |
| orange | 100 `#ffedd5` · 400 `#ff8b1a` · 500 `#fe6e00` · 700 `#c53c00` |
| yellow | 400 `#fac800` |

Blur tokens: `--blur-sm: 8px` · `--blur-2xl: 40px` · `--blur-3xl: 64px`.  
Default `backdrop-blur` utility = **`blur(8px)`**.

---

## 12. Auth Page Layout Recipe (measured)

Centered auth shell (sign-in / sign-up):

```
div.flex.min-h-svh.flex-col.items-center.justify-center.gap-6.bg-muted.p-6.md:p-10
  └─ div.flex.w-full.max-w-sm.flex-col.gap-6          /* 384px */
       ├─ logo row (gap-2, font-medium)
       └─ div.flex.flex-col.gap-8
            └─ Card (rounded-xl, py-6, shadow-sm, hover lift)
                 ├─ CardHeader px-6 text-center
                 └─ CardContent px-6 space-y-4
```

| Element | Measured |
|---|---|
| Page bg | `--muted` (`#f5f5f5` light) |
| Card width | 384px |
| Card radius | 14px |
| Card padding Y | 24px |
| Primary CTA | h-9, full width, `bg-primary` |
| OAuth buttons | outline variant, full width, gap-3 icons |

---

## 13. Rebuild Checklist (for matching aesthetic)

1. **Geist Sans + Geist Mono** variable fonts; `antialiased`.
2. Port **exact hex CSS variables** for `:root` and `.dark` (section 1).
3. `--radius: 0.625rem`; cards `rounded-xl` (14px), controls `rounded-md` (8px), badges `rounded-full`.
4. Neutrals-first UI: near-black primary on light, near-white primary on dark — **not** a purple dashboard theme.
5. Cards: `shadow-sm`, border `--border`, **200ms** lift −2px + `shadow-lg`.
6. Frosted bars: `bg-background/90` + `blur(8px) saturate(1.2) brightness(1.01)`.
7. Focus: `ring-[3px]` at `ring/50` + `border-ring`.
8. Brand accents sparingly: cyan→blue logo gradient; neon pink/yellow/green for marketing/charts only.
9. Spacing on **4px** grid; card padding **24px**; control height **36px** (`h-9`).
10. Sidebar: `--sidebar*` tokens, 16rem / 3rem collapsible, active = `sidebar-accent` fill + medium weight.
11. Chart series: prefer `--chart-1…12` (mode-aware) or `THEME_COLORS` dual light/dark pairs.
12. Honor `motion-reduce:` — disable card translate/scale when reduced motion is set.

---

## 14. File / Bundle References

| Asset | Role |
|---|---|
| `/_next/static/chunks/3-617n945py-f.css` | Theme tokens, utilities, shadows, sidebar width utilities |
| `/_next/static/chunks/0bgy6pjy32l5k.css` | Geist `@font-face` |
| `/_next/static/chunks/1w12n2rbo_3vb.js` | `BRAND_*`, `OVERLAY`, `CHART_*`, `GRID_DEFAULTS`, `UI_COLORS`, `Z` |
| `/_next/static/chunks/1--0cl5t47jgl.js` | `buttonVariants` (cva) |
| `/_next/static/chunks/2chyw88oirbl8.js` | Card, Badge, Separator, semantic tone maps |

---

*End of design system document.*
