"""
Agent Adapters for GemFilter Skill.

Provides agent-specific implementations for different AI coding tools.
"""

from .base import AgentAdapter, AdapterCapability
from .claude_code import ClaudeCodeAdapter
from .opencode import OpenCodeAdapter
from .coodex import CodexAdapter

__all__ = [
    "AgentAdapter",
    "AdapterCapability",
    "ClaudeCodeAdapter",
    "OpenCodeAdapter",
    "CodexAdapter",
]
