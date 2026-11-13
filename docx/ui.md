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
├── page.tsx                   # Main workspace shell with thick black border boundaries
└── login/
    └── page.tsx               # Neo-Brutalist authentication portal (Sign In, Sign Up, Social OAuth)
frontend/components/
├── ChatInterface.tsx          # Real-time SSE chat loop, multi-source event aggregator, user profile badge
├── PaperCard.tsx              # Multi-source literature card (arXiv + OpenAlex citations, OA PDFs & DOIs)
├── DatasetCard.tsx            # Multi-source dataset card (Kaggle + Hugging Face likes, downloads & tags)
├── ApprovalPrompt.tsx         # High-contrast HITL security confirmation modal & recipe customizer (#FF0000 fill)
├── DataPreviewTable.tsx       # Tabular data preview, searchable columns, pagination, health gauge & CSV/Parquet export
├── SessionSidebar.tsx         # SQLite research threads drawer with instant turn restoration
├── HealthBadge.tsx            # Real-time ping latency & active provider telemetry indicator
├── DossierExport.tsx          # 1-click Markdown research dossier & canonical BibTeX export bar
└── FileUploadModal.tsx        # Drag-and-drop multipart CSV file ingestion modal with 250MB guardrail
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

### 4.5 Starter Presets & Stream Interruption Controls (`ChatInterface.tsx`)
- **Starter Suggestion Chips:** Neo-Brutalist prompt cards displaying recommended research hypotheses with colored domain badges (`#FFFF00`, `#00FF00`, `#00FFFF`, `#FF00FF`), allowing 1-click execution.
- **Client-Side Stream Cancellation:** Live toggle replacing `EXECUTE` with high-contrast red `[■ STOP]` button linked to `AbortController`, halting streaming responses in $< 100\text{ ms}$.
- **Dismissible Error Alert Banner:** Red container (`#FF0000`) with warning icon and dismiss button for network/provider errors.
- **Dynamic API Base URL:** Environment-driven URL resolution (`NEXT_PUBLIC_API_URL`) via `getApiBaseUrl()`, eliminating hardcoded host vulnerabilities.

### 4.6 Research Productivity & Session Architecture (`SessionSidebar.tsx`, `HealthBadge.tsx`, `DossierExport.tsx`)
- **Session History Sidebar:** Collapsible sliding drawer (`w-80`) with thick black border and hard shadow (`8px 0 0 #000`), restoring past conversations from backend SQLite WAL store (`/api/chat/sessions`, `/api/chat/history/{id}`).
- **Health & Latency Diagnostic Pill:** Real-time telemetry monitoring (`HealthBadge.tsx`) querying `/api/health` every 15s, displaying active model engine and ping latency in milliseconds.
- **Academic Research Dossier Export:** 1-click download of academic Markdown summaries (`.md`) and canonical BibTeX citation blocks (`.bib`), ready for direct import into LaTeX / Overleaf manuscripts.

### 4.7 Custom Data Ingestion & Interactive Customization (`FileUploadModal.tsx`, `ApprovalPrompt.tsx`, `DataPreviewTable.tsx`)
- **Multipart CSV Ingestion Modal (`FileUploadModal.tsx`):** Neo-Brutalist drag-and-drop file ingestion portal (`border-4 border-black`, `shadow-[10px_10px_0_#000]`) connecting to `POST /api/data/upload`. Features instantaneous Pandas validation, column counting, sample feature preview, and automatic transition into an autonomous profiling pipeline.
- **Interactive HITL Recipe Customizer (`ApprovalPrompt.tsx`):** Collapsible drawer allowing domain researchers to calibrate the pipeline prior to disk modification:
  - Stratified Train/Test Split Slider (range 60/40 to 90/10, default 80/20) with zero data leakage guarantees.
  - Missing value imputation strategy selector (`median_impute`, `mean_impute`, `mode_impute`, `drop`).
  - Target prediction feature override input.
  - IQR Outlier Winsorization and duplicate detection toggles.
