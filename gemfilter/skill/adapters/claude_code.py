"""
Claude Code Adapter for GemFilter Skill.

Implements hooks and notifications for Claude Code.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import AgentAdapter, AdapterCapability, AdapterConfig

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter(AgentAdapter):
    """
    Adapter for Claude Code.

    Claude Code uses settings.json for hook configuration.
    Hooks are registered as module paths that get imported.
    """

    SETTINGS_FILE = ".claude/settings.json"
    HOOK_TEMPLATE = {
        "onBeforeSend": None,
        "onAfterReceive": None,
    }

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        settings_path: Optional[str] = None,
    ):
        """
        Initialize Claude Code adapter.

        Args:
            config: Optional adapter configuration
            settings_path: Optional path to settings.json
        """
        super().__init__(config)
        self._settings_path = settings_path or self.SETTINGS_FILE
        self._original_settings: Optional[Dict] = None

    @property
    def name(self) -> str:
        return "claude_code"

    @property
    def supported_capabilities(self) -> List[AdapterCapability]:
        return [
            AdapterCapability.PRE_SEND_HOOK,
            AdapterCapability.POST_RECEIVE_HOOK,
            AdapterCapability.CONTEXT_HOOK,
            AdapterCapability.NOTIFICATION,
        ]

    def install(self) -> bool:
        """
        Install hooks into Claude Code settings.

        Returns:
            True if installation succeeded
        """
        try:
            settings = self._load_settings()
            self._original_settings = settings.copy()

            # Update hooks
            if "hooks" not in settings:
                settings["hooks"] = {}

            settings["hooks"]["onBeforeSend"] = (
                "gemfilter.skill.hooks.pre_send_hook"
            )
            settings["hooks"]["onAfterReceive"] = (
                "gemfilter.skill.hooks.post_receive_hook"
            )

            self._save_settings(settings)
            logger.info("Claude Code adapter installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install Claude Code adapter: {e}")
            return False

    def uninstall(self) -> bool:
        """
        Uninstall hooks from Claude Code settings.

        Returns:
            True if uninstallation succeeded
        """
        try:
            if self._original_settings:
                self._save_settings(self._original_settings)
                self._original_settings = None
            else:
                # Just remove our hooks
                settings = self._load_settings()
                if "hooks" in settings:
                    settings["hooks"].pop("onBeforeSend", None)
                    settings["hooks"].pop("onAfterReceive", None)
                    self._save_settings(settings)

            logger.info("Claude Code adapter uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall Claude Code adapter: {e}")
            return False

    def get_conversation_id(self) -> Optional[str]:
        """
        Get current Claude Code conversation ID.

        Claude Code stores conversation ID in CLAUDE.md or session state.
        This is a best-effort attempt.
        """
        # Try environment variable
        conv_id = os.environ.get("CLAUDE_CONVERSATION_ID")
        if conv_id:
            return conv_id

        # Try .claude directory
        claude_dir = Path(".claude")
        if claude_dir.exists():
            # Check for session file
            session_file = claude_dir / ".session"
            if session_file.exists():
                try:
                    return session_file.read_text().strip()
                except Exception:
                    pass

        return None

    def display_notification(self, message: str, gem_count: int) -> None:
        """
        Display notification in Claude Code.

        Claude Code doesn't have native notification support,
        so we log it and it will be included in responses.

        Args:
            message: Notification message
            gem_count: Number of gems protected
        """
        logger.info(f"GemFilter: {message}")

        # Also write to a status file for CLI visibility
        status_file = Path(".gemfilter/.last_notification")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps({
            "message": message,
            "gem_count": gem_count,
        }))

    def get_hook_paths(self) -> Dict[str, str]:
        """Get Claude Code hook paths."""
        return {
            "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
            "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook",
        }

    def validate_installation(self) -> bool:
        """
        Validate that hooks are properly installed.

        Returns:
            True if hooks are registered in settings.json
        """
        try:
            settings = self._load_settings()
            hooks = settings.get("hooks", {})
            return (
                hooks.get("onBeforeSend") == "gemfilter.skill.hooks.pre_send_hook"
                and hooks.get("onAfterReceive") == "gemfilter.skill.hooks.post_receive_hook"
            )
        except Exception:
            return False

    def _load_settings(self) -> Dict:
        """Load settings from settings.json."""
        path = Path(self._settings_path)
        if not path.exists():
            return {"hooks": {}}

        with open(path, "r") as f:
            return json.load(f)

    def _save_settings(self, settings: Dict) -> None:
        """Save settings to settings.json."""
        path = Path(self._settings_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(settings, f, indent=2)

    def enable_hooks(self) -> bool:
        """Enable the registered hooks."""
        return self.install()

    def disable_hooks(self) -> bool:
        """Disable hooks temporarily (without uninstalling)."""
        try:
            settings = self._load_settings()
            if "hooks" in settings:
                settings["hooks"]["onBeforeSend"] = None
                settings["hooks"]["onAfterReceive"] = None
                self._save_settings(settings)
            return True
        except Exception as e:
            logger.error(f"Failed to disable hooks: {e}")
            return False


class ClaudeCodeSettings:
    """
    Helper class for working with Claude Code settings.

    Provides more granular control over settings management.
    """

    def __init__(self, settings_path: Optional[str] = None):
        """
        Initialize settings helper.

        Args:
            settings_path: Path to settings.json
        """
        self._settings_path = settings_path or ClaudeCodeAdapter.SETTINGS_FILE
        self._settings: Optional[Dict] = None

    def load(self) -> Dict:
        """Load settings from file."""
        path = Path(self._settings_path)
        if not path.exists():
            return {}

        with open(path, "r") as f:
            self._settings = json.load(f)
        return self._settings

    def save(self, settings: Optional[Dict] = None) -> None:
        """Save settings to file."""
        if settings is not None:
            self._settings = settings
        if self._settings is None:
            return

        path = Path(self._settings_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._settings, f, indent=2)

    def get_hooks(self) -> Dict[str, Any]:
        """Get current hooks configuration."""
        if self._settings is None:
            self.load()
        return self._settings.get("hooks", {})

    def set_hook(self, event: str, handler: Optional[str]) -> None:
        """
        Set a hook handler.

        Args:
            event: Event name (e.g., "onBeforeSend")
            handler: Module path to handler function
        """
        if self._settings is None:
            self.load()

        if "hooks" not in self._settings:
            self._settings["hooks"] = {}

        self._settings["hooks"][event] = handler

    def remove_hook(self, event: str) -> None:
        """Remove a hook handler."""
        if self._settings is None:
            self.load()

        if "hooks" in self._settings:
            self._settings["hooks"].pop(event, None)
