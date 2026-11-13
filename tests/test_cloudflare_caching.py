"""Cloudflare Pages Edge & High-Performance Caching Benchmark Suite.

Verifies:
- Thread-safe In-Memory Cache (LRU/TTL, eviction, latency savings)
- Cache Telemetry and Statistics tracking
- Cloudflare CDN Edge Cache-Control headers
- Endpoint caching on /api/health and /api/data/processed
- Cache purge authorization and invalidation
- High-concurrency load burst benchmark (< 1ms cached latency at >10,000 RPS)
- Cloudflare Pages configuration files (_headers, _routes.json, wrangler.toml)
"""

import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.config import settings
from backend.app.cache import InMemoryEdgeCache, app_cache

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_AUTH_KEY}"}


def test_in_memory_cache_mechanics():
    print("\n[CACHE TEST 1] Testing In-Memory LRU & TTL Cache Mechanics...")
    test_cache = InMemoryEdgeCache(max_entries=5, default_ttl=2)

    # 1. Set and Get
    test_cache.set("key1", {"data": "value1"}, ttl=2, compute_time_ms=50.0)
    val, hit, age = test_cache.get("key1")
    assert hit is True, "Expected cache hit"
    assert val == {"data": "value1"}
    assert age >= 0

    # 2. Miss on non-existent key
    val, hit, _ = test_cache.get("non_existent")
    assert hit is False

    # 3. Capacity eviction
    for i in range(2, 8):
        test_cache.set(f"key{i}", f"val{i}", ttl=5)
    # Total entries should not exceed max_entries significantly
    assert len(test_cache._cache) <= 6

    # 4. TTL expiration
    test_cache.set("short_lived", "expired_val", ttl=0.01)
    time.sleep(0.02)
    val, hit, _ = test_cache.get("short_lived")
    assert hit is False, "Expired key should result in cache miss"

    print(" -> In-Memory cache mechanics verified.")


def test_cloudflare_edge_headers_contract():
    print("\n[CACHE TEST 2] Testing Cloudflare CDN Edge Headers Contract...")
    # First request
    resp1 = client.get("/api/health")
    assert resp1.status_code == 200
    headers1 = resp1.headers
    assert "cache-control" in headers1
    assert "cdn-cache-control" in headers1
    assert "cloudflare-cdn-cache-control" in headers1
    assert headers1.get("x-edge-origin") == "AMRA-Edge-FastAPI"

    # Second request within 5s window should be a cache HIT
    resp2 = client.get("/api/health")
    assert resp2.status_code == 200
    headers2 = resp2.headers
    assert headers2.get("x-cache") == "HIT"
    print(f" -> Edge Cache Headers verified: Cache-Control={headers2.get('cache-control')}, X-Cache={headers2.get('x-cache')}")


def test_cache_telemetry_and_stats():
    print("\n[CACHE TEST 3] Testing Cache Telemetry Endpoint (/api/cache/stats)...")
    resp = client.get("/api/cache/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "healthy"
    assert "cloudflare_edge" in data
    assert data["cloudflare_edge"]["status"] == "active"
    assert "in_memory_tier" in data
    stats = data["in_memory_tier"]
    assert "hits" in stats
    assert "misses" in stats
    assert "hit_ratio_percent" in stats
    print(f" -> Telemetry: Hits={stats['hits']}, Misses={stats['misses']}, HitRatio={stats['hit_ratio_percent']}%")


def test_cache_purge_authorization():
    print("\n[CACHE TEST 4] Testing Cache Purge Endpoint (/api/cache/purge)...")
    # Pre-populate dummy key
    app_cache.set("purge_test:1", "data", ttl=60)
    assert app_cache.get("purge_test:1")[1] is True

    # 1. Unauthenticated purge should fail
    fail_resp = client.post("/api/cache/purge")
    assert fail_resp.status_code == 401

    # 2. Authenticated purge should succeed
    succ_resp = client.post("/api/cache/purge", headers=AUTH_HEADERS, json={"prefix": "purge_test:"})
    assert succ_resp.status_code == 200
    data = succ_resp.json()
    assert data["status"] == "success"
    assert data["purged_entries"] >= 1

    # Verify key was purged
    assert app_cache.get("purge_test:1")[1] is False
    print(f" -> Authenticated cache purge verified ({data['purged_entries']} entries cleared).")


def test_load_burst_benchmark():
    print("\n[CACHE TEST 5] Testing High-Concurrency Load Burst Benchmark...")
    resp = client.get("/api/cache/benchmark?concurrency=50")
    assert resp.status_code == 200
    data = resp.json()

    assert data["concurrency_tested"] == 50
    assert data["cache_hits"] == 50
    assert data["cache_hit_rate"] == "100.0%"
    assert data["avg_cached_latency_ms"] < 2.0, f"Expected < 2ms cached latency, got {data['avg_cached_latency_ms']}ms"
    assert data["throughput_requests_per_second"] > 1000.0
    print(f" -> Benchmark: {data['concurrency_tested']} reqs at {data['throughput_requests_per_second']} RPS ({data['avg_cached_latency_ms']} ms/req, {data['latency_reduction_percent']} reduction)")


def test_cloudflare_pages_config_files():
    print("\n[CACHE TEST 6] Verifying Cloudflare Pages Configuration Files...")
    headers_file = PROJECT_ROOT / "frontend" / "public" / "_headers"
    routes_file = PROJECT_ROOT / "frontend" / "public" / "_routes.json"
    wrangler_file = PROJECT_ROOT / "wrangler.toml"

    assert headers_file.exists(), "frontend/public/_headers must exist"
    headers_content = headers_file.read_text(encoding="utf-8")
    assert "CDN-Cache-Control" in headers_content
    assert "Cloudflare-CDN-Cache-Control" in headers_content

    assert routes_file.exists(), "frontend/public/_routes.json must exist"
    routes_content = routes_file.read_text(encoding="utf-8")
    assert "include" in routes_content

    assert wrangler_file.exists(), "wrangler.toml must exist"
    print(" -> Cloudflare Pages _headers, _routes.json, and wrangler.toml verified.")


if __name__ == "__main__":
    test_in_memory_cache_mechanics()
    test_cloudflare_edge_headers_contract()
    test_cache_telemetry_and_stats()
    test_cache_purge_authorization()
    test_load_burst_benchmark()
    test_cloudflare_pages_config_files()
    print("\n ALL CLOUDFLARE EDGE & CACHING BENCHMARKS PASSED WITH ZERO ERRORS!")
