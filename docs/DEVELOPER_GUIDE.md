# Developer Guide: Adding New Agent Adapters

This guide explains how to extend GemFilter Skill to support new AI coding agents.

---

## Overview

GemFilter uses an adapter pattern to support multiple AI coding agents. Each adapter:

1. Registers hooks with the host agent
2. Extracts conversation/session IDs
3. Displays notifications to users
4. Handles agent-specific quirks

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Host Application                   │
├─────────────────────────────────────────────────────────────┤
│                      AgentAdapter (ABC)                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  + name: str                                        │    │
│  │  + supported_capabilities: List[AdapterCapability] │    │
│  │  + install() -> bool                               │    │
│  │  + uninstall() -> bool                             │    │
│  │  + get_conversation_id() -> Optional[str]          │    │
│  │  + display_notification(message, gem_count)        │    │
│  │  + register_hooks(pre_send, post_receive, tool)    │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Concrete Adapters                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │Claude Code │ │  OpenCode  │ │   Codex    │  + more...  │
│  │  Adapter   │ │   Adapter  │ │  Adapter   │            │
│  └────────────┘ └────────────┘ └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Guide

### Step 1: Create the Adapter Class

Create a new file: `gemfilter/skill/adapters/my_agent.py`

```python
"""
MyAgent Adapter for GemFilter Skill.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentAdapter, AdapterCapability, AdapterConfig

logger = logging.getLogger(__name__)


class MyAgentAdapter(AgentAdapter):
    """
    Adapter for MyAgent AI coding tool.

    MyAgent uses <hook_file> for hook registration.
    """

    CONFIG_FILE = ".myagent/config.json"
    PLUGIN_NAME = "gemfilter"

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize MyAgent adapter.

        Args:
            config: Optional adapter configuration
            config_path: Optional path to config file
        """
        super().__init__(config)
        self._config_path = config_path or self.CONFIG_FILE
        self._original_config: Optional[Dict] = None

    @property
    def name(self) -> str:
        return "myagent"

    @property
    def supported_capabilities(self) -> List[AdapterCapability]:
        """
        Return capabilities supported by MyAgent.

        MyAgent supports:
        - PRE_SEND_HOOK: Before sending to LLM
        - POST_RECEIVE_HOOK: After receiving from LLM
        - NOTIFICATION: User notifications
        """
        return [
            AdapterCapability.PRE_SEND_HOOK,
            AdapterCapability.POST_RECEIVE_HOOK,
            AdapterCapability.NOTIFICATION,
        ]

    def install(self) -> bool:
        """
        Install hooks into MyAgent configuration.

        Returns:
            True if installation succeeded
        """
        try:
            config = self._load_config()
            self._original_config = config.copy()

            # Register hook handlers
            if "hooks" not in config:
                config["hooks"] = {}

            config["hooks"]["pre_send"] = "gemfilter.skill.hooks.pre_send_hook"
            config["hooks"]["post_receive"] = "gemfilter.skill.hooks.post_receive_hook"

            self._save_config(config)
            logger.info("MyAgent adapter installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install MyAgent adapter: {e}")
            return False

    def uninstall(self) -> bool:
        """
        Uninstall hooks from MyAgent configuration.

        Returns:
            True if uninstallation succeeded
        """
        try:
            if self._original_config:
                self._save_config(self._original_config)
                self._original_config = None
            else:
                config = self._load_config()
                if "hooks" in config:
                    config["hooks"].pop("pre_send", None)
                    config["hooks"].pop("post_receive", None)
                    self._save_config(config)

            logger.info("MyAgent adapter uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to uninstall MyAgent adapter: {e}")
            return False

    def get_conversation_id(self) -> Optional[str]:
        """
        Get current MyAgent conversation ID.

        MyAgent stores session info in its config.
        """
        try:
            config = self._load_config()
            session = config.get("session", {})
            return session.get("conversation_id")
        except Exception:
            return None

    def display_notification(self, message: str, gem_count: int) -> None:
        """
        Display notification in MyAgent UI.

        Args:
            message: Notification message
            gem_count: Number of gems protected
        """
        logger.info(f"GemFilter: {message}")

        # Write to MyAgent's notification system
        notification_file = Path(".myagent/.notifications")
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

    # Internal methods

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
```

