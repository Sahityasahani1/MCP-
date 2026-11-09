# Frontend — Autonomous ML Research Agent (AMRA)

Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS with Neo-Brutalism Design Tokens.

## Key Components

- **`ChatInterface.tsx`:** Real-time Server-Sent Events (SSE) chat container with multi-source card aggregation, collapsible thought disclosure, provider switcher, and auto-scroll.
- **`PaperCard.tsx`:** Multi-source literature card displaying arXiv preprints and OpenAlex peer-reviewed research (with citation counts, peer-reviewed tags, DOIs, and verified open-access PDF links).
- **`DatasetCard.tsx`:** Multi-source dataset card supporting Kaggle and Hugging Face Hub repositories (with usability scores, community downloads, likes, and modality tags).
- **`ApprovalPrompt.tsx`:** High-contrast HITL security confirmation modal for authoring and approving single-use cryptographic pipeline tokens (`hitl_tok_...`).
- **`DataPreviewTable.tsx`:** Tabular preview of cleaned data, dual-state Data Health Score gauge ($0.0 \to 100.0$), LightGBM baseline ML metrics, and CSV/Apache Parquet export downloads.

## Design Archetype: Neo-Brutalism
- **Tokens:** 0px border radius, 4px solid black borders, hard offset box-shadows (`box-shadow: 6px 6px 0 #000000;`), high-contrast palette (`#FFFF00`, `#00FF00`, `#00FFFF`, `#FF0000`), and instant active state translations.
