"""
Skill Configuration for GemFilter Skill.

Handles loading and validation of skill configuration.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


class NotificationStyle(Enum):
    """Notification style options."""
    SILENT = "silent"
    BANNER = "banner"
    INLINE = "inline"
    DETAILED = "detailed"
    PROMINENT = "prominent"


class MaskStyle(Enum):
    """Masking style options."""
    PARTIAL = "partial"
    FULL = "full"
    HASH = "hash"


class AgentType(Enum):
    """Supported AI agent types."""
    CLAUDE_CODE = "claude_code"
    OPENCODE = "opencode"
    CODEX = "coodex"


@dataclass
class AgentConfig:
    """Configuration for a specific agent."""
    enabled: bool = True
    hooks: Dict[str, str] = field(default_factory=dict)
    notification_style: str = "banner"
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    style: NotificationStyle = NotificationStyle.BANNER
    show_types: bool = True
    show_count: bool = True
    custom_banner: Optional[str] = None


@dataclass
class FilterConfig:
    """Configuration for filter core integration."""
    config_path: Optional[str] = None
    auto_update: bool = True
    enabled_types: List[str] = field(default_factory=list)


@dataclass
class SkillConfig:
    """Main skill configuration."""
    name: str = "gemfilter"
    version: str = "1.0.0"
    auto_activate: bool = True
    activate_on: List[str] = field(default_factory=lambda: ["context_build", "api_request", "tool_call"])
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    mask_style: MaskStyle = MaskStyle.PARTIAL
    preserve_format: bool = True
    agents: Dict[AgentType, AgentConfig] = field(default_factory=dict)
    filter_config: FilterConfig = field(default_factory=FilterConfig)

    # Internal storage for raw config
    _raw_config: Optional[Dict[str, Any]] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize default agents if not provided."""
        if not self.agents:
            self.agents = {
                AgentType.CLAUDE_CODE: AgentConfig(
                    enabled=True,
                    hooks={
                        "pre_send": "gemfilter.skill.hooks.pre_send",
                        "post_receive": "gemfilter.skill.hooks.post_receive",
                    },
                ),
                AgentType.OPENCODE: AgentConfig(enabled=True),
                AgentType.CODEX: AgentConfig(enabled=True),
            }

    def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for a specific agent."""
        return self.agents.get(agent_type, AgentConfig())

    def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if an agent type is enabled."""
        config = self.get_agent_config(agent_type)
        return config.enabled

    def should_activate_on(self, event: str) -> bool:
        """Check if skill should activate on a specific event."""
        return self.auto_activate and event in self.activate_on

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillConfig":
        """Create SkillConfig from a dictionary."""
        # Parse notification style
        notification_data = data.get("notification", {})
        notification_style = NotificationStyle(
            notification_data.get("style", "banner")
        )
        notification = NotificationConfig(
            style=notification_style,
            show_types=notification_data.get("show_types", True),
            show_count=notification_data.get("show_count", True),
            custom_banner=notification_data.get("custom_banner"),
        )

        # Parse mask style
        mask_style = MaskStyle(data.get("mask_style", "partial"))

        # Parse filter config
        filter_data = data.get("filter", {})
        filter_config = FilterConfig(
            config_path=filter_data.get("config_path"),
            auto_update=filter_data.get("auto_update", True),
            enabled_types=filter_data.get("enabled_types", []),
        )

        # Parse agents
        agents_data = data.get("agents", {})
        agents = {}
        for agent_type_str, agent_data in agents_data.items():
            try:
                agent_type = AgentType(agent_type_str)
                agents[agent_type] = AgentConfig(
                    enabled=agent_data.get("enabled", True),
                    hooks=agent_data.get("hooks", {}),
                )
            except ValueError:
                # Skip unknown agent types
                pass

        return cls(
            name=data.get("name", "gemfilter"),
            version=data.get("version", "1.0.0"),
            auto_activate=data.get("auto_activate", True),
            activate_on=data.get("activate_on", ["context_build", "api_request", "tool_call"]),
            notification=notification,
            mask_style=mask_style,
            preserve_format=data.get("preserve_format", True),
            agents=agents,
            filter_config=filter_config,
            _raw_config=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SkillConfig to a dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "auto_activate": self.auto_activate,
            "activate_on": self.activate_on,
            "notification": {
                "style": self.notification.style.value,
                "show_types": self.notification.show_types,
                "show_count": self.notification.show_count,
                "custom_banner": self.notification.custom_banner,
            },
            "mask_style": self.mask_style.value,
            "preserve_format": self.preserve_format,
            "agents": {
                agent_type.value: {
                    "enabled": config.enabled,
                    "hooks": config.hooks,
                }
                for agent_type, config in self.agents.items()
            },
            "filter": {
                "config_path": self.filter_config.config_path,
                "auto_update": self.filter_config.auto_update,
                "enabled_types": self.filter_config.enabled_types,
            },
        }


def load_skill_config(config_path: Optional[str] = None) -> SkillConfig:
    """
    Load skill configuration from a YAML file.

    Args:
        config_path: Path to config file. If not provided, looks for
                    default config in common locations.

    Returns:
        SkillConfig instance

    Raises:
        FileNotFoundError: If config file is not found
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        config_path = _find_default_config()

    if config_path is None:
        # Return default config if no file found
        return SkillConfig()

    path = Path(config_path)
    if not path.exists():
        # Return default config if file not found
        return SkillConfig()

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if data is None:
        return SkillConfig()

    return SkillConfig.from_dict(data)


def _find_default_config() -> Optional[str]:
    """
    Search for default config in common locations.

    Search order:
    1. GEMFILTER_SKILL_CONFIG env variable
    2. ./config/skill.yaml
    3. ./gemfilter/skill/config.yaml
    4. ~/.gemfilter/skill.yaml
    """
    # Check environment variable
    env_path = os.environ.get("GEMFILTER_SKILL_CONFIG")
    if env_path and Path(env_path).exists():
        return env_path

    # Check common relative paths
    search_paths = [
        Path("config/skill.yaml"),
        Path("gemfilter/skill/config.yaml"),
        Path.home() / ".gemfilter" / "skill.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return str(path)

    return None


def save_skill_config(config: SkillConfig, config_path: str) -> None:
    """
    Save skill configuration to a YAML file.

    Args:
        config: SkillConfig instance to save
        config_path: Path to save config file
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)


def validate_skill_config(config: SkillConfig) -> List[str]:
    """
    Validate a skill configuration.

    Args:
        config: SkillConfig to validate

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors = []

    if not config.name:
        errors.append("Skill name cannot be empty")

    if not config.version:
        errors.append("Version cannot be empty")

    if config.auto_activate and not config.activate_on:
        errors.append("auto_activate is True but activate_on is empty")

    # Validate notification style
    valid_styles = [s.value for s in NotificationStyle]
    style_value = config.notification.style.value
    if style_value not in valid_styles:
        errors.append(f"Invalid notification style: {style_value}")

    # Validate mask style
    valid_masks = [s.value for s in MaskStyle]
    mask_value = config.mask_style.value
    if mask_value not in valid_masks:
        errors.append(f"Invalid mask style: {mask_value}")

    # Validate agents
    for agent_type, agent_config in config.agents.items():
        if agent_config.enabled:
            for hook_name, hook_path in agent_config.hooks.items():
                if not hook_path or "." not in hook_path:
                    errors.append(
                        f"Invalid hook path for {agent_type.value}.{hook_name}: {hook_path}"
                    )

    return errors
