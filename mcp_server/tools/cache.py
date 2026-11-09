"""High-performance SQLite-backed TTL Cache for MCP Tool Queries.

Thread-safe, connection-pooled SQLite cache ensuring sub-5ms retrieval
for repeated queries and resilience against upstream API rate limits.
"""

import os
import json
import sqlite3
import hashlib
import time
import threading
from pathlib import Path
from typing import Any, Optional


class QueryCache:
    """Thread-safe, connection-pooled SQLite TTL Cache for API responses."""

    def __init__(self, db_path: Optional[str | Path] = None, default_ttl_seconds: int = 86400):
        if db_path is None:
            cache_dir = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = cache_dir / "mcp_query_cache.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.default_ttl = default_ttl_seconds
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Retrieves or creates a thread-local SQLite connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_cache (
                    cache_key TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    query_params TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON tool_cache(expires_at);")

    @staticmethod
    def generate_key(tool_name: str, params: dict) -> str:
        """Computes deterministic MD5 hash for tool name + parameters."""
        serialized = json.dumps({"tool": tool_name, "params": params}, sort_keys=True)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def get(self, tool_name: str, params: dict) -> Optional[Any]:
        """Retrieves cached result if not expired. Returns None on cache miss."""
        key = self.generate_key(tool_name, params)
        now = time.time()
        conn = self._get_connection()

        cursor = conn.execute(
            "SELECT result_json, expires_at FROM tool_cache WHERE cache_key = ?",
            (key,),
        )
        row = cursor.fetchone()
        if row:
            result_json, expires_at = row
            if expires_at > now:
                return json.loads(result_json)
            else:
                with conn:
                    conn.execute("DELETE FROM tool_cache WHERE cache_key = ?", (key,))
        return None

    def set(self, tool_name: str, params: dict, result: Any, ttl_seconds: Optional[int] = None) -> None:
        """Stores result in cache with expiration timestamp."""
        key = self.generate_key(tool_name, params)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        expires_at = now + ttl
        result_json = json.dumps(result)
        params_json = json.dumps(params, sort_keys=True)
        conn = self._get_connection()

        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO tool_cache 
                (cache_key, tool_name, query_params, result_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, tool_name, params_json, result_json, now, expires_at))

    def clear_expired(self) -> int:
        """Purges all expired entries from cache."""
        now = time.time()
        conn = self._get_connection()
        with conn:
            cursor = conn.execute("DELETE FROM tool_cache WHERE expires_at <= ?", (now,))
            return cursor.rowcount

    def purge_all(self) -> None:
        """Clears entire cache."""
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM tool_cache;")


# Global singleton cache instance
global_cache = QueryCache()
