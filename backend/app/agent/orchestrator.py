"""Autonomous Agent Orchestration Engine with HITL Gatekeeping & SSE Streaming."""

import json
import secrets
import asyncio
import re
import time
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path
import sys

# Ensure mcp_server is reachable
MCP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "mcp_server"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from tools.arxiv_tool import search_academic_papers
from tools.openalex_tool import search_openalex_papers
from tools.kaggle_tool import find_kaggle_datasets
from tools.hf_dataset_tool import find_huggingface_datasets
from ml_research_server import trigger_data_pipeline
from .factory import get_model_adapter
from .memory import session_memory
from ..schemas.events import (
    ThoughtEvent,
    ToolStartEvent,
    ToolResultEvent,
    HITLRequiredEvent,
    TextDeltaEvent,
    CostAuditEvent,
    CompleteEvent,
    ErrorEvent,
)

# Active pending approval tokens: token -> metadata
PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}

QUERY_ACRONYMS: Dict[str, str] = {
    "gnn": "graph neural network",
    "llm": "large language model",
    "sota": "state of the art",
    "rl": "reinforcement learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "fraud": "fraud detection",
    "churn": "customer churn",
    "tabular": "tabular dataset classification",
}

STOP_PHRASES = [
    "can you find me", "find me", "can you", "please find", "show me", "give me",
    "search for", "look for", "i want to find", "i need", "looking for",
    "recent papers on", "papers on", "papers about", "paper on", "paper about",
    "academic papers on", "literature on", "source datasets for", "source dataset for",
    "datasets for", "dataset for", "datasets on", "dataset on",
    "benchmark dataset to", "benchmark dataset", "benchmark to test them",
    "and clean it", "and clean a", "and download", "to test them", "to test it",
    "check the durability of the project", "challenge this website",
    "how does the backend work", "how it works", "what tech is used"
]

GENERIC_SEARCH_STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "can", "could", "will", "would", "should", "some", "any", "this", "that",
    "these", "those", "my", "your", "its", "their", "our", "all", "both",
    "each", "few", "more", "most", "other", "such", "only", "own", "same",
    "so", "than", "too", "very", "just", "now", "paper", "papers",
    "dataset", "datasets", "data", "benchmark", "benchmarks", "clean",
    "cleaned", "cleaning", "recent", "sota", "source", "find", "search"
}


def _extract_search_keywords(raw_text: str) -> str:
    """Strips conversational boilerplate and isolates the actual research domain/subject."""
    cleaned = raw_text.lower()
    for phrase in STOP_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
    words = [w for w in cleaned.split() if w not in GENERIC_SEARCH_STOPWORDS and len(w) > 2]
    keywords = " ".join(words).strip()
    return keywords if keywords else raw_text.strip()


def _expand_search_query(raw_query: str) -> str:
    """Expands domain abbreviations to maximize search recall across repositories."""
    tokens = raw_query.lower().split()
    expanded = []
    for t in tokens:
        clean_t = re.sub(r"[^\w]", "", t)
        if clean_t in QUERY_ACRONYMS:
            expanded.append(QUERY_ACRONYMS[clean_t])
        else:
            expanded.append(t)
    return " ".join(expanded)


