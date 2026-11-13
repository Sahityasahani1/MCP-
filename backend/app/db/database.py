"""SQLite Database Engine for AMRA Multi-Tenant User & Session Management.

Manages persistent users, credentials, user profiles, and multi-tenant isolated
chat/research session history using thread-safe SQLite in WAL mode.
"""

import sqlite3
import json
import time
import uuid
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional


class AMRADatabase:
    """Thread-safe SQLite database manager for users, sessions, and messages."""

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path is None:
            storage_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sessions"
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = storage_dir / "amra_users.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=15.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes for users, sessions, and messages."""
        conn = self._get_connection()
        with conn:
            # 1. Users Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT,
                    full_name TEXT NOT NULL,
                    avatar_url TEXT,
                    provider TEXT NOT NULL DEFAULT 'local',
                    provider_id TEXT,
                    created_at REAL NOT NULL,
                    last_login REAL NOT NULL
                );
            """)

            # 2. Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # 3. Messages Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Indexes for sub-millisecond lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);")

            # Create default developer / system user if not exists
            cursor = conn.execute("SELECT id FROM users WHERE email = 'developer@amra.local'")
            if not cursor.fetchone():
                now = time.time()
                conn.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, full_name, avatar_url, provider, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "usr_default_dev",
                        "developer@amra.local",
                        None,
                        "AMRA Research Developer",
                        "https://api.dicebear.com/7.x/bottts/svg?seed=amra_dev",
                        "system",
                        now,
                        now,
                    ),
                )

    # =========================================================================
    # USER OPERATIONS
    # =========================================================================

    def create_user(
        self,
        email: str,
        hashed_password: Optional[str],
        full_name: str,
        avatar_url: Optional[str] = None,
        provider: str = "local",
        provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new user record in the database."""
        conn = self._get_connection()
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = time.time()
        clean_email = email.strip().lower()
        avatar = avatar_url or f"https://api.dicebear.com/7.x/identicon/svg?seed={clean_email}"

        with conn:
            conn.execute(
                """
                INSERT INTO users (id, email, hashed_password, full_name, avatar_url, provider, provider_id, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, clean_email, hashed_password, full_name.strip(), avatar, provider, provider_id, now, now),
            )
        return self.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by email address."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by their primary key user_id."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by external OAuth provider and provider subject ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM users WHERE provider = ? AND provider_id = ?",
            (provider.lower(), str(provider_id)),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_last_login(self, user_id: str) -> None:
        """Updates the last_login timestamp for a user."""
        conn = self._get_connection()
        with conn:
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user_id))

    def upsert_oauth_user(
        self,
        email: str,
        full_name: str,
        avatar_url: Optional[str],
        provider: str,
        provider_id: str,
    ) -> Dict[str, Any]:
        """Finds or creates a user authenticated via Google, GitHub, or Microsoft OAuth."""
        clean_email = email.strip().lower()
        existing = self.get_user_by_provider(provider, provider_id)
        if not existing:
            # Check if email exists under local or another provider
            existing = self.get_user_by_email(clean_email)

        now = time.time()
        conn = self._get_connection()

        if existing:
            user_id = existing["id"]
            with conn:
                conn.execute(
                    """
                    UPDATE users 
                    SET full_name = ?, avatar_url = COALESCE(?, avatar_url), last_login = ?, provider = ?, provider_id = ?
                    WHERE id = ?
                    """,
                    (full_name, avatar_url, now, provider, str(provider_id), user_id),
                )
            return self.get_user_by_id(user_id)
        else:
            return self.create_user(
                email=clean_email,
                hashed_password=None,
                full_name=full_name,
                avatar_url=avatar_url,
                provider=provider,
                provider_id=str(provider_id),
            )

    # =========================================================================
    # SESSION & THREAD OPERATIONS
    # =========================================================================

    def create_or_update_session(self, session_id: str, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Creates a research thread or updates its last modified timestamp."""
        conn = self._get_connection()
        now = time.time()
        cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        with conn:
            if row:
                if title:
                    conn.execute(
                        "UPDATE sessions SET updated_at = ?, title = ? WHERE session_id = ?",
                        (now, title, session_id),
                    )
                else:
                    conn.execute(
                        "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                        (now, session_id),
                    )
            else:
                session_title = title or "New Research Thread"
                conn.execute(
                    "INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, session_title, now, now),
                )

        cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        return dict(cursor.fetchone())

    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a research session by ID."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_user_sessions(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Lists research sessions owned specifically by the given user_id."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT 
                s.session_id,
                s.title,
                s.created_at,
                s.updated_at as last_updated,
                COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.session_id
            WHERE s.user_id = ?
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [dict(r) for r in cursor.fetchall()]

    def delete_user_session(self, session_id: str, user_id: str) -> bool:
        """Deletes a session and all its messages if owned by user_id."""
        conn = self._get_connection()
        with conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            return cursor.rowcount > 0

    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================

    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Stores a conversation turn in the database, updating the session."""
        conn = self._get_connection()
        now = time.time()
        meta_str = json.dumps(metadata) if metadata else None

        # Ensure session exists
        self.create_or_update_session(session_id=session_id, user_id=user_id)

        with conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, user_id, role, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, role, content, meta_str, now),
            )

            # Update session title if first user query
            if role == "user":
                cursor = conn.execute(
                    "SELECT title FROM sessions WHERE session_id = ? AND (title = 'New Research Thread' OR title = 'Research Thread')",
                    (session_id,),
                )
                if cursor.fetchone():
                    snippet = content.strip()[:60]
                    if len(content.strip()) > 60:
                        snippet += "..."
                    conn.execute(
                        "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
                        (snippet, now, session_id),
                    )

    def get_session_messages(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves chronological messages for a session. If user_id is provided, asserts ownership."""
        conn = self._get_connection()
        if user_id:
            cursor = conn.execute(
                """
                SELECT m.role, m.content, m.metadata_json, m.created_at
                FROM messages m
                JOIN sessions s ON s.session_id = m.session_id
                WHERE m.session_id = ? AND s.user_id = ?
                ORDER BY m.id ASC
                LIMIT ?
                """,
                (session_id, user_id, limit),
            )
        else:
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

        messages = []
        for row in cursor.fetchall():
            meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            messages.append({
                "role": row["role"],
                "content": row["content"],
                "metadata": meta,
                "created_at": row["created_at"],
            })
        return messages


# Global Singleton Instance
amra_db = AMRADatabase()