---

### Step 2: Register the Adapter

Update `gemfilter/skill/adapters/__init__.py`:

```python
from .my_agent import MyAgentAdapter

__all__ = [
    "AgentAdapter",
    "AdapterCapability",
    "ClaudeCodeAdapter",
    "OpenCodeAdapter",
    "CodexAdapter",
    "MyAgentAdapter",  # Add this line
]
```

Update `gemfilter/skill/adapters/base.py`:

```python
def create_adapter(agent_type: str, config: Optional[AdapterConfig] = None) -> AgentAdapter:
    """Factory function to create an adapter by agent type."""
    # ... existing imports ...

    adapters = {
        "claude_code": ClaudeCodeAdapter,
        "opencode": OpenCodeAdapter,
        "coodex": CodexAdapter,
        "myagent": MyAgentAdapter,  # Add this line
    }

    adapter_class = adapters.get(agent_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
```

---

### Step 3: Add Agent Type Enum

Update `gemfilter/skill/config.py`:

```python
class AgentType(Enum):
    """Supported AI agent types."""
    CLAUDE_CODE = "claude_code"
    OPENCODE = "opencode"
    CODEX = "coodex"
    MYAGENT = "myagent"  # Add this line
```

---

### Step 4: Write Tests

Create `gemfilter/skill/tests/adapters/test_my_agent.py`:

```python
"""
Unit tests for MyAgentAdapter.
"""

import pytest
import json
import tempfile
from pathlib import Path

from gemfilter.skill.adapters.my_agent import MyAgentAdapter


class TestMyAgentAdapter:
    """Tests for MyAgentAdapter class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        adapter = MyAgentAdapter()
        assert adapter.name == "myagent"

    def test_supported_capabilities(self):
        """Test supported capabilities."""
        adapter = MyAgentAdapter()
        caps = adapter.supported_capabilities

        from gemfilter.skill.adapters.base import AdapterCapability
        assert AdapterCapability.PRE_SEND_HOOK in caps
        assert AdapterCapability.POST_RECEIVE_HOOK in caps
        assert AdapterCapability.NOTIFICATION in caps

    @patch("pathlib.Path.exists")
    def test_install_success(self, mock_exists):
        """Test successful installation."""
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")

            adapter = MyAgentAdapter(config_path=str(config_path))
            result = adapter.install()

            assert result is True

            config = json.loads(config_path.read_text())
            assert "hooks" in config
            assert "pre_send" in config["hooks"]

    # ... more tests ...
```

---

### Step 5: Document the Adapter

Add to `docs/CONFIGURATION.md`:

```markdown
### MyAgent

```yaml
agents:
  myagent:
    enabled: true
```
```

Add to `gemfilter/skill/README.md`:

```markdown
| MyAgent | Custom hooks | Any | Contact: myagent@example.com |
```

---

## Hook Registration Patterns

Different agents use different hook registration mechanisms:

### 1. Settings File (Claude Code)

```json
// .claude/settings.json
{
  "hooks": {
    "onBeforeSend": "gemfilter.skill.hooks.pre_send_hook",
    "onAfterReceive": "gemfilter.skill.hooks.post_receive_hook"
  }
}
```

### 2. Plugin System (OpenCode)

```json
// .opencode/config.json
{
  "plugins": {
    "gemfilter": {
      "enabled": true,
      "hooks": {
        "pre_send": "gemfilter.skill.hooks.pre_send_hook",
        "post_receive": "gemfilter.skill.hooks.post_receive_hook"
      }
    }
  }
}
```

### 3. MCP Protocol (Codex)

```json
// .codex/mcp_config.json
{
  "tools": {
    "gemfilter": {
      "type": "filter",
      "handler": "gemfilter.skill.mcp_handler"
    }
  },
  "resources": {
    "gemfilter://filter": {
      "type": "filter",
      "handler": "gemfilter.skill.hooks.pre_send_hook"
    }
  }
}
```

### 4. Environment Variables (Custom Agent)

