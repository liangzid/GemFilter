"""
Session Manager for GemFilter Skill.

Manages gem mappings across multi-turn conversations.
"""

import uuid
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict


@dataclass
class GemMapping:
    """Represents a single gem mapping."""
    fake_value: str
    original_value: str
    gem_type: str
    created_at: float = field(default_factory=time.time)


@dataclass
class Session:
    """A conversation session with gem mappings."""
    session_id: str
    mappings: Dict[str, GemMapping] = field(default_factory=dict)  # fake -> GemMapping
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def add_mapping(self, fake_value: str, original_value: str, gem_type: str) -> None:
        """Add a gem mapping to this session."""
        self.mappings[fake_value] = GemMapping(
            fake_value=fake_value,
            original_value=original_value,
            gem_type=gem_type,
        )
        self.last_accessed = time.time()

    def get_original(self, fake_value: str) -> Optional[str]:
        """Get original value for a fake placeholder."""
        mapping = self.mappings.get(fake_value)
        return mapping.original_value if mapping else None

    def get_gem_type(self, fake_value: str) -> Optional[str]:
        """Get gem type for a fake placeholder."""
        mapping = self.mappings.get(fake_value)
        return mapping.gem_type if mapping else None

    def get_all_fakes(self) -> List[str]:
        """Get all fake values in this session."""
        return list(self.mappings.keys())

    def clear(self) -> None:
        """Clear all mappings."""
        self.mappings.clear()


class SessionManager:
    """
    Manages gem mappings across multi-turn conversations.

    Thread-safe session management with TTL support.
    """

    DEFAULT_TTL: int = 3600  # 1 hour default TTL

    def __init__(self, default_ttl: int = DEFAULT_TTL):
        """
        Initialize SessionManager.

        Args:
            default_ttl: Default time-to-live for sessions in seconds (default: 3600)
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session.

        Args:
            session_id: Optional custom session ID. If not provided, a UUID is generated.

        Returns:
            The session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        with self._lock:
            self._sessions[session_id] = Session(session_id=session_id)
            return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Session object if found, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_accessed = time.time()
            return session

    def add_mappings(
        self,
        session_id: str,
        mappings: Dict[str, str],
        gem_type: str = "general",
    ) -> bool:
        """
        Add multiple gem mappings to a session.

        Args:
            session_id: The session ID
            mappings: Dict of fake_value -> original_value
            gem_type: Type of gems (e.g., "email", "phone")

        Returns:
            True if session exists and mappings added, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            for fake_value, original_value in mappings.items():
                session.add_mapping(fake_value, original_value, gem_type)
            return True

    def add_mapping(
        self,
        session_id: str,
        fake_value: str,
        original_value: str,
        gem_type: str = "general",
    ) -> bool:
        """
        Add a single gem mapping to a session.

        Args:
            session_id: The session ID
            fake_value: The fake placeholder value
            original_value: The original gem value
            gem_type: Type of gem

        Returns:
            True if session exists and mapping added, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            session.add_mapping(fake_value, original_value, gem_type)
            return True

    def get_original(self, session_id: str, fake_value: str) -> Optional[str]:
        """
        Get the original value for a fake placeholder.

        Args:
            session_id: The session ID
            fake_value: The fake placeholder value

        Returns:
            Original value if found, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            return session.get_original(fake_value)

    def get_gem_type(self, session_id: str, fake_value: str) -> Optional[str]:
        """
        Get the gem type for a fake placeholder.

        Args:
            session_id: The session ID
            fake_value: The fake placeholder value

        Returns:
            Gem type if found, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            return session.get_gem_type(fake_value)

    def get_all_fakes(self, session_id: str) -> List[str]:
        """
        Get all fake values in a session.

        Args:
            session_id: The session ID

        Returns:
            List of fake values
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            return session.get_all_fakes()

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all mappings for a session.

        Args:
            session_id: The session ID

        Returns:
            True if session existed, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.clear()
            return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session entirely.

        Args:
            session_id: The session ID

        Returns:
            True if session existed, False otherwise
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def get_active_sessions(self) -> List[str]:
        """
        Get all active session IDs.

        Returns:
            List of session IDs
        """
        with self._lock:
            return list(self._sessions.keys())

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        with self._lock:
            return len(self._sessions)

    def cleanup_expired(self, ttl: Optional[int] = None) -> int:
        """
        Remove expired sessions.

        Args:
            ttl: Time-to-live in seconds. Uses default if not provided.

        Returns:
            Number of sessions removed
        """
        if ttl is None:
            ttl = self._default_ttl

        current_time = time.time()
        removed = 0

        with self._lock:
            expired_ids = [
                sid
                for sid, session in self._sessions.items()
                if current_time - session.last_accessed > ttl
            ]
            for sid in expired_ids:
                del self._sessions[sid]
                removed += 1

        return removed

    def start_auto_cleanup(self, interval: int = 300) -> None:
        """
        Start automatic cleanup of expired sessions.

        Args:
            interval: Cleanup interval in seconds (default: 300 = 5 minutes)
        """
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(
            target=self._auto_cleanup_loop,
            args=(interval,),
            daemon=True,
        )
        self._cleanup_thread.start()

    def stop_auto_cleanup(self) -> None:
        """Stop automatic cleanup."""
        self._stop_cleanup.set()
        if self._cleanup_thread is not None:
            self._cleanup_thread.join(timeout=5)
            self._cleanup_thread = None

    def _auto_cleanup_loop(self, interval: int) -> None:
        """Internal auto cleanup loop."""
        while not self._stop_cleanup.wait(interval):
            self.cleanup_expired()

    def get_stats(self) -> Dict:
        """Get session statistics."""
        with self._lock:
            total_mappings = sum(len(s.mappings) for s in self._sessions.values())
            return {
                "session_count": len(self._sessions),
                "total_mappings": total_mappings,
                "sessions": [
                    {
                        "session_id": sid,
                        "mapping_count": len(s.mappings),
                        "created_at": s.created_at,
                        "last_accessed": s.last_accessed,
                    }
                    for sid, s in self._sessions.items()
                ],
            }


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global SessionManager instance."""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


def set_session_manager(manager: SessionManager) -> None:
    """Set the global SessionManager instance."""
    global _global_session_manager
    _global_session_manager = manager
