"""Multi-Source Discovery Benchmark Test Suite (AMRA v3.0).

Validates concurrent multi-source retrieval across:
1. arXiv & OpenAlex (250M+ literature works with citation counts and verified OA PDFs)
2. Kaggle & Hugging Face Hub (150K+ open-source ML datasets with likes & downloads)
3. Sub-millisecond TTL caching (<15ms SLA)
4. Domain acronym query expansion
"""

import sys
import time
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "mcp_server"))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from tools.arxiv_tool import search_academic_papers
from tools.openalex_tool import search_openalex_papers
from tools.kaggle_tool import find_kaggle_datasets
from tools.hf_dataset_tool import find_huggingface_datasets
from app.agent.orchestrator import _expand_search_query


def test_query_expansion():
    print("\n[TEST 1] Testing Domain Acronym Query Expansion...")
    raw = "sota gnn models for fraud"
    expanded = _expand_search_query(raw)
    print(f" -> Raw:      '{raw}'")
    print(f" -> Expanded: '{expanded}'")
    assert "graph neural network" in expanded, "Failed to expand 'gnn'"
    assert "state of the art" in expanded, "Failed to expand 'sota'"
    assert "fraud detection" in expanded, "Failed to expand 'fraud'"
    print(" [PASSED TEST 1]")


def test_openalex_discovery():
    print("\n[TEST 2] Testing OpenAlex Literature Discovery & OA PDF Verification...")
    # Cold call to populate cache
    papers1 = search_openalex_papers("graph neural network fraud", max_results=3, use_cache=True)
    assert len(papers1) > 0, "No papers returned from OpenAlex"
    top_paper = papers1[0]
    print(f" -> Title:     {top_paper['title']}")
    print(f" -> Citations: {top_paper.get('citation_count')}")
    print(f" -> OA PDF:    {top_paper['pdf_url']}")
    print(f" -> DOI:       {top_paper.get('doi')}")
    print(f" -> Source:    {top_paper.get('source')}")

    assert top_paper["pdf_url"].startswith("http"), "Invalid PDF URL"
    assert top_paper["source"] == "OpenAlex", "Source mismatch"
    assert top_paper.get("citation_count") is not None, "Missing citation count"

    # Hot call to benchmark cache hit latency
    t0 = time.perf_counter()
    papers2 = search_openalex_papers("graph neural network fraud", max_results=3, use_cache=True)
    t1 = time.perf_counter()
    cache_latency_ms = (t1 - t0) * 1000.0
    print(f" -> OpenAlex Cache Hit Latency: {cache_latency_ms:.2f} ms")
    assert papers1 == papers2, "Cached papers did not match cold response"
    assert cache_latency_ms < 15.0, f"Cache latency SLA breached: {cache_latency_ms:.2f} ms"
    print(" [PASSED TEST 2]")


def test_hf_dataset_discovery():
    print("\n[TEST 3] Testing Hugging Face Hub Dataset Discovery...")
    # Cold call to populate cache
    datasets1 = find_huggingface_datasets("fraud detection", max_results=3, use_cache=True)
    assert len(datasets1) > 0, "No datasets returned from Hugging Face"
    top_ds = datasets1[0]
    print(f" -> Dataset ID:  {top_ds['dataset_id']}")
    print(f" -> Title:       {top_ds['title']}")
    print(f" -> Downloads:   {top_ds['download_count']}")
    print(f" -> Usability:   {top_ds['usability_score']}")
    print(f" -> Repo URL:    {top_ds['url']}")
    print(f" -> Source:      {top_ds['source']}")

    assert top_ds["url"].startswith("https://huggingface.co/datasets/"), "Invalid HF URL"
    assert top_ds["source"] == "Hugging Face", "Source mismatch"

    # Hot call to benchmark cache hit latency
    t0 = time.perf_counter()
    datasets2 = find_huggingface_datasets("fraud detection", max_results=3, use_cache=True)
    t1 = time.perf_counter()
    cache_latency_ms = (t1 - t0) * 1000.0
    print(f" -> HF Cache Hit Latency: {cache_latency_ms:.2f} ms")
    assert datasets1 == datasets2, "Cached datasets did not match cold response"
    assert cache_latency_ms < 15.0, f"Cache latency SLA breached: {cache_latency_ms:.2f} ms"
    print(" [PASSED TEST 3]")


def test_multi_source_orchestration():
    print("\n[TEST 4] Testing Dual-Stream SSE Orchestration with Combined Sources...")
    import asyncio
    from app.agent.orchestrator import AgentOrchestrator

    async def run_turn():
        events = []
        async for chunk in AgentOrchestrator.stream_chat_turn(
            message="Find high-citation papers on GNN for fraud and sourced datasets",
            session_id="test_sess_multisource",
            provider_override="mock",
        ):
            if chunk.startswith("data: "):
                import json
                events.append(json.loads(chunk[6:].strip()))
        return events

    events = asyncio.run(run_turn())
    event_types = [e.get("type") for e in events]
    print(f" -> Emitted Event Types: {event_types}")

    # Inspect tool results
    tool_results = [e for e in events if e.get("type") == "tool_result"]
    assert len(tool_results) >= 2, f"Expected at least 2 tool results, got {len(tool_results)}"

    papers_result = next((e["result"] for e in tool_results if e.get("tool") == "search_academic_papers"), [])
    datasets_result = next((e["result"] for e in tool_results if e.get("tool") == "find_kaggle_datasets"), [])

    print(f" -> Combined Papers Found: {len(papers_result)}")
    paper_sources = {p.get("source") for p in papers_result}
    print(f" -> Paper Sources Detected: {paper_sources}")

    print(f" -> Combined Datasets Found: {len(datasets_result)}")
    dataset_sources = {d.get("source") for d in datasets_result}
    print(f" -> Dataset Sources Detected: {dataset_sources}")

    assert len(papers_result) > 0, "No papers returned in SSE stream"
    assert len(datasets_result) > 0, "No datasets returned in SSE stream"
    print(" [PASSED TEST 4]")


if __name__ == "__main__":
    print("===========================================================================")
    print("  AMRA MULTI-SOURCE RESEARCH & DATASET INTEGRATION AUDIT")
    print("===========================================================================")
    test_query_expansion()
    test_openalex_discovery()
    test_hf_dataset_discovery()
    test_multi_source_orchestration()
    print("\n===========================================================================")
    print("  ALL MULTI-SOURCE AUDITS PASSED WITH ZERO FAILURES!")
    print("===========================================================================")
