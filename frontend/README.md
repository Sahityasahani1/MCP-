# Frontend — Autonomous ML Research Agent (AMRA)

Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS with Neo-Brutalism Design Tokens & Cloudflare Pages Edge Deployment.

## Key Routes & Pages

- **`/` (`app/page.tsx`):** Main research workspace with real-time SSE streaming, multi-source card aggregation, collapsible thought disclosure, model engine switcher, and custom CSV upload modal.
- **`/login` (`app/login/page.tsx`):** Neo-Brutalist authentication portal featuring tabbed Sign In / Create Account forms, NIST PBKDF2 password security, and working OAuth 2.0 social sign-in buttons for Google (Gmail), GitHub, and Microsoft (Outlook).
- **`/cloudflare` (`app/cloudflare/page.tsx`):** Cloudflare Pages Edge Caching & Telemetry Dashboard with live cache hit/miss stats, active entries, an interactive 50-request load burst benchmark simulator, cache purge controls, and live HTTP header inspection.

## Key Components

- **`ChatInterface.tsx`:** Real-time Server-Sent Events (SSE) chat container with multi-source card aggregation, collapsible thought disclosure, provider switcher, edge cache navigation button, and user profile header badge with single-click logout.
- **`PaperCard.tsx`:** Multi-source literature card displaying arXiv preprints and OpenAlex peer-reviewed research (with citation counts, peer-reviewed tags, DOIs, and verified open-access PDF links).
- **`DatasetCard.tsx`:** Multi-source dataset card supporting Kaggle and Hugging Face Hub repositories (with usability scores, community downloads, likes, and modality tags).
- **`ApprovalPrompt.tsx`:** High-contrast HITL security confirmation modal for authoring and approving single-use cryptographic pipeline tokens (`hitl_tok_...`) with interactive recipe customization.
- **`DataPreviewTable.tsx`:** Tabular preview of cleaned data, dual-state Data Health Score gauge ($0.0 \to 100.0$), LightGBM baseline ML metrics, and CSV/Apache Parquet export downloads.
- **`SessionSidebar.tsx`:** Sliding drawer restoring past conversational research threads from backend SQLite WAL store.
- **`FileUploadModal.tsx`:** Drag-and-drop CSV ingestion modal with 250 MB ceiling protection.
- **`DossierExport.tsx`:** 1-click download of academic research dossiers (`.md`) and canonical BibTeX citation blocks (`.bib`).

## Cloudflare Pages Edge Deployment

```bash
# Build for Cloudflare Pages
npm run pages:build

# Deploy directly via Wrangler
npm run deploy:cloudflare
```

## Design Archetype: Neo-Brutalism
- **Tokens:** 0px border radius, 4px solid black borders, hard offset box-shadows (`box-shadow: 6px 6px 0 #000000;`), high-contrast palette (`#FFFF00`, `#00FF00`, `#00FFFF`, `#FF0000`, `#FF8000`), and instant active state translations.
