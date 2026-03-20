"""
Unit tests for CodexAdapter.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from gemfilter.skill.adapters.coodex import CodexAdapter, MCPTool


class TestCodexAdapter:
    """Tests for CodexAdapter class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        adapter = CodexAdapter()

        assert adapter.name == "coodex"
        assert adapter._config_path == CodexAdapter.MCP_CONFIG_FILE

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        adapter = CodexAdapter(config_path="/custom/path.json")

        assert adapter._config_path == "/custom/path.json"

    def test_supported_capabilities(self):
        """Test supported capabilities."""
        adapter = CodexAdapter()

        caps = adapter.supported_capabilities
        from gemfilter.skill.adapters.base import AdapterCapability

        assert AdapterCapability.PRE_SEND_HOOK in caps
        assert AdapterCapability.POST_RECEIVE_HOOK in caps
        assert AdapterCapability.TOOL_HOOK in caps
        assert AdapterCapability.NOTIFICATION in caps

    def test_get_hook_paths(self):
        """Test getting hook paths."""
        adapter = CodexAdapter()
        paths = adapter.get_hook_paths()

        assert "filter" in paths
        assert "restore" in paths

    @patch("pathlib.Path.exists")
    def test_install_success(self, mock_exists):
        """Test successful installation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp_config.json"
            config_path.write_text("{}")

            adapter = CodexAdapter(config_path=str(config_path))
            result = adapter.install()

            assert result is True

            config = json.loads(config_path.read_text())
            assert "tools" in config
            assert "gemfilter" in config["tools"]

    @patch("pathlib.Path.exists")
    def test_uninstall_success(self, mock_exists):
        """Test successful uninstallation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp_config.json"
            config_path.write_text(json.dumps({
                "tools": {
                    "gemfilter": {"type": "filter"}
                },
                "resources": {
                    "gemfilter://filter": {"type": "filter"},
                    "gemfilter://restore": {"type": "restore"}
                }
            }))

            adapter = CodexAdapter(config_path=str(config_path))
            result = adapter.uninstall()

            assert result is True

            config = json.loads(config_path.read_text())
            assert "gemfilter" not in config.get("tools", {})

    def test_display_notification(self):
        """Test display notification."""
        adapter = CodexAdapter()

        # Should not raise
        adapter.display_notification("Test message", 3)

    def test_get_conversation_id(self):
        """Test get conversation ID."""
        adapter = CodexAdapter()

        # Should not raise, may return None
        conv_id = adapter.get_conversation_id()
        assert conv_id is None or isinstance(conv_id, str)

    def test_validate_installation_not_installed(self):
        """Test validation when not installed."""
        adapter = CodexAdapter(config_path="/nonexistent/path.json")

        result = adapter.validate_installation()

        assert result is False

    def test_validate_installation_installed(self):
        """Test validation when installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp_config.json"
            config_path.write_text(json.dumps({
                "tools": {
                    "gemfilter": {"type": "filter"}
                }
            }))

            adapter = CodexAdapter(config_path=str(config_path))
            result = adapter.validate_installation()

            assert result is True


class TestMCPTool:
    """Tests for MCPTool class."""

    def test_get_filter_tool(self):
        """Test getting filter tool definition."""
        tool = MCPTool.get_filter_tool()

        assert tool["name"] == "gemfilter"
        assert "inputSchema" in tool
        assert "outputSchema" in tool

    def test_get_restore_tool(self):
        """Test getting restore tool definition."""
        tool = MCPTool.get_restore_tool()

        assert tool["name"] == "gemfilter_restore"
        assert "inputSchema" in tool
        assert "outputSchema" in tool

    def test_get_all_tools(self):
        """Test getting all tools."""
        tools = MCPTool.get_all_tools()

        assert len(tools) == 2
        tool_names = [t["name"] for t in tools]
        assert "gemfilter" in tool_names
        assert "gemfilter_restore" in tool_names

    def test_filter_tool_schema(self):
        """Test filter tool input schema."""
        tool = MCPTool.get_filter_tool()
        schema = tool["inputSchema"]

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "text" in schema["properties"]

    def test_restore_tool_schema(self):
        """Test restore tool input schema."""
        tool = MCPTool.get_restore_tool()
        schema = tool["inputSchema"]

        assert schema["type"] == "object"
        assert "text" in schema["properties"]
        assert "session_id" in schema["properties"]
