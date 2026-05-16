# NutriPlan AI — Design System

## Overview

NutriPlan AI is a clinical B2B tool for nutrition doctors. The design language is professional, trustworthy, and information-dense — built for daily clinical workflows, not consumer shopping. It draws from established clinical software conventions (EHR systems, health dashboards) rather than consumer ecommerce.

**Key characteristics:**

- Dark navy sidebar (`#0f172a`) as the primary navigation surface — familiar to users of clinical and enterprise software
- Clinical teal (`#0d9488`) as the sole accent colour — used for primary actions, active states, and focus rings only
- Light slate background (`#f1f5f9`) behind white content panels — creates depth without shadows
- Inter at 15px base — professional, highly legible at small sizes, no custom font dependency
- Rounded-rectangle buttons (8px radius) — professional without being pill-shaped consumer CTAs
- Compact information density — page titles at 24px, not 64px hero displays

---

## Colors

### Brand & Accent

| Token | Value | Use |
|---|---|---|
| `--primary` | `#0d9488` | Primary buttons, active nav links, focus rings, progress bars, teal chips |
| `--primary-deep` | `#0f766e` | Button hover/active state, focused input border, link hover |
| `--primary-soft` | `#f0fdfa` | Teal chip background, table row hover, active pill tab background |

### Surface

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#ffffff` | Cards, panels, inputs, modal backgrounds |
| `--surface-soft` | `#f1f5f9` | Page background, table header, step form background, upload zone |
| `--surface-mid` | `#e2e8f0` | Progress bar track, calendar header cells |

### Borders

| Token | Value | Use |
|---|---|---|
| `--hairline` | `#cbd5e1` | Input borders, standard dividers |
| `--hairline-soft` | `#e2e8f0` | Card borders, panel dividers, table row separators |

### Text

| Token | Value | Use |
|---|---|---|
| `--ink-deep` | `#0f172a` | Page headings, strong labels, primary body text |
| `--ink` | `#1e293b` | Body text, table cell text |
| `--charcoal` | `#334155` | Label text, secondary headings |
| `--slate` | `#64748b` | Supporting copy, subheadings, table column headers |
| `--steel` | `#94a3b8` | Placeholder text, sidebar nav text (inactive) |
| `--stone` | `#cbd5e1` | Disabled labels |

### Sidebar

| Token | Value | Use |
|---|---|---|
| `--sidebar-bg` | `#0f172a` | Sidebar background |
| `--sidebar-hover` | `#1e293b` | Nav link hover background |
| `--sidebar-active` | `rgba(13,148,136,0.15)` | Active nav link background |
| `--sidebar-text` | `#94a3b8` | Inactive nav link text |
| `--sidebar-bright` | `#ffffff` | Active nav link text, brand name |

### Semantic

| Token | Value | Use |
|---|---|---|
| `--success` | `#059669` | Success badge text |
| `--success-bg` | `#ecfdf5` | Success badge background |
| `--warning` | `#d97706` | Warning badge text, clinical caution labels |
| `--warning-bg` | `#fffbeb` | Warning badge background |
| `--critical` | `#dc2626` | Error text, abnormal blood marker rows, allergen critical badge |
| `--critical-bg` | `#fef2f2` | Error backgrounds, abnormal row highlight |

---

## Typography

**Font:** Inter (loaded from Google Fonts). Fallback: `system-ui, -apple-system, sans-serif`.

| Role | Size | Weight | Use |
|---|---|---|---|
| Page heading (`h1`) | 24px | 600 | Dashboard and page titles |
| Section heading (`h2`) | 16px | 600 | Panel headers, card titles |
| Category label (`h3`) | 13px | 600 + uppercase + 0.05em spacing | Section kickers, sidebar section labels |
| Body | 15px | 400 | Default app text (set on `:root`) |
| Label | 13px | 600 | Form labels, table column headers |
| Small / supporting | 13–14px | 400–500 | Subtitles, helper text, table cells |
| Caption / eyebrow | 11–12px | 600–700 + uppercase | Step indicators, section kickers, badge text |

**Principles:**
- No extra-large hero text — this is a dashboard, not a landing page
- Labels are always 13px/600 to distinguish from body text
- Table column headers use uppercase + letter-spacing for scannability

---

## Layout

### App Shell

The standard authenticated layout uses a **two-column sidebar + main** structure:

```
┌─────────────────────────────────────────────────────┐
│  Sidebar (240px)    │  Main content area            │
│  --sidebar-bg       │  --surface-soft background    │
│                     │                               │
│  Brand lockup       │  .page-header (white, sticky) │
│  Nav links          │  ─────────────────────────    │
│                     │  .content (max-width 1280px)  │
│                     │                               │
│  Doctor name        │                               │
│  Sign out           │                               │
└─────────────────────────────────────────────────────┘
```

- Sidebar: `position: sticky; height: 100vh` — always visible while scrolling content
- Page header: `background: white; border-bottom: 1px solid --hairline-soft` — contextual title + primary action button
- Content: `padding: 28px 32px 48px; max-width: 1280px`

### Spacing

Base unit: 4px. Standard steps: 4 · 6 · 8 · 10 · 12 · 14 · 16 · 18 · 20 · 24 · 28 · 32 · 48.

### Grid

| Context | Columns | Gap |
|---|---|---|
| Stat cards (dashboard) | 4 | 16px |
| Field pair (form) | 2 | 14px |
| Field trio (form) | 3 | 14px |
| Profile grid (medical) | 2 | 12px |
| Constraint grid | 3 | 12px |
| Calendar | 1 label + 7 days | 6px |

---

## Components

### Sidebar Navigation

