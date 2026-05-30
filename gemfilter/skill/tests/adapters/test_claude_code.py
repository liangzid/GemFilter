"""
Unit tests for ClaudeCodeAdapter.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from gemfilter.skill.adapters.claude_code import ClaudeCodeAdapter, ClaudeCodeSettings


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        adapter = ClaudeCodeAdapter()

        assert adapter.name == "claude_code"
        assert adapter._settings_path == ClaudeCodeAdapter.SETTINGS_FILE

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        adapter = ClaudeCodeAdapter(settings_path="/custom/path.json")

        assert adapter._settings_path == "/custom/path.json"

    def test_supported_capabilities(self):
        """Test supported capabilities."""
        adapter = ClaudeCodeAdapter()

        caps = adapter.supported_capabilities
        from gemfilter.skill.adapters.base import AdapterCapability

        assert AdapterCapability.PRE_SEND_HOOK in caps
        assert AdapterCapability.POST_RECEIVE_HOOK in caps
        assert AdapterCapability.NOTIFICATION in caps

    def test_get_hook_paths(self):
        """Test getting hook paths."""
        adapter = ClaudeCodeAdapter()
        paths = adapter.get_hook_paths()

        assert "onBeforeSend" in paths
        assert "onAfterReceive" in paths
        assert "onToolOutput" in paths
        assert "gemfilter.skill.hooks.pre_send_hook" in paths["onBeforeSend"]

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_load_settings_not_exists(self, mock_json_load, mock_open, mock_exists):
        """Test loading settings when file doesn't exist."""
        mock_exists.return_value = False

        adapter = ClaudeCodeAdapter()
        settings = adapter._load_settings()

        assert settings == {"hooks": {}}

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_load_settings_exists(self, mock_json_load, mock_open, mock_exists):
        """Test loading settings when file exists."""
        mock_exists.return_value = True
        mock_json_load.return_value = {"hooks": {"test": "value"}}

        adapter = ClaudeCodeAdapter()
        settings = adapter._load_settings()

        assert settings["hooks"]["test"] == "value"

    @patch("pathlib.Path.exists")
    def test_install_success(self, mock_exists):
        """Test successful installation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text("{}")

            adapter = ClaudeCodeAdapter(settings_path=str(settings_path))
            result = adapter.install()

            assert result is True

            # Verify hooks were added
            settings = json.loads(settings_path.read_text())
            assert "hooks" in settings
            assert "onBeforeSend" in settings["hooks"]
            assert settings["hooks"]["onToolOutput"] == "gemfilter.skill.hooks.tool_output_hook"

    @patch("pathlib.Path.exists")
    def test_uninstall_success(self, mock_exists):
        """Test successful uninstallation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps({
                "hooks": {
                    "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
                    "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook",
                    "onToolOutput": "gemfilter.skill.hooks.tool_output_hook",
                }
            }))

            adapter = ClaudeCodeAdapter(settings_path=str(settings_path))
            result = adapter.uninstall()

            assert result is True

            settings = json.loads(settings_path.read_text())
            assert "onBeforeSend" not in settings.get("hooks", {})

    def test_display_notification(self):
        """Test display notification."""
        adapter = ClaudeCodeAdapter()

        # Should not raise
        adapter.display_notification("Test message", 3)

    def test_get_conversation_id_no_env(self):
        """Test get conversation ID when not set."""
        adapter = ClaudeCodeAdapter()

        with patch.dict("os.environ", {}, clear=True):
            conv_id = adapter.get_conversation_id()

        # Should return None or from .claude/.session
        # Just verify it doesn't raise
        assert conv_id is None or isinstance(conv_id, str)

    def test_validate_installation_not_installed(self):
        """Test validation when not installed."""
        adapter = ClaudeCodeAdapter(settings_path="/nonexistent/path.json")

        result = adapter.validate_installation()

        assert result is False

    def test_validate_installation_installed(self):
        """Test validation when installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps({
                "hooks": {
                    "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
                    "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook",
                    "onToolOutput": "gemfilter.skill.hooks.tool_output_hook",
                }
            }))

            adapter = ClaudeCodeAdapter(settings_path=str(settings_path))
            result = adapter.validate_installation()

            assert result is True

    def test_enable_hooks(self):
        """Test enable hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps({
                "hooks": {
                    "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
                    "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook",
                    "onToolOutput": "gemfilter.skill.hooks.tool_output_hook",
                }
            }))

            adapter = ClaudeCodeAdapter(settings_path=str(settings_path))
            result = adapter.enable_hooks()

            assert result is True

    def test_disable_hooks(self):
        """Test disable hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps({
                "hooks": {
                    "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
                    "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook",
                    "onToolOutput": "gemfilter.skill.hooks.tool_output_hook",
                }
            }))

            adapter = ClaudeCodeAdapter(settings_path=str(settings_path))
            result = adapter.disable_hooks()

            assert result is True

            # Verify hooks are set to None
            settings = json.loads(settings_path.read_text())
            assert settings["hooks"]["onBeforeSend"] is None
            assert settings["hooks"]["onToolOutput"] is None


class TestClaudeCodeSettings:
    """Tests for ClaudeCodeSettings helper class."""

    def test_load_no_file(self):
        """Test loading when file doesn't exist."""
        settings = ClaudeCodeSettings("/nonexistent/path.json")
        result = settings.load()

        assert result == {}

    def test_save_creates_directory(self):
        """Test save creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "subdir" / "settings.json"
            settings = ClaudeCodeSettings(str(save_path))

            settings.save({"hooks": {}})

            assert save_path.exists()

    def test_get_hooks_empty(self):
        """Test getting hooks when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text("{}")

            settings = ClaudeCodeSettings(str(settings_path))
            settings.load()
            hooks = settings.get_hooks()

            assert hooks == {}

    def test_set_hook(self):
        """Test setting a hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text("{}")

            settings = ClaudeCodeSettings(str(settings_path))
            settings.load()
            settings.set_hook("onBeforeSend", "module.func")

            hooks = settings.get_hooks()
            assert hooks["onBeforeSend"] == "module.func"

    def test_remove_hook(self):
        """Test removing a hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            settings_path.write_text(json.dumps({
                "hooks": {"onBeforeSend": "module.func"}
            }))

            settings = ClaudeCodeSettings(str(settings_path))
            settings.load()
            settings.remove_hook("onBeforeSend")

            hooks = settings.get_hooks()
            assert "onBeforeSend" not in hooks
