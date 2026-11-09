# ui.md — AMRA UI/UX Specifications & Brutalism Design System

> **Frontend Framework:** Next.js 15 (App Router), React 19, TypeScript  
> **Styling Framework:** Tailwind CSS, Brutalism Design Tokens  
> **Aesthetic Archetype:** Brutalism / Anti-Design (Raw, Stark, High-Contrast, Thick Borders, 0px Radius, Hard Offset Shadows)  
> **Communication Protocol:** Server-Sent Events (SSE) Stream  

---

## 1. UI/UX Design Philosophy: Brutalism & Anti-Design

Inspired by Brutalist architecture and hacker-grade research terminals, AMRA's user interface embraces raw, honest, and unpolished aesthetics:

1. **Anti-Design & Raw Utility:** Eliminates artificial rounded corners (`border-radius: 0;`), glassmorphism, and slow transition animations (`transition: none;`). Every element has tactile, deliberate edges.
2. **Heavy Black Typography & Default Fonts:** Uses `Arial, Helvetica, sans-serif` for primary copy and `Courier New, Courier, monospace` for code, with heavy black weights (`font-weight: 900;`) and bold uppercase titles.
3. **Thick Borders & Hard Offset Shadows:** All cards and interactive elements feature thick borders (`border: 4px solid #000000;`) and stark, hard offset drop shadows (`box-shadow: 4px 4px 0 #000000;` or `8px 8px 0 #000000;`).
4. **Instant State Changes:** Interactive buttons feature zero animation delay. On `:active`, buttons translate directly into their hard shadow (`transform: translate(4px, 4px); box-shadow: none;`).
5. **Human-in-the-Loop High Alert:** Destructive or local disk actions are gated behind high-contrast warning red (`#FF0000`) containers with stark black borders.

---

## 2. Design Tokens & Visual Hierarchy

### 2.1 Brutalism Color Palette
| Token | Variable | Hex Value | WCAG Contrast Rule & Usage |
| :--- | :--- | :--- | :--- |
| **Brut Red** | `--brut-red` | `#FF0000` | Black text on Red (`card--red`); HITL security gate alert |
| **Brut Blue** | `--brut-blue` | `#0000FF` | White text on Blue (`card--blue`); primary CTA buttons, focus rings |
| **Brut Yellow**| `--brut-yellow`| `#FFFF00` | Black text on Yellow (`card--yellow`); arXiv literature cards, thoughts |
| **Brut Black** | `--brut-black` | `#000000` | White text on Black (`card--black`); structural borders, shadows, table headers |
| **Brut White** | `--brut-white` | `#FFFFFF` | Black text on White (`card--white`); page background, data table cells |
| **Brut Green** | `--brut-green` | `#00FF00` | Black text on Green (`card--green`); Kaggle dataset cards, health scores |
| **Brut Magenta**| `--brut-magenta`| `#FF00FF` | Black text on Magenta (`card--magenta`); MCP version badges, highlights |

> **Contrast Rule:** Black text is enforced on yellow, green, magenta, and red fills; white text is strictly reserved for blue and black fills to ensure 100% WCAG AA contrast compliance.

### 2.2 Typography Scale
- **Display Header:** `h1` `font-black text-xl md:text-2xl uppercase tracking-tight text-black`
- **Section Heading:** `h3` `font-black text-xs uppercase text-black bg-[#FFFF00] border-2 border-black px-2.5 py-1`
- **Card Title:** `h4` `font-black text-base uppercase text-black leading-snug`
- **Body & Prompts:** `font-bold text-sm leading-relaxed text-black`
- **Code & Metadata:** `font-mono text-xs font-bold uppercase text-black`

---

## 3. Component Architecture & Hierarchy

```
frontend/app/
├── layout.tsx                 # Root layout with 0px radius, selection highlights & font setup
└── page.tsx                   # Main workspace shell with thick black border boundaries
frontend/components/
├── ChatInterface.tsx          # Real-time SSE chat loop, engine switcher & thought disclosure
├── PaperCard.tsx              # Brutalist arXiv literature discovery card (#FFFF00 fill)
├── DatasetCard.tsx            # Brutalist Kaggle dataset card (#00FF00 fill)
├── ApprovalPrompt.tsx         # High-contrast HITL security confirmation modal (#FF0000 fill)
└── DataPreviewTable.tsx       # Tabular data preview, health gauge & CSV export
frontend/lib/
└── sse-client.ts              # EventSource & fetch streaming buffer parser
```

---

## 4. Component Specifications

### 4.1 Header & Status Bar (`ChatInterface.tsx`)
- **Brand Title:** `AMRA // RESEARCH AGENT` in heavy black uppercase.
- **MCP Version Tag:** `MCP v2.0` in `#FF00FF` magenta chip with 2px black border.
- **Engine Switcher:**
  - Active Engine: `#0000FF` blue fill with white text, 2px border, 2px hard shadow.
  - Inactive Engine: White fill with black text, hover yellow `#FFFF00` fill.

### 4.2 PaperCard (`components/PaperCard.tsx`)
- **Container:** Yellow background (`#FFFF00`), 4px solid black border, 6px hard shadow.
- **Top Bar:** White arXiv ID tag with 2px border; Verified PDF button with `#0000FF` blue fill and white text.
- **Abstract Box:** White background with 2px black border and 3px hard shadow.

### 4.3 DatasetCard (`components/DatasetCard.tsx`)
- **Container:** Green background (`#00FF00`), 4px solid black border, 6px hard shadow.
- **Badges:** Black Kaggle chip with white text; Magenta demo benchmark tag.
- **Metrics Grid:** 3 white metric cards with 2px black borders and 3px hard shadows displaying Usability, Size, and Download Counts.

### 4.4 ApprovalPrompt (`components/ApprovalPrompt.tsx`)
- **Container:** Warning Red background (`#FF0000`), 4px solid black border, 8px hard shadow.
- **Warning Banner:** Black chip with yellow alert icon and white text.
- **Cleaning Recipe:** White background with 3px black border displaying proposed parameters in monospace.
- **CTA Buttons:** Green `#00FF00` approval button with black text; white abort button with black border.

### 4.5 DataPreviewTable (`components/DataPreviewTable.tsx`)
- **Container:** White background, 4px solid black border, 8px hard shadow.
- **Health Score Badge:** Green `#00FF00` chip with black text and delta indicator.
- **Metric Tiles:** 4 yellow `#FFFF00` metric cards displaying clean rows, columns, nulls resolved, and duplicates dropped.
- **Tab Switcher:** Black active tab with white text; white inactive tabs with hover yellow.
- **Table Grid:** Solid black 3px border, black header row with white text, alternating white and neutral-100 rows with 2px black cell borders.

---

## 5. Accessibility & Motion Rules

- **WCAG AA Contrast:** Checked across all color pairs. High-contrast black type on high-luminance fills (yellow, green, white, red); high-contrast white type on low-luminance fills (blue, black).
- **Focus Rings:** Visible focus ring on all interactive elements via `outline: 4px solid #0000FF !important; outline-offset: 4px !important;`.
- **Labels:** Explicit `aria-label` attributes on icon-only and interactive controls.
- **Prefers-Reduced-Motion:** Instant transitions by default (`transition: none;`); `@media (prefers-reduced-motion: reduce)` zeroes all remaining animation properties.