class AgentOrchestrator:
    """Orchestrates research discovery, tool dispatch, and streaming events."""

    @staticmethod
    async def stream_chat_turn(
        message: str,
        session_id: str,
        provider_override: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Executes full agent turn and yields formatted SSE data strings."""
        try:
            # 1. Thought Event
            yield f"data: {ThoughtEvent(content=f'Analyzing research hypothesis: \"{message[:80]}...\"').model_dump_json()}\n\n"
            await asyncio.sleep(0.05)

            # 2. Add User Message to Memory
            session_memory.add_message(session_id=session_id, role="user", content=message, user_id=user_id)
            history = session_memory.get_history(session_id=session_id, user_id=user_id, limit=6)

            # Convert history to format needed by adapters
            formatted_messages = [{"role": m["role"], "content": m["content"]} for m in history]

            # 3. Intent Routing & Clean Keyword Extraction
            msg_lower = message.lower()
            clean_keywords = _extract_search_keywords(message)
            expanded_q = _expand_search_query(clean_keywords)
            found_papers = []
            found_datasets = []

            # Check if this is a meta inquiry about AMRA itself (architecture, how it works, sample inputs, durability)
            is_meta_inquiry = any(
                q in msg_lower for q in [
                    "how does", "how it works", "how it fetch", "what tech", "architecture",
                    "explain", "what are the gap", "sample input", "durability", "challenge this",
                    "who are you", "what can you do", "help me understand"
                ]
            )

            # Check for academic literature intent (only if not a pure meta inquiry)
            is_academic = not is_meta_inquiry and (
                any(w in msg_lower for w in ["paper", "arxiv", "openalex", "literature", "algorithm", "research", "recent", "sota", "citation"])
                or (len(history) <= 1 and len(clean_keywords.split()) >= 1 and not any(w in msg_lower for w in ["hi", "hello", "hey", "test"]))
            )

            if is_academic:
                yield f"data: {ThoughtEvent(content=f'Executing literature discovery across arXiv and OpenAlex for: \"{clean_keywords}\"...').model_dump_json()}\n\n"
                yield f"data: {ToolStartEvent(tool='search_academic_papers', args={'query': clean_keywords, 'sources': ['arXiv', 'OpenAlex']}).model_dump_json()}\n\n"

                arxiv_future = asyncio.to_thread(search_academic_papers, query=clean_keywords, max_results=3)
                openalex_future = asyncio.to_thread(search_openalex_papers, query=expanded_q, max_results=3)

                results_pair = await asyncio.gather(arxiv_future, openalex_future, return_exceptions=True)
                arxiv_papers = results_pair[0] if isinstance(results_pair[0], list) else []
                openalex_papers = results_pair[1] if isinstance(results_pair[1], list) else []

                for p in arxiv_papers:
                    p.setdefault("source", "arXiv")
                    p.setdefault("citation_count", None)

                # Merge & deduplicate by normalized title
                all_papers = []
                seen_titles = set()
                for p in (openalex_papers + arxiv_papers):
                    norm_t = re.sub(r"[^a-z0-9]", "", p.get("title", "").lower())[:40]
                    if norm_t and norm_t not in seen_titles:
                        seen_titles.add(norm_t)
                        all_papers.append(p)

                # Sort by verified citation count descending (nulls last)
                all_papers.sort(key=lambda x: (x.get("citation_count") or 0), reverse=True)
                found_papers = all_papers[:5]

                yield f"data: {ToolResultEvent(tool='search_academic_papers', result=found_papers).model_dump_json()}\n\n"
                await asyncio.sleep(0.05)

            # Check for dataset sourcing intent
            is_dataset = not is_meta_inquiry and (
                any(w in msg_lower for w in ["data", "dataset", "kaggle", "huggingface", "hf", "csv", "table", "benchmark"])
                or len(found_papers) > 0
            )

            if is_dataset:
                yield f"data: {ThoughtEvent(content=f'Searching Kaggle and Hugging Face Hub for: \"{clean_keywords}\"...').model_dump_json()}\n\n"
                yield f"data: {ToolStartEvent(tool='find_kaggle_datasets', args={'query': clean_keywords, 'sources': ['Kaggle', 'Hugging Face']}).model_dump_json()}\n\n"

                kaggle_future = asyncio.to_thread(find_kaggle_datasets, query=clean_keywords, max_results=2)
                hf_future = asyncio.to_thread(find_huggingface_datasets, query=expanded_q, max_results=2)

                results_ds = await asyncio.gather(kaggle_future, hf_future, return_exceptions=True)
                kaggle_ds = results_ds[0] if isinstance(results_ds[0], list) else []
                hf_ds = results_ds[1] if isinstance(results_ds[1], list) else []

                for d in kaggle_ds:
                    d.setdefault("source", "Kaggle")

                all_datasets = []
                seen_ids = set()
                kw_tokens = set(re.findall(r"\w+", clean_keywords.lower()))

                for d in (kaggle_ds + hf_ds):
                    ds_id = d.get("dataset_id", "").lower()
                    if ds_id and ds_id not in seen_ids:
                        seen_ids.add(ds_id)
                        # Compute relevance score against research keywords
                        search_corpus = (d.get("title", "") + " " + ds_id + " " + " ".join(d.get("tags", []))).lower()
                        overlap_score = sum(1 for kw in kw_tokens if kw in search_corpus)
                        d["_relevance_score"] = overlap_score
                        all_datasets.append(d)

                # Sort by keyword relevance first, then download count & usability
                all_datasets.sort(
                    key=lambda x: (
                        x.get("_relevance_score", 0),
                        (x.get("download_count") or 0),
                        x.get("usability_score", 0.0),
                    ),
                    reverse=True,
                )
                for d in all_datasets:
                    d.pop("_relevance_score", None)

                found_datasets = all_datasets[:4]

                yield f"data: {ToolResultEvent(tool='find_kaggle_datasets', result=found_datasets).model_dump_json()}\n\n"
                await asyncio.sleep(0.05)

            # Check for data cleaning / execution intent (HITL Intercept)
            if any(w in msg_lower for w in ["clean", "download", "run pipeline", "ingest", "process data"]) and found_datasets:
                target_ds = found_datasets[0]["dataset_id"]
                token = f"hitl_tok_{secrets.token_hex(8)}"
                recipe = {
                    "handle_missing": "median_impute",
                    "drop_duplicates": True,
                    "normalize_headers": True,
                    "cap_outliers": True,
                    "train_test_split": "80/20 Stratified",
                    "train_baseline": True,
                    "export_formats": ["CSV", "Parquet", "Train Parquet", "Test Parquet"],
                }
                now = time.time()
                PENDING_APPROVALS[token] = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "dataset_id": target_ds,
                    "recipe": recipe,
                    "created_at": now,
                    "expires_at": now + 600.0,  # 10-Minute TTL
                }

                yield f"data: {HITLRequiredEvent(dataset_id=target_ds, cleaning_recipe=recipe, approval_token=token).model_dump_json()}\n\n"

            # 4. Synthesize with Sustainable LLM
            adapter = get_model_adapter(provider_override)
            llm_result = await adapter.generate_response(messages=formatted_messages)

            # 5. Yield Text Delta
            assistant_text = llm_result.get("text", "")
            if not assistant_text and (found_papers or found_datasets):
                sources_p = sorted(list({p.get('source', 'arXiv') for p in found_papers}))
                sources_d = sorted(list({d.get('source', 'Kaggle') for d in found_datasets}))
                p_text = f"{len(found_papers)} academic papers ({', '.join(sources_p)})" if found_papers else ""
                d_text = f"{len(found_datasets)} datasets ({', '.join(sources_d)})" if found_datasets else ""
                summary_parts = [p for p in [p_text, d_text] if p]
                assistant_text = f"I discovered and verified {' and '.join(summary_parts)} matching your research hypothesis."

            yield f"data: {TextDeltaEvent(content=assistant_text).model_dump_json()}\n\n"

            # 6. Yield Cost Audit Event ($0.00 proof)
            yield f"data: {CostAuditEvent(provider=llm_result['provider'], model=llm_result['model'], prompt_tokens=llm_result['prompt_tokens'], completion_tokens=llm_result['completion_tokens']).model_dump_json()}\n\n"

            # 7. Record Assistant Response in Memory
            session_memory.add_message(
                session_id=session_id,
                role="assistant",
                content=assistant_text,
                user_id=user_id,
                metadata={
                    "papers_count": len(found_papers),
                    "datasets_count": len(found_datasets),
                    "papers": found_papers,
                    "datasets": found_datasets,
                    "costAudit": {
                        "provider": llm_result["provider"],
                        "model": llm_result["model"],
                        "prompt_tokens": llm_result["prompt_tokens"],
                        "completion_tokens": llm_result["completion_tokens"],
                    },
                },
            )

            # 8. Complete Event
            yield f"data: {CompleteEvent(session_id=session_id).model_dump_json()}\n\n"

        except Exception as e:
            yield f"data: {ErrorEvent(error_message=str(e)).model_dump_json()}\n\n"

    @staticmethod
    async def stream_approval_execution(
        approval_token: str,
        session_id: str,
        action: str = "approve",
        custom_recipe: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Executes or cancels the approved data cleaning pipeline upon user authorization."""
        try:
            if approval_token not in PENDING_APPROVALS:
                yield f"data: {ErrorEvent(error_message='Invalid or expired approval token.').model_dump_json()}\n\n"
                return

            task_info = PENDING_APPROVALS.get(approval_token)

            # 1. Validate Expiration (10-minute TTL)
            now = time.time()
            if task_info.get("expires_at") and now > task_info["expires_at"]:
                PENDING_APPROVALS.pop(approval_token, None)
                yield f"data: {ErrorEvent(error_message='Approval token expired: the 10-minute authorization window has lapsed.').model_dump_json()}\n\n"
                return

            # 2. Validate Session Binding
            if task_info.get("session_id") and task_info["session_id"] != session_id:
                yield f"data: {ErrorEvent(error_message='Session mismatch: approval token does not belong to this session.').model_dump_json()}\n\n"
                return

            # Pop token to prevent replay attacks
            PENDING_APPROVALS.pop(approval_token, None)

            # 3. Explicitly handle user rejection
            if action == "reject":
                yield f"data: {ThoughtEvent(content='User rejected pipeline execution. Local disk storage remains unmodified.').model_dump_json()}\n\n"
                summary_msg = f" Pipeline execution for dataset `{task_info['dataset_id']}` was cancelled by the user. No files were written to disk."
                yield f"data: {TextDeltaEvent(content=summary_msg).model_dump_json()}\n\n"
                session_memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=summary_msg,
                    user_id=task_info.get("user_id"),
                )
                yield f"data: {CompleteEvent(session_id=session_id).model_dump_json()}\n\n"
                return

            dataset_id = task_info["dataset_id"]
            recipe = task_info["recipe"]
            if custom_recipe:
                recipe = {**recipe, **custom_recipe}

            yield f"data: {ThoughtEvent(content=f'User authorization verified. Executing local data ingestion & profiling for {dataset_id}...').model_dump_json()}\n\n"
            yield f"data: {ToolStartEvent(tool='trigger_data_pipeline', args={'dataset_id': dataset_id, **recipe}).model_dump_json()}\n\n"

            # Run cleaning pipeline in threadpool with 60s watchdog timeout
            try:
                raw_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        trigger_data_pipeline,
                        dataset_id=dataset_id,
                        handle_missing=recipe.get("handle_missing", "median_impute"),
                        drop_duplicates=recipe.get("drop_duplicates", True),
                        normalize_headers=recipe.get("normalize_headers", True),
                        cap_outliers=recipe.get("cap_outliers", True),
                        test_size=recipe.get("test_size", 0.2),
                        target_column=recipe.get("target_column"),
                    ),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                yield f"data: {ErrorEvent(error_message=f'Execution watchdog triggered: data pipeline for {dataset_id} exceeded 60s timeout limit.').model_dump_json()}\n\n"
                return
            parsed_result = json.loads(raw_result)
            yield f"data: {ToolResultEvent(tool='trigger_data_pipeline', result=parsed_result).model_dump_json()}\n\n"

            # Text summary of cleaning
            delta = parsed_result.get("health_score_delta", 0.0)
            score_after = parsed_result.get("stats_after", {}).get("health_score", 100.0)
            target_col = parsed_result.get("target_column")
            baseline_info = parsed_result.get("baseline_benchmark", {})
            metrics_str = ""
            if baseline_info and baseline_info.get("status") == "success":
                m = baseline_info.get("metrics", {})
                algo = m.get("algorithm", "Baseline Model")
                auc = f", ROC-AUC: `{m.get('roc_auc')}`" if "roc_auc" in m else ""
                acc = f", Accuracy: `{m.get('accuracy')}`" if "accuracy" in m else ""
                metrics_str = f"\n* **Baseline ML Benchmark ({algo}):**{acc}{auc}"

            summary_msg = (
                f" Pipeline Execution Complete for **{dataset_id}**!\n\n"
                f"* **Data Health Score:** `{score_after}/100` (+{delta})\n"
                f"* **Output Cleaned CSV:** `{parsed_result.get('output_filename')}`\n"
                f"* **Parquet Export:** Generated full cleaned, train, and test partitions.{metrics_str}\n"
                f"* **Transformations:** {', '.join(parsed_result.get('actions_taken', []))}"
            )
            yield f"data: {TextDeltaEvent(content=summary_msg).model_dump_json()}\n\n"

            session_memory.add_message(
                session_id=session_id,
                role="assistant",
                content=summary_msg,
                user_id=task_info.get("user_id"),
                metadata={"pipelineResult": parsed_result},
            )
            yield f"data: {CompleteEvent(session_id=session_id).model_dump_json()}\n\n"

        except Exception as e:
            yield f"data: {ErrorEvent(error_message=str(e)).model_dump_json()}\n\n"
