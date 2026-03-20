"""
Base Agent Adapter for GemFilter Skill.

Abstract interface for agent-specific hook implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AdapterCapability(Enum):
    """Capabilities that adapters may support."""
    PRE_SEND_HOOK = "pre_send_hook"
    POST_RECEIVE_HOOK = "post_receive_hook"
    TOOL_HOOK = "tool_hook"
    CONTEXT_HOOK = "context_hook"
    NOTIFICATION = "notification"
    SESSION_PERSISTENCE = "session_persistence"


@dataclass
class AdapterConfig:
    """Configuration for an agent adapter."""
    enabled: bool = True
    hooks: Dict[str, str] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class AgentAdapter(ABC):
    """
    Abstract base class for agent adapters.

    Each AI coding agent (Claude Code, OpenCode, Codex) has different
    mechanisms for hooks and notifications. This base class defines
    the common interface.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        """
        Initialize the adapter.

        Args:
            config: Optional adapter configuration
        """
        self._config = config or AdapterConfig()
        self._pre_send_handler: Optional[Callable[[Any], Any]] = None
        self._post_receive_handler: Optional[Callable[[Any], Any]] = None
        self._tool_handler: Optional[Callable[[Any], Any]] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the adapter name."""
        ...

    @property
    @abstractmethod
    def supported_capabilities(self) -> List[AdapterCapability]:
        """Get list of capabilities supported by this adapter."""
        ...

    @property
    def config(self) -> AdapterConfig:
        """Get adapter configuration."""
        return self._config

    def is_capable(self, capability: AdapterCapability) -> bool:
        """Check if this adapter supports a capability."""
        return capability in self.supported_capabilities

    def register_hooks(
        self,
        pre_send: Optional[Callable[[Any], Any]] = None,
        post_receive: Optional[Callable[[Any], Any]] = None,
        tool_call: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """
        Register hook handlers.

        Args:
            pre_send: Handler called before sending to LLM
            post_receive: Handler called after receiving from LLM
            tool_call: Handler called for tool interactions
        """
        if pre_send:
            self._pre_send_handler = pre_send
        if post_receive:
            self._post_receive_handler = post_receive
        if tool_call:
            self._tool_handler = tool_call

    def unregister_hooks(self) -> None:
        """Unregister all hook handlers."""
        self._pre_send_handler = None
        self._post_receive_handler = None
        self._tool_handler = None

    @abstractmethod
    def install(self) -> bool:
        """
        Install the adapter with the host agent.

        Returns:
            True if installation succeeded, False otherwise
        """
        ...

    @abstractmethod
    def uninstall(self) -> bool:
        """
        Uninstall the adapter from the host agent.

        Returns:
            True if uninstallation succeeded, False otherwise
        """
        ...

    @abstractmethod
    def get_conversation_id(self) -> Optional[str]:
        """
        Get the current conversation/session ID.

        Returns:
            Conversation ID if available, None otherwise
        """
        ...

    @abstractmethod
    def display_notification(self, message: str, gem_count: int) -> None:
        """
        Display a notification to the user.

        Args:
            message: Notification message
            gem_count: Number of gems protected
        """
        ...

    def pre_send(self, payload: Any) -> Any:
        """
        Execute pre-send hook.

        Args:
            payload: Payload to process

        Returns:
            Processed payload
        """
        if self._pre_send_handler:
            return self._pre_send_handler(payload)
        return payload

    def post_receive(self, payload: Any) -> Any:
        """
        Execute post-receive hook.

        Args:
            payload: Payload to process

        Returns:
            Processed payload
        """
        if self._post_receive_handler:
            return self._post_receive_handler(payload)
        return payload

    def tool_call(self, payload: Any) -> Any:
        """
        Execute tool hook.

        Args:
            payload: Tool payload to process

        Returns:
            Processed payload
        """
        if self._tool_handler:
            return self._tool_handler(payload)
        return payload

    def get_hook_paths(self) -> Dict[str, str]:
        """
        Get the hook function paths for this adapter.

        Returns:
            Dict of hook_name -> module.path.function
        """
        return self._config.hooks.copy()

    def validate_installation(self) -> bool:
        """
        Validate that the adapter is properly installed.

        Returns:
            True if installation is valid, False otherwise
        """
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self._config.enabled})"


class HookPayload:
    """
    Standardized payload format for hook operations.

    Provides a consistent interface across different agent types.
    """

    def __init__(
        self,
        text: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        raw_payload: Any = None,
    ):
        self.text = text
        self.session_id = session_id
        self.metadata = metadata or {}
        self.raw_payload = raw_payload

    def has_text(self) -> bool:
        """Check if payload contains text."""
        return self.text is not None and len(self.text) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_any(cls, payload: Any) -> "HookPayload":
        """
        Create HookPayload from various payload types.

        Args:
            payload: Raw payload (str, dict, or HookPayload)

        Returns:
            HookPayload instance
        """
        if isinstance(payload, HookPayload):
            return payload
        elif isinstance(payload, str):
            return cls(text=payload, raw_payload=payload)
        elif isinstance(payload, dict):
            text = payload.get("text") or payload.get("content") or payload.get("message")
            session_id = payload.get("session_id")
            metadata = {k: v for k, v in payload.items() if k not in ["text", "session_id"]}
            return cls(text=text, session_id=session_id, metadata=metadata, raw_payload=payload)
        else:
            return cls(text=str(payload), raw_payload=payload)


def create_adapter(agent_type: str, config: Optional[AdapterConfig] = None) -> AgentAdapter:
    """
    Factory function to create an adapter by agent type.

    Args:
        agent_type: Type of agent ("claude_code", "opencode", "coodex")
        config: Optional adapter configuration

    Returns:
        AgentAdapter instance

    Raises:
        ValueError: If agent_type is unknown
    """
    # Lazy import to avoid circular import issues
    from .claude_code import ClaudeCodeAdapter
    from .opencode import OpenCodeAdapter
    from .coodex import CodexAdapter

    adapters = {
        "claude_code": ClaudeCodeAdapter,
        "opencode": OpenCodeAdapter,
        "coodex": CodexAdapter,
    }

    adapter_class = adapters.get(agent_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(adapters.keys())}")

    return adapter_class(config)
