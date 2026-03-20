"""
Unit tests for HookManager and hooks.
"""

import pytest
from unittest.mock import MagicMock, patch

from gemfilter.skill.hooks import (
    HookManager,
    HookResult,
    pre_send_hook,
    post_receive_hook,
    get_hook_manager,
    set_hook_manager,
    filter_text,
    sanitize_response,
)
from gemfilter.skill.session import SessionManager
from gemfilter.skill.masker import GemMasker
from gemfilter.skill.unmasker import GemUnmasker
from gemfilter.skill.ui import UINotifier, NotificationStyle


class TestHookResult:
    """Tests for HookResult dataclass."""

    def test_create_result(self):
        """Test creating a hook result."""
        result = HookResult(
            success=True,
            payload="test payload",
            gems_detected=2,
            notification="🔒 2 gems protected",
        )

        assert result.success is True
        assert result.payload == "test payload"
        assert result.gems_detected == 2
        assert result.notification == "🔒 2 gems protected"
        assert result.error is None

    def test_create_result_with_error(self):
        """Test creating a hook result with error."""
        result = HookResult(
            success=False,
            payload="test payload",
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"


class TestHookManager:
    """Tests for HookManager class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        manager = HookManager()

        assert manager._session_manager is not None
        assert manager._masker is not None
        assert manager._unmasker is not None
        assert manager._notifier is not None
        assert manager._config is not None

    def test_init_custom(self):
        """Test initialization with custom components."""
        session_mgr = SessionManager()
        masker = GemMasker()
        unmasker = GemUnmasker()
        notifier = UINotifier()

        manager = HookManager(
            session_manager=session_mgr,
            masker=masker,
            unmasker=unmasker,
            notifier=notifier,
        )

        assert manager._session_manager is session_mgr
        assert manager._masker is masker
        assert manager._unmasker is unmasker
        assert manager._notifier is notifier

    def test_pre_send_no_gems(self):
        """Test pre_send with no gems."""
        manager = HookManager()
        result = manager.pre_send("Hello world")

        assert result.success is True
        assert result.gems_detected == 0
        assert result.payload == "Hello world"

    def test_pre_send_with_gems(self):
        """Test pre_send with gems."""
        manager = HookManager()
        result = manager.pre_send("Contact: test@example.com")

        assert result.success is True
        assert result.gems_detected >= 1
        assert "test@example.com" not in result.payload
        assert result.notification is not None
        assert "🔒" in result.notification

    def test_pre_send_with_session_id(self):
        """Test pre_send with explicit session ID."""
        manager = HookManager()
        result = manager.pre_send("Email: test@example.com", session_id="my-session")

        assert result.success is True
        assert "my-session" in manager._active_sessions

    def test_pre_send_dict_payload(self):
        """Test pre_send with dict payload."""
        manager = HookManager()
        payload = {"text": "Contact: test@example.com", "user": "john"}

        result = manager.pre_send(payload)

        assert result.success is True
        assert isinstance(result.payload, dict)
        assert result.payload["user"] == "john"

    def test_pre_send_multiple_gems(self):
        """Test pre_send with multiple gems."""
        manager = HookManager()
        text = "Email: test@example.com, Phone: 13912345678"

        result = manager.pre_send(text)

        assert result.success is True
        assert result.gems_detected >= 2

    def test_post_receive_no_session(self):
        """Test post_receive with no active session."""
        manager = HookManager()
        result = manager.post_receive("Hello world")

        assert result.success is True
        assert result.payload == "Hello world"

    def test_post_receive_with_fakes(self):
        """Test post_receive with fake placeholders."""
        manager = HookManager()

        # First mask some text
        pre_result = manager.pre_send("Email: test@example.com")
        session_id = list(manager._active_sessions.keys())[0]

        # Now receive a response with fakes
        response = "I see your email is t***@example.com_ema"
        result = manager.post_receive(response, session_id)

        assert result.success is True
        assert "[FILTERED]" in result.payload

    def test_post_receive_cleans_session(self):
        """Test post_receive cleans up session."""
        manager = HookManager()

        pre_result = manager.pre_send("Email: test@example.com")
        session_id = list(manager._active_sessions.keys())[0]

        result = manager.post_receive("Response", session_id)

        assert session_id not in manager._active_sessions

    def test_post_receive_with_error(self):
        """Test post_receive handles errors gracefully."""
        manager = HookManager()
        result = manager.post_receive("Some text")

        # Should not raise, should return success even without session
        assert result.success is True

    def test_extract_text_from_string(self):
        """Test extracting text from string payload."""
        manager = HookManager()
        text, is_dict, fields = manager._extract_text("Hello")

        assert text == "Hello"
        assert is_dict is False
        assert fields == []

    def test_extract_text_from_dict(self):
        """Test extracting text from dict payload."""
        manager = HookManager()
        text, is_dict, fields = manager._extract_text({"text": "Hello", "extra": 123})

        assert text == "Hello"
        assert is_dict is True
        assert "text" in fields

    def test_extract_text_from_dict_content_field(self):
        """Test extracting text from dict with content field."""
        manager = HookManager()
        text, is_dict, fields = manager._extract_text({"content": "Hello world"})

        assert text == "Hello world"
        assert is_dict is True

    def test_extract_text_from_dict_message_field(self):
        """Test extracting text from dict with message field."""
        manager = HookManager()
        text, is_dict, fields = manager._extract_text({"message": "Hello world"})

        assert text == "Hello world"
        assert is_dict is True

    def test_extract_text_from_other(self):
        """Test extracting text from other types."""
        manager = HookManager()
        text, is_dict, fields = manager._extract_text(123)

        assert text == "123"
        assert is_dict is False

    def test_reconstruct_payload_string(self):
        """Test reconstructing string payload."""
        manager = HookManager()
        result = manager._reconstruct_payload("original", "modified", False, [])

        assert result == "modified"

    def test_reconstruct_payload_dict(self):
        """Test reconstructing dict payload."""
        manager = HookManager()
        original = {"text": "old", "extra": "keep"}
        result = manager._reconstruct_payload(original, "new", True, ["text"])

        assert result["text"] == "new"
        assert result["extra"] == "keep"

    def test_register_with_agent(self):
        """Test registering hooks with agent adapter."""
        manager = HookManager()
        adapter = MagicMock()

        manager.register_with_agent(adapter)

        adapter.register_hooks.assert_called_once()


class TestStandaloneHookFunctions:
    """Tests for standalone hook functions."""

    def setup_method(self):
        """Reset global hook manager."""
        set_hook_manager(None)

    def test_pre_send_hook(self):
        """Test pre_send_hook function."""
        result = pre_send_hook("Contact: test@example.com")

        assert result.success is True
        assert result.gems_detected >= 1

    def test_post_receive_hook_no_session(self):
        """Test post_receive_hook without session."""
        result = post_receive_hook("Hello world")

        assert result.success is True

    def test_filter_text(self):
        """Test filter_text function."""
        masked, mapping, notification = filter_text("Contact: test@example.com")

        assert "test@example.com" not in masked
        assert "🔒" in notification

    def test_sanitize_response(self):
        """Test sanitize_response function."""
        sanitized, notification = sanitize_response("Email: t***@example.com_ema", "test")

        assert "[FILTERED]" in sanitized


class TestHookManagerEdgeCases:
    """Edge case tests for HookManager."""

    def test_pre_send_empty_string(self):
        """Test pre_send with empty string."""
        manager = HookManager()
        result = manager.pre_send("")

        assert result.success is True
        assert result.gems_detected == 0

    def test_pre_send_very_long_text(self):
        """Test pre_send with very long text."""
        manager = HookManager()
        # Create text with gems spread throughout
        gem = "test@example.com"
        text = (gem + ", ") * 100

        result = manager.pre_send(text)

        assert result.success is True
        assert result.gems_detected >= 100

    def test_pre_send_special_characters(self):
        """Test pre_send with special characters."""
        manager = HookManager()
        text = "Email: test@example.com\nPhone: 13912345678\tAPI: sk-key123"

        result = manager.pre_send(text)

        assert result.success is True

    def test_multiple_pre_send_same_session(self):
        """Test multiple pre_sends in same session."""
        manager = HookManager()
        session_id = manager._session_manager.create_session("test")

        result1 = manager.pre_send("Email: a@b.com", session_id)
        result2 = manager.pre_send("Phone: 13912345678", session_id)

        assert result1.success is True
        assert result2.success is True

    def test_post_receive_empty_string(self):
        """Test post_receive with empty string."""
        manager = HookManager()
        result = manager.post_receive("")

        assert result.success is True

    def test_config_property(self):
        """Test config property."""
        manager = HookManager()

        assert manager.config is not None
        assert manager.config.name == "gemfilter"

    def test_masker_property(self):
        """Test masker property."""
        manager = HookManager()

        assert manager.masker is not None
        assert isinstance(manager.masker, GemMasker)

    def test_unmasker_property(self):
        """Test unmasker property."""
        manager = HookManager()

        assert manager.unmasker is not None
        assert isinstance(manager.unmasker, GemUnmasker)

    def test_session_manager_property(self):
        """Test session_manager property."""
        manager = HookManager()

        assert manager.session_manager is not None
        assert isinstance(manager.session_manager, SessionManager)


class TestGlobalHookManager:
    """Tests for global hook manager."""

    def setup_method(self):
        """Reset global manager."""
        set_hook_manager(None)

    def test_get_hook_manager(self):
        """Test getting global hook manager."""
        manager = get_hook_manager()

        assert manager is not None
        assert isinstance(manager, HookManager)

    def test_set_hook_manager(self):
        """Test setting global hook manager."""
        custom = HookManager()
        set_hook_manager(custom)

        retrieved = get_hook_manager()

        assert retrieved is custom
