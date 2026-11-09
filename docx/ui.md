# ui.md — AMRA Interactive Cursor Design System Specifications

> **Frontend Framework:** Next.js 15 (App Router), React 19, TypeScript  
> **Aesthetic Archetype:** Interactive Cursor Design (Custom Cursor, Cursor as Tool, Morphing, Trails, Magnetic Pull)  
> **Color Palette:** Primary `#000000`, `#FFFFFF`; Secondary `#EC4899`, `#111827`  
> **Communication Protocol:** Real-time Server-Sent Events (SSE) Stream  

---

> ⚠️ **Industry & Use-Case Suitability Notice:**
> Interactive Cursor Design transforms the cursor into a primary engagement mechanism. While ideal for creative portfolios, agency showcases, and interactive demonstrations, custom cursor mechanics and magnetic pull are generally avoided in mobile-first applications (where touch replaces pointer interactions), dense financial data entry forms, and accessibility-critical environments. 
> To safeguard accessibility, AMRA strictly disables custom cursor trails and magnetic motions under `prefers-reduced-motion: reduce`, preserves visible native keyboard focus indicators (`:focus-visible`), and activates `cursor: none` *only* inside `@media (hover: hover) and (pointer: fine)`.

---

## 1. Interactive Cursor Architecture & Capabilities

1. **Native Cursor Hiding with Media Boundaries:**
   - The native operating system pointer is hidden with `cursor: none !important;` *only* on devices reporting `@media (hover: hover) and (pointer: fine)`. Mobile and touch devices retain their default native behavior.
2. **Dual-Layer Fixed Cursor Loop (`requestAnimationFrame` & `translate3d`):**
   - **Central Core Dot:** 8px circle with zero latency following the exact mouse coordinate.
   - **Follower Ring:** Smoothly interpolated follower with a linear interpolation factor ($\text{lerp} \approx 0.18$). When distance $< 0.1\text{px}$, the animation frame cancels automatically to eliminate idle CPU cycles.
3. **Inversion with `mix-blend-mode: difference`:**
   - The cursor inverts colors cleanly against light and dark content (`#FFFFFF` inverts against `#000000`, `#111827`, and `#EC4899`).
4. **Context-Aware Morphing (`data-cursor`):**
   - When hovering interactive targets (and *never* on static text or cards), the ring expands to 56px and displays a context label:
     - `data-cursor="switch"` over AI mode buttons.
     - `data-cursor="pdf"` over verified paper PDF buttons.
     - `data-cursor="view"` over dataset source links.
     - `data-cursor="approve"` over data preparation buttons.
     - `data-cursor="cancel"` over cancel buttons.
     - `data-cursor="tab"` over preview tabs.
     - `data-cursor="csv"` over spreadsheet download links.
     - `data-cursor="send"` over research prompt submission.
5. **Magnetic Button Attraction (`data-magnetic="true"`):**
   - When the pointer enters a magnetic button, the element is drawn toward the pointer coordinates by approximately 25% of the distance from center:
     $$\Delta X = (X_{\text{mouse}} - X_{\text{center}}) \times 0.25, \quad \Delta Y = (Y_{\text{mouse}} - Y_{\text{center}}) \times 0.25$$
   - On `pointerleave`, the element smoothly eases back to origin with `transform: translate3d(0, 0, 0)` using a cubic bezier transition.
6. **Trailing Particle Effects:**
   - Emits a trailing tail of 4 translucent pink `#EC4899` particle dots that dynamically fade behind pointer movements.

---

## 2. Design Tokens & Visual Hierarchy

### 2.1 Color Palette
| Token | Variable | Hex Value | Semantic Usage & Contrast |
| :--- | :--- | :--- | :--- |
| **Primary Black** | `--cursor-primary-black` | `#000000` | Input backgrounds, metric tiles, depth overlays |
| **Primary White** | `--cursor-primary-white` | `#FFFFFF` | Primary headings, button text, inverted cursor dot |
| **Secondary Pink** | `--cursor-secondary-pink` | `#EC4899` | Primary action buttons, active badges, cursor trails |
| **Secondary Dark** | `--cursor-secondary-dark` | `#111827` | Deep slate page background & card containers |

### 2.2 Contrast & Accessibility Compliance
- **WCAG AA Compliance:** `#FFFFFF` text on `#111827` delivers a contrast ratio $> 16:1$ (AAA standard). Black text on `#EC4899` and `#EC4899` text on `#111827` deliver $> 4.5:1$ (AA standard).
- **Keyboard Navigation:** Native focus outlines are preserved for keyboard tab traversal (`outline: 2px solid #EC4899 !important; outline-offset: 3px !important;`).
- **Screen Reader Support:** All icon-only controls carry explicit `aria-label` attributes.

---

## 3. Component Architecture & Hierarchy

```
frontend/app/
├── layout.tsx                 # Injects <InteractiveCursor /> & root #111827 dark canvas
└── page.tsx                   # Centered responsive workspace container
frontend/components/
├── InteractiveCursor.tsx      # Core rAF cursor controller, morphing engine & magnetic tracker
├── ChatInterface.tsx          # Real-time chat loop with magnetic switchers & send CTA
├── PaperCard.tsx              # Paper card with magnetic "Read PDF" morphing button
├── DatasetCard.tsx            # Dataset card with magnetic "View Source" morphing link
├── ApprovalPrompt.tsx         # Safety prompt with magnetic "Approve" and "Cancel" buttons
└── DataPreviewTable.tsx       # Tabular data preview with magnetic tabs & download CTA
frontend/lib/
└── sse-client.ts              # EventSource & fetch streaming buffer parser
```
