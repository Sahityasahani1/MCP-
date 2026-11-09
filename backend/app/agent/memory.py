"""Persistent SQLite Conversation Memory for Multi-Turn Agent Sessions."""

import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional


class ConversationMemory:
    """Thread-safe SQLite conversation store."""

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path is None:
            storage_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sessions"
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = storage_dir / "chat_history.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
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
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at REAL NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id, created_at);")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Stores a message in conversation history."""
        conn = self._get_connection()
        now = time.time()
        meta_str = json.dumps(metadata) if metadata else None
        with conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, meta_str, now),
            )

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves chronological message history for a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT role, content, metadata_json, created_at 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY id ASC 
            LIMIT ?
            """,
            (session_id, limit),
        )
        history = []
        for role, content, meta_str, created_at in cursor.fetchall():
            meta = json.loads(meta_str) if meta_str else {}
            history.append({
                "role": role,
                "content": content,
                "metadata": meta,
                "created_at": created_at,
            })
        return history

    def clear_session(self, session_id: str) -> None:
        """Deletes all messages for a session."""
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


# Global singleton instance
session_memory = ConversationMemory()