```bash
# Set hook paths in environment
export GEMFILTER_PRE_SEND_HOOK="gemfilter.skill.hooks.pre_send_hook"
export GEMFILTER_POST_RECEIVE_HOOK="gemfilter.skill.hooks.post_receive_hook"
```

### 5. Function Call Interceptor (Custom Agent)

```python
class MyAgentAdapter(AgentAdapter):
    def install(self) -> bool:
        # Wrap the LLM send function
        original_send = llm.send
        def wrapped_send(payload):
            filtered = self.pre_send(payload)
            return original_send(filtered)
        llm.send = wrapped_send
        return True
```

---

## Notification Patterns

### 1. Log-based (Claude Code)

```python
logger.info(f"GemFilter: {message}")
```

### 2. File-based (OpenCode, Codex)

```python
notification_file = Path(".agent/.notifications")
notification_file.write_text(json.dumps({"message": message}))
```

### 3. UI Popup (Custom Agent)

```python
class MyAgentAdapter(AgentAdapter):
    def display_notification(self, message: str, gem_count: int) -> None:
        # Call agent's notification API
        self._agent.show_notification(
            title="🔒 GemFilter",
            body=message,
            icon="gem"
        )
```

### 4. Inline Insertion (Custom Agent)

```python
class MyAgentAdapter(AgentAdapter):
    def display_notification(self, message: str, gem_count: int) -> None:
        # Insert notification into response
        self._agent.append_to_output(f"\n\n{message}\n")
```

---

## Session/Conversation ID Patterns

### 1. File-based (Claude Code)

```python
def get_conversation_id(self) -> Optional[str]:
    session_file = Path(".claude/.session")
    if session_file.exists():
        return session_file.read_text().strip()
    return None
```

### 2. Config-based (OpenCode)

```python
def get_conversation_id(self) -> Optional[str]:
    config = self._load_config()
    return config.get("session", {}).get("conversation_id")
```

### 3. Environment Variable

```python
def get_conversation_id(self) -> Optional[str]:
    return os.environ.get("AGENT_CONVERSATION_ID")
```

### 4. API-based

```python
def get_conversation_id(self) -> Optional[str]:
    try:
        response = self._agent.api.get_current_session()
        return response["id"]
    except Exception:
        return None
```

---

## Testing Checklist

When adding a new adapter, ensure you test:

- [ ] Adapter instantiation
- [ ] `install()` creates proper configuration
- [ ] `uninstall()` restores original configuration
- [ ] `get_conversation_id()` returns correct ID
- [ ] `display_notification()` shows notification
- [ ] `validate_installation()` returns correct value
- [ ] Hook handlers are called correctly
- [ ] Error handling works gracefully

---

## Example: Terminal Agent Adapter

Here's a minimal adapter for a terminal-based agent that uses environment variables:

```python
"""
Terminal Agent Adapter - Example minimal implementation.
"""

import os
from typing import Optional, List
from gemfilter.skill.adapters.base import AgentAdapter, AdapterCapability

class TerminalAgentAdapter(AgentAdapter):
    """Adapter for terminal-based agents."""

    @property
    def name(self) -> str:
        return "terminal"

    @property
    def supported_capabilities(self) -> List[AdapterCapability]:
        return [
            AdapterCapability.PRE_SEND_HOOK,
            AdapterCapability.POST_RECEIVE_HOOK,
        ]

    def install(self) -> bool:
        # Set environment variables for hooks
        os.environ["GEMFILTER_PRE_SEND"] = "gemfilter.skill.hooks.pre_send_hook"
        os.environ["GEMFILTER_POST_RECEIVE"] = "gemfilter.skill.hooks.post_receive_hook"
        return True

    def uninstall(self) -> bool:
        os.environ.pop("GEMFILTER_PRE_SEND", None)
        os.environ.pop("GEMFILTER_POST_RECEIVE", None)
        return True

    def get_conversation_id(self) -> Optional[str]:
        return os.environ.get("TERMINAL_SESSION_ID")

    def display_notification(self, message: str, gem_count: int) -> None:
        print(f"\n{message}\n")
```

---

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Configure your adapter
- [API Reference](API.md) - Python API documentation
- [Development Log](DEVELOPMENT_LOG.md) - Implementation history
