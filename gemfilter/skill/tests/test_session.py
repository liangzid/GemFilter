"""
Unit tests for SessionManager.
"""

import pytest
import threading
import time
from gemfilter.skill.session import SessionManager, Session, GemMapping, get_session_manager, set_session_manager


class TestSession:
    """Tests for Session dataclass."""

    def test_create_session(self):
        """Test session creation."""
        session = Session(session_id="test-123")
        assert session.session_id == "test-123"
        assert len(session.mappings) == 0

    def test_add_mapping(self):
        """Test adding a gem mapping."""
        session = Session(session_id="test-123")
        session.add_mapping("fake@example.com", "real@example.com", "email")

        assert "fake@example.com" in session.mappings
        mapping = session.mappings["fake@example.com"]
        assert mapping.original_value == "real@example.com"
        assert mapping.gem_type == "email"

    def test_get_original(self):
        """Test retrieving original value."""
        session = Session(session_id="test-123")
        session.add_mapping("fake@example.com", "real@example.com", "email")

        assert session.get_original("fake@example.com") == "real@example.com"
        assert session.get_original("nonexistent") is None

    def test_get_gem_type(self):
        """Test retrieving gem type."""
        session = Session(session_id="test-123")
        session.add_mapping("fake@example.com", "real@example.com", "email")

        assert session.get_gem_type("fake@example.com") == "email"
        assert session.get_gem_type("nonexistent") is None

    def test_clear(self):
        """Test clearing mappings."""
        session = Session(session_id="test-123")
        session.add_mapping("fake1@example.com", "real1@example.com", "email")
        session.add_mapping("fake2@example.com", "real2@example.com", "email")

        session.clear()
        assert len(session.mappings) == 0


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_create_session_with_id(self):
        """Test creating session with custom ID."""
        manager = SessionManager()
        session_id = manager.create_session("custom-id")
        assert session_id == "custom-id"

    def test_create_session_auto_id(self):
        """Test creating session with auto-generated ID."""
        manager = SessionManager()
        session_id = manager.create_session()
        assert session_id is not None
        assert len(session_id) > 0

    def test_get_session(self):
        """Test retrieving session."""
        manager = SessionManager()
        session_id = manager.create_session("test-session")

        session = manager.get_session("test-session")
        assert session is not None
        assert session.session_id == "test-session"

    def test_get_session_nonexistent(self):
        """Test retrieving nonexistent session."""
        manager = SessionManager()
        session = manager.get_session("nonexistent")
        assert session is None

    def test_add_mappings(self):
        """Test adding multiple mappings."""
        manager = SessionManager()
        session_id = manager.create_session("test")

        mappings = {
            "fake1@example.com": "real1@example.com",
            "fake2@example.com": "real2@example.com",
        }
        result = manager.add_mappings(session_id, mappings, "email")

        assert result is True
        assert len(manager.get_session(session_id).mappings) == 2

    def test_add_mappings_session_not_found(self):
        """Test adding mappings to nonexistent session."""
        manager = SessionManager()
        result = manager.add_mappings("nonexistent", {"fake": "real"}, "email")
        assert result is False

    def test_add_mapping(self):
        """Test adding single mapping."""
        manager = SessionManager()
        session_id = manager.create_session("test")

        result = manager.add_mapping(session_id, "fake@test.com", "real@test.com", "email")
        assert result is True

        session = manager.get_session(session_id)
        assert session.get_original("fake@test.com") == "real@test.com"

    def test_get_original(self):
        """Test getting original value."""
        manager = SessionManager()
        session_id = manager.create_session("test")
        manager.add_mapping(session_id, "fake@test.com", "real@test.com", "email")

        original = manager.get_original(session_id, "fake@test.com")
        assert original == "real@test.com"

    def test_get_original_not_found(self):
        """Test getting original for nonexistent fake."""
        manager = SessionManager()
        session_id = manager.create_session("test")

        original = manager.get_original(session_id, "nonexistent")
        assert original is None

    def test_clear_session(self):
        """Test clearing session."""
        manager = SessionManager()
        session_id = manager.create_session("test")
        manager.add_mapping(session_id, "fake@test.com", "real@test.com", "email")

        result = manager.clear_session(session_id)
        assert result is True
        assert len(manager.get_session(session_id).mappings) == 0

    def test_delete_session(self):
        """Test deleting session."""
        manager = SessionManager()
        session_id = manager.create_session("test")

        result = manager.delete_session(session_id)
        assert result is True
        assert manager.get_session(session_id) is None

    def test_get_active_sessions(self):
        """Test getting active sessions."""
        manager = SessionManager()
        manager.create_session("s1")
        manager.create_session("s2")
        manager.create_session("s3")

        sessions = manager.get_active_sessions()
        assert len(sessions) == 3
        assert "s1" in sessions
        assert "s2" in sessions
        assert "s3" in sessions

    def test_get_session_count(self):
        """Test getting session count."""
        manager = SessionManager()
        assert manager.get_session_count() == 0

        manager.create_session("s1")
        manager.create_session("s2")
        assert manager.get_session_count() == 2

    def test_cleanup_expired(self):
        """Test cleaning up expired sessions."""
        manager = SessionManager(default_ttl=1)  # 1 second TTL
        session_id = manager.create_session("test")

        # Wait for expiration
        time.sleep(1.5)

        removed = manager.cleanup_expired()
        assert removed == 1
        assert manager.get_session(session_id) is None

    def test_concurrent_access(self):
        """Test concurrent session access."""
        manager = SessionManager()
        errors = []

        def worker(session_id, i):
            try:
                manager.add_mapping(session_id, f"fake{i}@test.com", f"real{i}@test.com", "email")
                manager.get_original(session_id, f"fake{i}@test.com")
            except Exception as e:
                errors.append(e)

        session_id = manager.create_session("concurrent-test")
        threads = [threading.Thread(target=worker, args=(session_id, i)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_auto_cleanup(self):
        """Test auto cleanup feature."""
        manager = SessionManager(default_ttl=1)
        manager.create_session("test")

        manager.start_auto_cleanup(interval=1)
        time.sleep(2.5)

        manager.stop_auto_cleanup()
        assert manager.get_session_count() == 0


class TestGlobalSessionManager:
    """Tests for global session manager."""

    def setup_method(self):
        """Reset global manager before each test."""
        set_session_manager(None)

    def test_get_session_manager(self):
        """Test getting global session manager."""
        manager = get_session_manager()
        assert manager is not None
        assert isinstance(manager, SessionManager)

    def test_set_session_manager(self):
        """Test setting global session manager."""
        custom_manager = SessionManager()
        set_session_manager(custom_manager)

        retrieved = get_session_manager()
        assert retrieved is custom_manager


class TestGemMapping:
    """Tests for GemMapping dataclass."""

    def test_create_mapping(self):
        """Test creating a gem mapping."""
        mapping = GemMapping(
            fake_value="fake@test.com",
            original_value="real@test.com",
            gem_type="email"
        )

        assert mapping.fake_value == "fake@test.com"
        assert mapping.original_value == "real@test.com"
        assert mapping.gem_type == "email"
        assert mapping.created_at > 0