- **Searchable, Paginated & Semantically Typed Data Preview (`DataPreviewTable.tsx`):**
  - Instantaneous column search filter for high-dimensional datasets.
  - Pagination and row-density selector (5 / 10 / 25 rows per page).
  - Semantic column type badges (`numeric_continuous`, `categorical`, `identifier`, `numeric_discrete`) integrated directly into table column headers.

### 4.8 Power-User Productivity & Developer Experience (QoL Suite)
- **1-Click "Clean & Benchmark" on Dataset Cards (`DatasetCard.tsx`):** High-contrast button eliminating manual typing by dispatching autonomous data cleaning and profiling for any discovered Kaggle or Hugging Face tabular dataset in 1 click.
- **Python / Jupyter Loader Snippet (`DataPreviewTable.tsx`):** 1-click clipboard button generating boilerplate-free Pandas code to load the generated zero-leakage `train.parquet` and `test.parquet` partitions.
- **Single-Paper BibTeX Citation (`PaperCard.tsx`):** Dedicated `[📋 CITE]` button on individual paper cards copying canonical `@article` blocks for instant paper citations.
- **Developer Keyboard Shortcuts:**
  - `Ctrl + K` / `Cmd + K`: Focuses prompt input.
  - `Ctrl + U` / `Cmd + U`: Toggles custom CSV upload modal.

### 4.9 Neo-Brutalist Authentication Portal & Header Profile Badge (`app/login/page.tsx`, `ChatInterface.tsx`)
- **Dedicated Auth Portal (`/login`):**
  - High-contrast Neo-Brutalist card (`border-8 border-black`, `shadow-[12px_12px_0_#000000]`).
  - Dual-mode tab switcher (`SIGN IN` in `#FFFF00` vs `CREATE ACCOUNT` in `#00FF00`).
  - Local credentials form with client-side length and email formatting validation.
  - Production social login buttons with official SVG branding for **Google (Gmail)**, **GitHub**, and **Microsoft (Outlook)**.
  - Zero-friction sandbox test identity badges for 1-click evaluation without cloud credentials.
  - URL parameter token capture (`?token=...`) with automatic transition into workspace.
- **Dynamic Header Profile Badge (`ChatInterface.tsx`):**
  - When unauthenticated: stark Neo-Brutalist `SIGN IN` button (`bg-[#00FF00]`) linking to `/login`.
  - When authenticated: Displays avatar, researcher display name, and provider badge (`google`, `github`, `microsoft`, `local`), with single-click `[LogOut]` button.
  - `Esc`: Closes active modals/drawers or pauses streaming generation.
- **Dynamic Tab Title State:** Live status notifications (`(⚡ Reasoning...)` -> `(✓ Ready)`) enabling effortless background research while multitasking.

### 4.10 Cloudflare Pages & Multi-Tier Edge Caching Dashboard (`app/cloudflare/page.tsx`, `ChatInterface.tsx`)
- **Dedicated Cloudflare & Caching Dashboard (`/cloudflare`):**
  - **Edge PoP Telemetry:** Live global CDN status indicator (`330+ Global PoPs Active`, animated green status beacon).
  - **3-Tier Visual Topology:** Cards detailing Tier 1 (Cloudflare Edge CDN), Tier 2 (In-Memory RAM Cache), and Tier 3 (SQLite WAL Query Store).
  - **Real-Time Telemetry Cards:** Live Cache Hit Ratio (%) gauge, Cache Hits vs Misses tally, Saved Compute Latency counter, and Active In-Memory Entries count.
  - **High-Concurrency Load Burst Simulator:** Interactive control to fire 25, 50, or 100 concurrent requests against the caching layer, visualizing real-time Cold vs Cached latency comparison and throughput (RPS).
  - **Cache Management Actions:** Instant single-click `[PURGE CACHE]` button interacting with `POST /api/cache/purge` with status banners.
  - **Live HTTP Response Headers Inspector:** Inspects active `Cache-Control`, `CDN-Cache-Control`, `Cloudflare-CDN-Cache-Control`, `X-Cache: HIT/MISS`, and `Age` response headers.
- **Header Navigation Shortcut:** Main workspace header includes an `[EDGE CACHE]` button with orange Cloudflare branding icon navigating directly to `/cloudflare`.
