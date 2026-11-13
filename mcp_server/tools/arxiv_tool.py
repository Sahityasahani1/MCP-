"""arXiv Search Tool for Autonomous ML Research Agent.

Fetches verified academic papers from arXiv with strict metadata and direct PDF URLs.
Includes SQLite TTL query caching and HTTP atom feed fallback.
"""

from typing import List, Dict, Any, Optional
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from .cache import global_cache


def _clean_text(text: str) -> str:
    """Removes irregular whitespace and newlines."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _search_via_arxiv_package(query: str, max_results: int, sort_by: str) -> List[Dict[str, Any]]:
    """Attempts search using the official arxiv Python package."""
    import arxiv

    sort_criterion = arxiv.SortCriterion.Relevance
    if sort_by == "lastUpdatedDate":
        sort_criterion = arxiv.SortCriterion.LastUpdatedDate
    elif sort_by == "submittedDate":
        sort_criterion = arxiv.SortCriterion.SubmittedDate

    client = arxiv.Client(page_size=max_results, delay_seconds=1.0, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_criterion,
    )

    results = []
    for paper in client.results(search):
        clean_id = paper.get_short_id()
        raw_pdf = paper.pdf_url or f"https://arxiv.org/pdf/{clean_id}.pdf"
        if raw_pdf.startswith("http://"):
            raw_pdf = "https://" + raw_pdf[7:]
        if not raw_pdf.endswith(".pdf"):
            raw_pdf = f"{raw_pdf}.pdf"

        results.append({
            "id": clean_id,
            "title": _clean_text(paper.title),
            "authors": [author.name for author in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d") if paper.published else "",
            "summary": _clean_text(paper.summary)[:400] + ("..." if len(paper.summary) > 400 else ""),
            "pdf_url": raw_pdf,
            "categories": paper.categories,
        })
    return results


def _search_via_http_fallback(query: str, max_results: int, sort_by: str) -> List[Dict[str, Any]]:
    """Direct HTTP fallback to arXiv atom feed API."""
    base_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by if sort_by in ["relevance", "lastUpdatedDate", "submittedDate"] else "relevance",
        "sortOrder": "descending",
    }
    encoded_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = requests.get(encoded_url, timeout=10)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results = []

    for entry in root.findall("atom:entry", ns):
        id_elem = entry.find("atom:id", ns)
        raw_id = id_elem.text if id_elem is not None else ""
        arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

        title_elem = entry.find("atom:title", ns)
        title = _clean_text(title_elem.text) if title_elem is not None else "Untitled"

        summary_elem = entry.find("atom:summary", ns)
        summary = _clean_text(summary_elem.text) if summary_elem is not None else ""

        published_elem = entry.find("atom:published", ns)
        published = published_elem.text[:10] if published_elem is not None and published_elem.text else ""

        authors = [
            _clean_text(a.find("atom:name", ns).text)
            for a in entry.findall("atom:author", ns)
            if a.find("atom:name", ns) is not None
        ]

        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                raw_href = link.attrib.get("href", pdf_url)
                if raw_href.startswith("http://"):
                    raw_href = "https://" + raw_href[7:]
                if not raw_href.endswith(".pdf"):
                    raw_href = f"{raw_href}.pdf"
                pdf_url = raw_href
                break

        results.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "published": published,
            "summary": summary[:400] + ("..." if len(summary) > 400 else ""),
            "pdf_url": pdf_url,
            "categories": [],
        })

    return results


def search_academic_papers(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Search arXiv for academic papers with caching and zero URL hallucination."""
    clean_query = query.strip()
    if not clean_query:
        return []

    max_results = max(1, min(max_results, 10))
    cache_params = {"query": clean_query, "max_results": max_results, "sort_by": sort_by}

    # 1. Check TTL Cache
    if use_cache:
        cached = global_cache.get("arxiv_search", cache_params)
        if cached is not None:
            return cached

    # 2. Fetch from upstream
    try:
        results = _search_via_arxiv_package(clean_query, max_results, sort_by)
    except Exception:
        results = _search_via_http_fallback(clean_query, max_results, sort_by)

    # 3. Store in TTL Cache
    if use_cache and results:
        global_cache.set("arxiv_search", cache_params, results, ttl_seconds=86400)

    return results
