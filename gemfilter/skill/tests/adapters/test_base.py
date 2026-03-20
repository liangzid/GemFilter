"""
Unit tests for base AgentAdapter.
"""

import pytest
from gemfilter.skill.adapters.base import (
    AgentAdapter,
    AdapterCapability,
    AdapterConfig,
    HookPayload,
    create_adapter,
)


class TestAdapterConfig:
    """Tests for AdapterConfig dataclass."""

    def test_default_values(self):
        """Test default adapter config."""
        config = AdapterConfig()

        assert config.enabled is True
        assert config.hooks == {}
        assert config.custom_settings == {}

    def test_custom_values(self):
        """Test custom adapter config."""
        config = AdapterConfig(
            enabled=False,
            hooks={"pre_send": "module.func"},
            custom_settings={"timeout": 30},
        )

        assert config.enabled is False
        assert config.hooks["pre_send"] == "module.func"
        assert config.custom_settings["timeout"] == 30


class TestAgentAdapter:
    """Tests for AgentAdapter base class."""

    def test_is_capable(self):
        """Test checking adapter capabilities."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return [AdapterCapability.PRE_SEND_HOOK]

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        adapter = TestAdapter()

        assert adapter.is_capable(AdapterCapability.PRE_SEND_HOOK) is True
        assert adapter.is_capable(AdapterCapability.POST_RECEIVE_HOOK) is False

    def test_register_hooks(self):
        """Test registering hook handlers."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return [AdapterCapability.PRE_SEND_HOOK, AdapterCapability.POST_RECEIVE_HOOK]

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        adapter = TestAdapter()
        pre_handler = lambda x: x
        post_handler = lambda x: x

        adapter.register_hooks(pre_send=pre_handler, post_receive=post_handler)

        assert adapter._pre_send_handler is pre_handler
        assert adapter._post_receive_handler is post_handler

    def test_unregister_hooks(self):
        """Test unregistering hooks."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return [AdapterCapability.PRE_SEND_HOOK]

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        adapter = TestAdapter()
        adapter._pre_send_handler = lambda x: x

        adapter.unregister_hooks()

        assert adapter._pre_send_handler is None

    def test_pre_send_no_handler(self):
        """Test pre_send with no handler."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return []

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        adapter = TestAdapter()
        result = adapter.pre_send("test payload")

        assert result == "test payload"

    def test_post_receive_no_handler(self):
        """Test post_receive with no handler."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return []

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        adapter = TestAdapter()
        result = adapter.post_receive("test payload")

        assert result == "test payload"

    def test_get_hook_paths(self):
        """Test getting hook paths."""
        class TestAdapter(AgentAdapter):
            @property
            def name(self) -> str:
                return "test"

            @property
            def supported_capabilities(self):
                return []

            def install(self) -> bool:
                return True

            def uninstall(self) -> bool:
                return True

            def get_conversation_id(self):
                return None

            def display_notification(self, message: str, gem_count: int):
                pass

        config = AdapterConfig(hooks={"pre_send": "module.func"})
        adapter = TestAdapter(config)

        paths = adapter.get_hook_paths()

        assert paths["pre_send"] == "module.func"


class TestHookPayload:
    """Tests for HookPayload class."""

    def test_create_empty(self):
        """Test creating empty payload."""
        payload = HookPayload()

        assert payload.text is None
        assert payload.session_id is None
        assert payload.metadata == {}

    def test_create_with_values(self):
        """Test creating payload with values."""
        payload = HookPayload(
            text="Hello",
            session_id="sess-123",
            metadata={"key": "value"},
        )

        assert payload.text == "Hello"
        assert payload.session_id == "sess-123"
        assert payload.metadata["key"] == "value"

    def test_has_text_true(self):
        """Test has_text returns True."""
        payload = HookPayload(text="Hello")
        assert payload.has_text() is True

    def test_has_text_false_empty(self):
        """Test has_text returns False for empty text."""
        payload = HookPayload(text="")
        assert payload.has_text() is False

    def test_has_text_false_none(self):
        """Test has_text returns False for None."""
        payload = HookPayload(text=None)
        assert payload.has_text() is False

    def test_to_dict(self):
        """Test converting to dict."""
        payload = HookPayload(text="Hello", session_id="sess-123")
        data = payload.to_dict()

        assert data["text"] == "Hello"
        assert data["session_id"] == "sess-123"

    def test_from_string(self):
        """Test creating from string."""
        payload = HookPayload.from_any("Hello")

        assert isinstance(payload, HookPayload)
        assert payload.text == "Hello"
        assert payload.raw_payload == "Hello"

    def test_from_dict(self):
        """Test creating from dict."""
        data = {"text": "Hello", "session_id": "sess-123", "extra": 123}
        payload = HookPayload.from_any(data)

        assert payload.text == "Hello"
        assert payload.session_id == "sess-123"
        assert payload.metadata["extra"] == 123

    def test_from_hook_payload(self):
        """Test creating from HookPayload."""
        original = HookPayload(text="Hello", session_id="sess")
        payload = HookPayload.from_any(original)

        assert payload is original

    def test_from_other_type(self):
        """Test creating from other types."""
        payload = HookPayload.from_any(123)

        assert payload.text == "123"


class TestCreateAdapter:
    """Tests for create_adapter factory function."""

    def test_create_claude_code_adapter(self):
        """Test creating Claude Code adapter."""
        from gemfilter.skill.adapters.claude_code import ClaudeCodeAdapter

        adapter = create_adapter("claude_code")

        assert isinstance(adapter, ClaudeCodeAdapter)
        assert adapter.name == "claude_code"

    def test_create_opencode_adapter(self):
        """Test creating OpenCode adapter."""
        from gemfilter.skill.adapters.opencode import OpenCodeAdapter

        adapter = create_adapter("opencode")

        assert isinstance(adapter, OpenCodeAdapter)
        assert adapter.name == "opencode"

    def test_create_coodex_adapter(self):
        """Test creating Codex adapter."""
        from gemfilter.skill.adapters.coodex import CodexAdapter

        adapter = create_adapter("coodex")

        assert isinstance(adapter, CodexAdapter)
        assert adapter.name == "coodex"

    def test_create_unknown_adapter(self):
        """Test creating unknown adapter raises error."""
        with pytest.raises(ValueError) as exc_info:
            create_adapter("unknown_agent")

        assert "Unknown agent type" in str(exc_info.value)

    def test_create_adapter_case_insensitive(self):
        """Test creating adapter is case insensitive."""
        from gemfilter.skill.adapters.claude_code import ClaudeCodeAdapter

        adapter = create_adapter("Claude_Code")

        assert isinstance(adapter, ClaudeCodeAdapter)
