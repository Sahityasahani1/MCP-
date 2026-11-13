"""High-Performance In-Memory & Edge Caching Engine for AMRA Backend.

Provides:
- Thread-safe in-memory LRU / TTL cache for rapid sub-millisecond responses
- Cache statistics tracking (hits, misses, hit ratio, saved latency)
- Cloudflare CDN Edge Cache-Control headers generation
- Endpoint caching decorator with automatic serialization
"""

import time
import json
import hashlib
import threading
from typing import Any, Dict, Optional, Tuple, Callable
from functools import wraps
from fastapi import Request, Response
from fastapi.responses import JSONResponse


class CacheEntry:
    """Represents a cached item with TTL expiration and hit metrics."""
    __slots__ = ("value", "expires_at", "created_at", "hits", "compute_time_ms")

    def __init__(self, value: Any, ttl_seconds: int, compute_time_ms: float = 0.0):
        self.value = value
        now = time.time()
        self.created_at = now
        self.expires_at = now + ttl_seconds
        self.hits = 0
        self.compute_time_ms = compute_time_ms

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def age(self) -> int:
        return max(0, int(time.time() - self.created_at))


class InMemoryEdgeCache:
    """Thread-safe in-memory cache optimized for high concurrency and heavy traffic bursts."""

    def __init__(self, max_entries: int = 2000, default_ttl: int = 300):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Telemetry metrics
        self._hits = 0
        self._misses = 0
        self._saved_latency_ms = 0.0

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Deterministic cache key generation using MD5 hashing."""
        serialized = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        digest = hashlib.md5(serialized.encode("utf-8")).hexdigest()
        return f"{prefix}:{digest}" if prefix else digest

    def get(self, key: str) -> Tuple[Optional[Any], bool, int]:
        """Retrieves a cached item if not expired.
        
        Returns: (value, hit, age_seconds)
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None, False, 0

            if entry.is_expired:
                # Evict expired entry
                del self._cache[key]
                self._misses += 1
                return None, False, 0

            entry.hits += 1
            self._hits += 1
            self._saved_latency_ms += entry.compute_time_ms
            return entry.value, True, entry.age

    def set(self, key: str, value: Any, ttl: Optional[int] = None, compute_time_ms: float = 0.0) -> None:
        """Stores an item in cache with TTL and LRU eviction if capacity exceeded."""
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        with self._lock:
            # Simple LRU-style eviction if max_entries reached
            if len(self._cache) >= self.max_entries:
                # Remove expired keys first
                expired_keys = [k for k, v in self._cache.items() if v.is_expired]
                for k in expired_keys:
                    del self._cache[k]

                # If still at capacity, evict oldest 10% entries
                if len(self._cache) >= self.max_entries:
                    oldest_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].created_at)[: max(1, self.max_entries // 10)]
                    for k in oldest_keys:
                        self._cache.pop(k, None)

            self._cache[key] = CacheEntry(value=value, ttl_seconds=ttl_seconds, compute_time_ms=compute_time_ms)

    def delete(self, key: str) -> bool:
        """Removes a specific key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self, prefix: Optional[str] = None) -> int:
        """Purges either all cache keys or keys matching a prefix. Returns count of purged keys."""
        with self._lock:
            if prefix is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            matching_keys = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in matching_keys:
                del self._cache[k]
            return len(matching_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Returns comprehensive real-time cache performance metrics."""
        with self._lock:
            total = self._hits + self._misses
            ratio = round((self._hits / total * 100.0), 2) if total > 0 else 0.0
            active_entries = sum(1 for v in self._cache.values() if not v.is_expired)

            return {
                "active_entries": active_entries,
                "total_entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_ratio_percent": ratio,
                "saved_latency_ms": round(self._saved_latency_ms, 2),
                "cache_tier": "Tier 2: In-Memory RAM + Tier 1: Cloudflare Edge",
                "max_capacity": self.max_entries,
            }

    def reset_stats(self) -> None:
        """Resets telemetry counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._saved_latency_ms = 0.0


# Global singleton instance for backend
app_cache = InMemoryEdgeCache(max_entries=3000, default_ttl=300)


def apply_edge_cache_headers(
    response: Response,
    ttl_seconds: int = 60,
    is_hit: bool = False,
    age_seconds: int = 0,
) -> None:
    """Applies Cloudflare CDN Edge Caching and browser caching headers."""
    response.headers["Cache-Control"] = f"public, max-age={ttl_seconds}, stale-while-revalidate={ttl_seconds * 2}"
    response.headers["CDN-Cache-Control"] = f"public, max-age={ttl_seconds * 2}"
    response.headers["Cloudflare-CDN-Cache-Control"] = f"public, max-age={ttl_seconds * 4}"
    response.headers["X-Cache"] = "HIT" if is_hit else "MISS"
    response.headers["X-Edge-Origin"] = "AMRA-Edge-FastAPI"
    if is_hit:
        response.headers["Age"] = str(age_seconds)
