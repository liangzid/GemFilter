"""
OpenCode Adapter for GemFilter Skill.

Implements hooks and notifications for OpenCode.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentAdapter, AdapterCapability, AdapterConfig

logger = logging.getLogger(__name__)


class OpenCodeAdapter(AgentAdapter):
    """
    Adapter for OpenCode.

    OpenCode uses a plugin system for extending functionality.
    Hooks are registered via configuration files.
    """

    CONFIG_FILE = ".opencode/config.json"
    PLUGIN_NAME = "gemfilter"

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize OpenCode adapter.

        Args:
            config: Optional adapter configuration
            config_path: Optional path to config.json
        """
        super().__init__(config)
        self._config_path = config_path or self.CONFIG_FILE
        self._original_config: Optional[Dict] = None

    @property
    def name(self) -> str:
        return "opencode"

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
        Install OpenCode plugin configuration.

        Returns:
            True if installation succeeded
        """
        try:
            config = self._load_config()

            # Store original for uninstall
            self._original_config = config.copy()

            # Register as a plugin
            if "plugins" not in config:
                config["plugins"] = {}

            config["plugins"][self.PLUGIN_NAME] = {
                "enabled": True,
                "hooks": {
                    "pre_send": "gemfilter.skill.hooks.pre_send_hook",
                    "post_receive": "gemfilter.skill.hooks.post_receive_hook",
                },
            }

            self._save_config(config)
            logger.info("OpenCode adapter installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install OpenCode adapter: {e}")
            return False

    def uninstall(self) -> bool:
        """
        Uninstall OpenCode plugin configuration.

        Returns:
            True if uninstallation succeeded
        """
        try:
            if self._original_config:
                self._save_config(self._original_config)
                self._original_config = None
            else:
                config = self._load_config()
                if "plugins" in config:
                    config["plugins"].pop(self.PLUGIN_NAME, None)
                    self._save_config(config)

            logger.info("OpenCode adapter uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall OpenCode adapter: {e}")
            return False

    def get_conversation_id(self) -> Optional[str]:
        """
        Get current OpenCode conversation ID.

        OpenCode stores session info in its config.
        """
        try:
            config = self._load_config()
            session = config.get("session", {})
            return session.get("conversation_id")
        except Exception:
            return None

    def display_notification(self, message: str, gem_count: int) -> None:
        """
        Display notification in OpenCode.

        Args:
            message: Notification message
            gem_count: Number of gems protected
        """
        logger.info(f"GemFilter: {message}")

        # Write to OpenCode's notification system if available
        notification_file = Path(".opencode/.notifications")
        notification_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            notifications = []
            if notification_file.exists():
                with open(notification_file, "r") as f:
                    notifications = json.load(f)

            notifications.append({
                "type": "gemfilter",
                "message": message,
                "gem_count": gem_count,
            })

            with open(notification_file, "w") as f:
                json.dump(notifications, f)
        except Exception as e:
            logger.warning(f"Could not write notification: {e}")

    def get_hook_paths(self) -> Dict[str, str]:
        """Get OpenCode hook paths."""
        return {
            "pre_send": "gemfilter.skill.hooks.pre_send_hook",
            "post_receive": "gemfilter.skill.hooks.post_receive_hook",
        }

    def validate_installation(self) -> bool:
        """
        Validate that plugin is properly installed.

        Returns:
            True if plugin is registered
        """
        try:
            config = self._load_config()
            plugin = config.get("plugins", {}).get(self.PLUGIN_NAME)
            return plugin is not None and plugin.get("enabled", False)
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


class OpenCodePlugin:
    """
    OpenCode plugin manifest and configuration.

    Represents the plugin in OpenCode's plugin registry.
    """

    MANIFEST = {
        "name": "gemfilter",
        "version": "1.0.0",
        "description": "Privacy protection filter for sensitive information",
        "author": "GemFilter Team",
        "hooks": {
            "pre_send": "gemfilter.skill.hooks.pre_send_hook",
            "post_receive": "gemfilter.skill.hooks.post_receive_hook",
        },
        "permissions": ["network", "filesystem"],
    }

    @classmethod
    def get_manifest(cls) -> Dict:
        """Get the plugin manifest."""
        return cls.MANIFEST.copy()

    @classmethod
    def write_manifest(cls, path: str) -> None:
        """Write manifest to plugin directory."""
        manifest_path = Path(path) / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(cls.MANIFEST, f, indent=2)
