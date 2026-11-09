# ui.md — AMRA UI/UX Specifications & Neo-Brutalism Design System

> **Frontend Framework:** Next.js 15 (App Router), React 19, TypeScript  
> **Styling Framework:** Tailwind CSS, Brutalism Design Tokens  
> **Aesthetic Archetype:** Brutalism / Anti-Design (Raw, Stark, High-Contrast, Thick Borders, 0px Radius, Hard Offset Shadows)  
> **Communication Protocol:** Server-Sent Events (SSE) Stream  

---

## 1. UI/UX Design Philosophy: Brutalism & Anti-Design

Inspired by Brutalist architecture and hacker-grade research terminals, AMRA's user interface embraces raw, honest, and unpolished aesthetics:

1. **Anti-Design & Raw Utility:** Eliminates artificial rounded corners (`border-radius: 0;`), glassmorphism, and slow transition animations (`transition: none;`). Every element has tactile, deliberate edges.
2. **Heavy Black Typography & Default Fonts:** Uses `Arial, Helvetica, sans-serif` for primary copy and `Courier New, Courier, monospace` for code, with heavy black weights (`font-weight: 900;`) and bold uppercase titles.
3. **Thick Borders & Hard Offset Shadows:** All cards and interactive elements feature thick borders (`border: 4px solid #000000;`) and stark, hard offset drop shadows (`box-shadow: 4px 4px 0 #000000;` or `6px 6px 0 #000000;`).
4. **Instant State Changes:** Interactive buttons feature zero animation delay. On `:active`, buttons translate directly into their hard shadow (`transform: translate(3px, 3px); box-shadow: none;`).
5. **Human-in-the-Loop High Alert:** Destructive or local disk actions are gated behind high-contrast warning red (`#FF0000`) containers with stark black borders.

---

## 2. Design Tokens & Visual Hierarchy

### 2.1 Brutalism Color Palette
| Token | Variable | Hex Value | WCAG Contrast Rule & Usage |
| :--- | :--- | :--- | :--- |
| **Brut Red** | `--brut-red` | `#FF0000` | Black text on Red (`card--red`); HITL security gate alert |
| **Brut Blue** | `--brut-blue` | `#0000FF` | White text on Blue (`card--blue`); primary CTA buttons, focus rings |
| **Brut Yellow**| `--brut-yellow`| `#FFFF00` | Black text on Yellow (`card--yellow`); literature discovery cards, thoughts |
| **Brut Cyan** | `--brut-cyan` | `#00FFFF` | Black text on Cyan (`card--cyan`); peer-reviewed tags, highlights |
| **Brut Black** | `--brut-black` | `#000000` | White text on Black (`card--black`); structural borders, shadows, table headers |
| **Brut White** | `--brut-white` | `#FFFFFF` | Black text on White (`card--white`); page background, data table cells |
| **Brut Green** | `--brut-green` | `#00FF00` | Black text on Green (`card--green`); dataset cards, citation badges, health scores |
| **Brut Magenta**| `--brut-magenta`| `#FF00FF` | Black text on Magenta (`card--magenta`); MCP version badges, highlights |

> **Contrast Rule:** Black text is strictly enforced on yellow, green, cyan, magenta, and red fills; white text is reserved for blue and black fills to ensure 100% WCAG AA contrast compliance.

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
├── ChatInterface.tsx          # Real-time SSE chat loop, multi-source event aggregator & thought disclosure
├── PaperCard.tsx              # Multi-source literature card (arXiv + OpenAlex citations, OA PDFs & DOIs)
├── DatasetCard.tsx            # Multi-source dataset card (Kaggle + Hugging Face likes, downloads & tags)
├── ApprovalPrompt.tsx         # High-contrast HITL security confirmation modal (#FF0000 fill)
└── DataPreviewTable.tsx       # Tabular data preview, health gauge, baseline metrics & CSV export
frontend/lib/
└── sse-client.ts              # EventSource & fetch streaming buffer parser
```

---

## 4. Multi-Source Component Specifications

### 4.1 PaperCard (`PaperCard.tsx`)
- **Card Background:** Brutalist Yellow (`#FFFF00`) with 4px solid black border and `6px 6px 0 #000000` drop shadow.
- **Source Badges:**
  - `ARXIV: {id}` or `OPENALEX: {id}` rendered in high-contrast black on white.
  - `CITATIONS: {count}` badge rendered in Brutalist Green (`#00FF00`) with `Award` icon.
  - `PEER REVIEWED` indicator in Cyan (`#00FFFF`) for OpenAlex entries.
- **Action Buttons:**
  - `VERIFIED PDF`: Direct hyperlink to canonical open-access PDF.
  - `DOI`: External link button resolving directly to `https://doi.org/...`.
- **Abstract Box:** Solid white container (`#FFFFFF`) with 2px black border.

### 4.2 DatasetCard (`DatasetCard.tsx`)
- **Card Background:** Brutalist Green (`#00FF00`) with 4px solid black border and `6px 6px 0 #000000` drop shadow.
- **Source Badges:**
  - `KAGGLE DATASET`: Solid black badge with white text.
  - `HUGGING FACE`: Solid yellow badge with black text.
  - `LIKES`: White badge with solid red heart icon (`Heart`).
  - `VERIFIED BENCHMARK`: Magenta badge (`#FF00FF`) for offline catalog fallbacks.
- **Modality Tags:** Monospace tags (`#tabular`, `#csv`, `#finance`, `#classification`).
- **3-Column Metrics Grid:** Individual white brutalist boxes for Usability Score (%), File Size (MB), and Download Counts.

### 4.3 ApprovalPrompt (`ApprovalPrompt.tsx`)
- **Card Background:** High-alert Brutalist Red (`#FF0000`) with 4px solid black border.
- **Security Gating:** Displays target dataset ID, proposed transformations, and single-use cryptographic token.
- **Interactive Action:** `APPROVE & CLEAN DATASET` CTA button with active shadow translation.

### 4.4 DataPreviewTable (`DataPreviewTable.tsx`)
- **Header Summary:** Dual-state Data Health Score gauge ($0.0 \to 100.0$) with delta indicator (`+1.4 pts`).
- **Baseline ML Metrics:** Displays LightGBM benchmark results (Algorithm, Accuracy, ROC-AUC).
- **Tabular Grid:** First 5 rows of cleaned data in a stark grid with black headers and alternating white rows.
- **Export Action:** Direct download button for cleaned CSV and Parquet partitions.
