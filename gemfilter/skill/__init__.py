"""
GemFilter Skill Module.

Provides privacy protection skill for AI coding agents.
"""

from .session import SessionManager
from .masker import GemMasker
from .unmasker import GemUnmasker
from .hooks import HookManager, pre_send_hook, post_receive_hook
from .ui import UINotifier, NotificationStyle
from .config import SkillConfig, load_skill_config
from .adapters.base import AgentAdapter
from .adapters.claude_code import ClaudeCodeAdapter
from .adapters.opencode import OpenCodeAdapter
from .adapters.coodex import CodexAdapter

__all__ = [
    "SessionManager",
    "GemMasker",
    "GemUnmasker",
    "HookManager",
    "pre_send_hook",
    "post_receive_hook",
    "UINotifier",
    "NotificationStyle",
    "SkillConfig",
    "load_skill_config",
    "AgentAdapter",
    "ClaudeCodeAdapter",
    "OpenCodeAdapter",
    "CodexAdapter",
]
