"""Persistent Multi-Tenant Conversation Memory for Multi-Turn Agent Sessions."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from ..db.database import amra_db


class ConversationMemory:
    """Thread-safe SQLite conversation store with multi-tenant user isolation."""

    def __init__(self):
        self.db = amra_db

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Stores a message in conversation history bound to a user."""
        uid = user_id or "usr_default_dev"
        self.db.add_message(
            session_id=session_id,
            user_id=uid,
            role=role,
            content=content,
            metadata=metadata,
        )

    def get_history(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves chronological message history for a session."""
        return self.db.get_session_messages(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
        )

    def clear_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Deletes all messages for a session."""
        uid = user_id or "usr_default_dev"
        self.db.delete_user_session(session_id=session_id, user_id=uid)

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Lists active sessions for a specific user, or default sessions if no user specified."""
        if user_id:
            return self.db.list_user_sessions(user_id=user_id, limit=limit)
        return self.db.list_user_sessions(user_id="usr_default_dev", limit=limit)


# Global singleton instance
session_memory = ConversationMemory()
