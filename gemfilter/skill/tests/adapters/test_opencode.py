"""
Unit tests for OpenCodeAdapter.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from gemfilter.skill.adapters.opencode import OpenCodeAdapter, OpenCodePlugin


class TestOpenCodeAdapter:
    """Tests for OpenCodeAdapter class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        adapter = OpenCodeAdapter()

        assert adapter.name == "opencode"
        assert adapter._config_path == OpenCodeAdapter.CONFIG_FILE

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        adapter = OpenCodeAdapter(config_path="/custom/path.json")

        assert adapter._config_path == "/custom/path.json"

    def test_supported_capabilities(self):
        """Test supported capabilities."""
        adapter = OpenCodeAdapter()

        caps = adapter.supported_capabilities
        from gemfilter.skill.adapters.base import AdapterCapability

        assert AdapterCapability.PRE_SEND_HOOK in caps
        assert AdapterCapability.POST_RECEIVE_HOOK in caps
        assert AdapterCapability.TOOL_HOOK in caps
        assert AdapterCapability.NOTIFICATION in caps

    def test_get_hook_paths(self):
        """Test getting hook paths."""
        adapter = OpenCodeAdapter()
        paths = adapter.get_hook_paths()

        assert "pre_send" in paths
        assert "post_receive" in paths
        assert "tool_output" in paths
        assert "gemfilter.skill.hooks.pre_send_hook" in paths["pre_send"]

    @patch("pathlib.Path.exists")
    def test_install_success(self, mock_exists):
        """Test successful installation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")

            adapter = OpenCodeAdapter(config_path=str(config_path))
            result = adapter.install()

            assert result is True

            config = json.loads(config_path.read_text())
            assert "plugins" in config
            assert OpenCodeAdapter.PLUGIN_NAME in config["plugins"]
            hooks = config["plugins"][OpenCodeAdapter.PLUGIN_NAME]["hooks"]
            assert hooks["tool_output"] == "gemfilter.skill.hooks.tool_output_hook"

    @patch("pathlib.Path.exists")
    def test_uninstall_success(self, mock_exists):
        """Test successful uninstallation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({
                "plugins": {
                    OpenCodeAdapter.PLUGIN_NAME: {
                        "enabled": True,
                        "hooks": {}
                    }
                }
            }))

            adapter = OpenCodeAdapter(config_path=str(config_path))
            result = adapter.uninstall()

            assert result is True

            config = json.loads(config_path.read_text())
            assert OpenCodeAdapter.PLUGIN_NAME not in config.get("plugins", {})

    def test_display_notification(self):
        """Test display notification."""
        adapter = OpenCodeAdapter()

        # Should not raise
        adapter.display_notification("Test message", 3)

    def test_get_conversation_id(self):
        """Test get conversation ID."""
        adapter = OpenCodeAdapter()

        # Should not raise, may return None
        conv_id = adapter.get_conversation_id()
        assert conv_id is None or isinstance(conv_id, str)

    def test_validate_installation_not_installed(self):
        """Test validation when not installed."""
        adapter = OpenCodeAdapter(config_path="/nonexistent/path.json")

        result = adapter.validate_installation()

        assert result is False

    def test_validate_installation_installed(self):
        """Test validation when installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({
                "plugins": {
                    OpenCodeAdapter.PLUGIN_NAME: {
                        "enabled": True,
                        "hooks": {}
                    }
                }
            }))

            adapter = OpenCodeAdapter(config_path=str(config_path))
            result = adapter.validate_installation()

            assert result is True


class TestOpenCodePlugin:
    """Tests for OpenCodePlugin class."""

    def test_get_manifest(self):
        """Test getting plugin manifest."""
        manifest = OpenCodePlugin.get_manifest()

        assert manifest["name"] == "gemfilter"
        assert "version" in manifest
        assert "hooks" in manifest
        assert "tool_output" in manifest["hooks"]

    def test_write_manifest(self):
        """Test writing plugin manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "gemfilter" / "manifest.json"

            OpenCodePlugin.write_manifest(str(manifest_path.parent))

            assert manifest_path.exists()

            manifest = json.loads(manifest_path.read_text())
            assert manifest["name"] == "gemfilter"
