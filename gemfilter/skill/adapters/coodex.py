"""
Codex/MCP Adapter for GemFilter Skill.

Implements hooks and notifications for Codex via MCP protocol.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentAdapter, AdapterCapability, AdapterConfig

logger = logging.getLogger(__name__)


class CodexAdapter(AgentAdapter):
    """
    Adapter for Codex (via MCP - Model Context Protocol).

    Codex uses MCP for tool and context management.
    Filters are applied as MCP resources or tools.
    """

    MCP_CONFIG_FILE = ".codex/mcp_config.json"

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize Codex adapter.

        Args:
            config: Optional adapter configuration
            config_path: Optional path to MCP config
        """
        super().__init__(config)
        self._config_path = config_path or self.MCP_CONFIG_FILE
        self._original_config: Optional[Dict] = None

    @property
    def name(self) -> str:
        return "coodex"

    @property
    def supported_capabilities(self) -> List[AdapterCapability]:
        return [
            AdapterCapability.PRE_SEND_HOOK,
            AdapterCapability.POST_RECEIVE_HOOK,
            AdapterCapability.TOOL_HOOK,
            AdapterCapability.NOTIFICATION,
            AdapterCapability.SESSION_PERSISTENCE,
        ]

    def install(self) -> bool:
        """
        Install Codex MCP configuration.

        Registers GemFilter as an MCP resource filter.

        Returns:
            True if installation succeeded
        """
        try:
            config = self._load_config()
            self._original_config = config.copy()

            # Register as MCP tool
            if "tools" not in config:
                config["tools"] = {}

            config["tools"]["gemfilter"] = {
                "type": "filter",
                "handler": "gemfilter.skill.mcp_handler",
                "description": "Filter sensitive information from text",
            }

            # Register as MCP resource
            if "resources" not in config:
                config["resources"] = {}

            config["resources"]["gemfilter://filter"] = {
                "type": "filter",
                "handler": "gemfilter.skill.hooks.pre_send_hook",
            }

            config["resources"]["gemfilter://restore"] = {
                "type": "restore",
                "handler": "gemfilter.skill.hooks.post_receive_hook",
            }

            self._save_config(config)
            logger.info("Codex adapter installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install Codex adapter: {e}")
            return False

    def uninstall(self) -> bool:
        """
        Uninstall Codex MCP configuration.

        Returns:
            True if uninstallation succeeded
        """
        try:
            if self._original_config:
                self._save_config(self._original_config)
                self._original_config = None
            else:
                config = self._load_config()
                config.get("tools", {}).pop("gemfilter", None)
                config.get("resources", {}).pop("gemfilter://filter", None)
                config.get("resources", {}).pop("gemfilter://restore", None)
                self._save_config(config)

            logger.info("Codex adapter uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall Codex adapter: {e}")
            return False

    def get_conversation_id(self) -> Optional[str]:
        """
        Get current Codex conversation ID.

        Codex stores session info in MCP context.
        """
        try:
            config = self._load_config()
            session = config.get("session", {})
            return session.get("id")
        except Exception:
            return None

    def display_notification(self, message: str, gem_count: int) -> None:
        """
        Display notification via Codex MCP.

        Args:
            message: Notification message
            gem_count: Number of gems protected
        """
        logger.info(f"GemFilter: {message}")

        # Write to Codex notification endpoint if available
        notification_file = Path(".codex/.notifications")
        notification_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            notifications = []
            if notification_file.exists():
                with open(notification_file, "r") as f:
                    notifications = json.load(f)

            notifications.append({
                "source": "gemfilter",
                "message": message,
                "gem_count": gem_count,
            })

            with open(notification_file, "w") as f:
                json.dump(notifications, f)
        except Exception as e:
            logger.warning(f"Could not write notification: {e}")

    def get_hook_paths(self) -> Dict[str, str]:
        """Get Codex MCP hook paths."""
        return {
            "filter": "gemfilter.skill.hooks.pre_send_hook",
            "restore": "gemfilter.skill.hooks.post_receive_hook",
        }

    def validate_installation(self) -> bool:
        """
        Validate that MCP configuration is valid.

        Returns:
            True if GemFilter tool/resource is registered
        """
        try:
            config = self._load_config()
            tools = config.get("tools", {})
            resources = config.get("resources", {})
            return (
                "gemfilter" in tools
                or "gemfilter://filter" in resources
            )
        except Exception:
            return False

    def _load_config(self) -> Dict:
        """Load config from file."""
        path = Path(self._config_path)
        if not path.exists():
            return {}

        with open(path, "r") as f:
            return json.load(f)

    def _save_config(self, config: Dict) -> None:
        """Save config to file."""
        path = Path(self._config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(config, f, indent=2)


class MCPTool:
    """
    MCP tool definition for GemFilter.

    Can be used to register GemFilter as a proper MCP tool.
    """

    TOOL_DEFINITION = {
        "name": "gemfilter",
        "description": "Filter sensitive information from text before sending to LLM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to filter",
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session ID for tracking",
                },
            },
            "required": ["text"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "filtered_text": {
                    "type": "string",
                    "description": "Text with gems filtered",
                },
                "gem_count": {
                    "type": "number",
                    "description": "Number of gems found",
                },
                "notification": {
                    "type": "string",
                    "description": "User notification message",
                },
            },
        },
    }

    RESTORE_TOOL_DEFINITION = {
        "name": "gemfilter_restore",
        "description": "Restore filtered text after receiving LLM response",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "LLM response text to sanitize",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for gem mapping lookup",
                },
            },
            "required": ["text", "session_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "sanitized_text": {
                    "type": "string",
                    "description": "Sanitized response text",
                },
                "notification": {
                    "type": "string",
                    "description": "User notification message",
                },
            },
        },
    }

    @classmethod
    def get_filter_tool(cls) -> Dict:
        """Get the filter tool definition."""
        return cls.TOOL_DEFINITION.copy()

    @classmethod
    def get_restore_tool(cls) -> Dict:
        """Get the restore tool definition."""
        return cls.RESTORE_TOOL_DEFINITION.copy()

    @classmethod
    def get_all_tools(cls) -> List[Dict]:
        """Get all GemFilter MCP tools."""
        return [cls.TOOL_DEFINITION, cls.RESTORE_TOOL_DEFINITION]