- Background: `--sidebar-bg` (`#0f172a`)
- Brand lockup: white bold name + teal "Clinical" badge
- Nav links: 14px/500, `--sidebar-text` colour, 8px padding, 7px border-radius
- Active: teal background (`--sidebar-active`) + teal text (`--primary`) + 600 weight
- Hover: `--sidebar-hover` background + white text
- Section labels: 10px uppercase, faded teal-white, not interactive
- Footer: doctor name + clinic above sign-out button

### Buttons

| Variant | Background | Radius | Height | Use |
|---|---|---|---|---|
| `.button-primary` | `--primary` (teal) | 8px | 40px | Primary actions: Save, Generate, Approve |
| `button` (default) | `--ink-deep` | 8px | 40px | Secondary actions with dark emphasis |
| `.button-ghost` | Transparent, `--hairline` border | 8px | 40px | Back, Cancel, Sign out |
| `.button-danger` | `--critical` | 8px | 40px | Destructive actions |

Disabled state: `opacity: 0.45; cursor: not-allowed` on all variants.

### Cards & Panels

`.checkout-summary` and `.data-panel`:
- Background: `--canvas`
- Border: `1px solid --hairline-soft`
- Border-radius: 10px
- Padding: 20px
- No box shadow — depth comes from the `--surface-soft` page background

Panel header (`.panel-header`):
- Flex row, space-between
- Border-bottom: `1px solid --hairline-soft`, padding-bottom: 14px, margin-bottom: 16px
- Left: `h2` title + `span` subtitle (slate colour)

### Tables

- Header row: `--surface-soft` background, 12px/600/uppercase/0.05em tracking
- First and last `th` have 7px border-radius (pill-table effect)
- Row hover: `background: --primary-soft` on all `td` in the row
- Abnormal marker rows: `background: --critical-bg; color: --critical; font-weight: 600`
- Last row has no border-bottom

### Badges

Rounded rectangle (5px radius), no pill shape:

| Class | Background | Text colour | Use |
|---|---|---|---|
| `.badge-success` | `--success-bg` | `--success` | Approved, complete, verified |
| `.badge-warning` | `--warning-bg` | `--warning` | Draft, pending, in-progress |
| `.badge-critical` | `--critical-bg` | `--critical` | Error, allergen violation |

### Forms

- Inputs: 40px height, 7px radius, `--hairline` border
- Focus: `--primary` border + `rgba(13,148,136,0.12)` box-shadow ring
- Labels: 13px/600, grid layout with 6px gap above the input
- Form sections: separated by `1px solid --hairline-soft` top border, 18px padding-top

### Pill Tabs

Used for week selectors, wizard steps, and nav overflows:
- Default: transparent, `--hairline` border, 7px radius, 34px height
- Active: `--primary-soft` background, `--primary` border, `--primary-deep` text, 600 weight
- Disabled: `opacity: 0.6; cursor: not-allowed`

### Removable Chips

`.chip-item` — used in PatientStepForm multi-item lists:
- Background: `--primary-soft`
- Border: `rgba(13,148,136,0.2)`
- Text: `--primary-deep`, 13px/500
- Remove button: inline ✕ icon, transparent, fades to full opacity on hover

### Allergen Badges

`.allergen-badge` variants — severity-coded:

| Class | Background | Text | Severity |
|---|---|---|---|
| `.allergen-badge.warning` | `--warning-bg` | `--warning` | Intolerance |
| `.allergen-badge.attention` | `#fff7ed` | `#c2410c` | Allergy |
| `.allergen-badge.critical` | `--critical-bg` | `--critical` | Anaphylactic |

### Upload Zone

`.upload-zone`:
- `--surface-soft` background, `2px dashed --hairline` border, 10px radius
- Centered grid layout, 36px vertical padding
- Hover: `--primary-soft` background, `--primary` border colour
- Accepts drag-and-drop and click-to-browse

### Calendar Grid

`.calendar-grid`:
- CSS Grid: 100px label column + 7 equal day columns
- 6px gap, horizontal scroll on narrow viewports
- Header cells: `--surface-mid`, uppercase label style
- Slot labels: `--surface-soft`
- Meal cells: transparent background, white meal cards inside

### Detail Panel (Slide-out)

`.detail-panel`:
- Fixed position, right edge, full height
- `--canvas` background, left border + shadow: `rgba(15,23,42,0.08)`
- Max-width: 400px, z-index: 20
- Contains: close button, meal name, clinical note, MacroSlider, macro summary row, ingredient list, recipe link, regenerate button

---

## Authentication Screen

Two-column split:
- **Left panel** (`.auth-showcase`): deep teal-to-navy gradient (`#0f766e → #0f172a`), 14px border-radius, app name + tagline in white, `rgba(255,255,255,0.7)` subtitle
- **Right panel**: white card, centered vertically, sign-in/sign-up segmented control, standard form fields

---

## Responsive Behaviour

| Breakpoint | Change |
|---|---|
| `≤ 900px` | Sidebar hidden; topbar replaces it. Feature grid → 2 columns. Profile layout → single column. |
| `≤ 640px` | Field pairs and radio rows → single column. Auth showcase shrinks to 36vh. |

---

## Do's

- Use `--primary` (teal) only for the active state, primary buttons, and focus indicators
- Keep `h1` at 24px — this is a dashboard, not a marketing page
- Use `--surface-soft` as the page background to give cards visual lift without shadows
- Keep button radius at 8px — professional, not pill-shaped
- Use uppercase + letter-spacing for category labels, never for body text

## Don'ts

- Don't use pill buttons (`border-radius: 100px`) — reserved for badge/chip elements only
- Don't introduce additional accent colours — teal is the only brand colour
- Don't use box shadows on cards — background contrast handles depth
- Don't use large display type — no element in the app needs font-size above 36px (auth showcase only)
- Don't add hover states on non-interactive elements
