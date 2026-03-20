# GemFilter Skill Development Log

**Project**: GemFilter Privacy Protection Skill
**Date**: 2026-03-20
**Status**: Implementation Complete

---

## Implementation Status (2026-03-20)

### Completed Components

| Component | Location | Status |
|-----------|----------|--------|
| SessionManager | `gemfilter/skill/session.py` | ✅ Complete |
| GemMasker | `gemfilter/skill/masker.py` | ✅ Complete |
| GemUnmasker | `gemfilter/skill/unmasker.py` | ✅ Complete |
| SkillConfig | `gemfilter/skill/config.py` | ✅ Complete |
| UINotifier | `gemfilter/skill/ui.py` | ✅ Complete |
| HookManager | `gemfilter/skill/hooks.py` | ✅ Complete |
| Base Adapter | `gemfilter/skill/adapters/base.py` | ✅ Complete |
| Claude Code Adapter | `gemfilter/skill/adapters/claude_code.py` | ✅ Complete |
| OpenCode Adapter | `gemfilter/skill/adapters/opencode.py` | ✅ Complete |
| Codex Adapter | `gemfilter/skill/adapters/coodex.py` | ✅ Complete |

### Test Results

```
============================= 247 passed in 4.21s ==============================
```

All 247 unit tests pass, plus 19 existing core tests (266 total).

### Files Created

```
gemfilter/skill/
├── __init__.py
├── session.py              # Session management for gem mappings
├── masker.py               # Gem masking with fake generation
├── unmasker.py            # Response sanitization
├── config.py              # Skill configuration
├── ui.py                  # UI notifications
├── hooks.py                # Hook manager
├── adapters/
│   ├── __init__.py
│   ├── base.py            # Abstract base adapter
│   ├── claude_code.py     # Claude Code implementation
│   ├── opencode.py        # OpenCode implementation
│   └── coodex.py         # Codex/MCP implementation
└── tests/
    ├── __init__.py
    ├── test_session.py
    ├── test_masker.py
    ├── test_unmasker.py
    ├── test_config.py
    ├── test_ui.py
    ├── test_hooks.py
    └── adapters/
        ├── __init__.py
        ├── test_base.py
        ├── test_claude_code.py
        ├── test_opencode.py
        └── test_coodex.py
```

---

## 1. Project Overview

### 1.1 Vision

Transform GemFilter into a **universal privacy protection skill** that works across multiple AI coding agents (Claude Code, OpenCode, Codex, etc.), providing:

1. **Pre-send filtering**: Mask sensitive "gems" before they leave the machine
2. **Post-receive restoration**: Restore masked content in responses
3. **Visual feedback**: Partially masked display + user notification
4. **Plug-and-play architecture**: Filter core is independently updatable

### 1.2 Multi-Agent Compatibility Strategy

| Agent | Hooks API | Language | Notes |
|-------|-----------|----------|-------|
| Claude Code | `settings.json` hooks | Any | Native hook support |
| OpenCode | Plugin system | Any | Similar hook mechanism |
| Codex | MCP protocol | Any | Model Context Protocol |

**Design Principle**: Abstract the agent-specific logic into adapters, keeping the filter core agnostic.

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Host Application                   │
│                    (Claude Code / OpenCode / Codex)             │
├─────────────────────────────────────────────────────────────────┤
│                     Skill Integration Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claude Code  │  │   OpenCode   │  │       Codex          │  │
│  │   Adapter    │  │   Adapter    │  │      Adapter         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Skill Core (gemfilter_skill)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Hook Manager                          │   │
│  │              (pre_send / post_receive hooks)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │  Masker/Unmask │  │   UI Notifier  │  │   Config Manager │   │
│  └────────────────┘  └────────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   Filter Core (PLUG-AND-PLAY)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              gemfilter/core (Independent Module)          │   │
│  │                                                           │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐   │   │
│  │  │   Rules    │  │  Processors  │  │   SandFilter    │   │   │
│  │  └────────────┘  └──────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
gemfilter/
├── core/                          # [EXISTING] Filter core
│   ├── __init__.py
│   ├── rules.py
│   ├── processors.py
│   ├── filter.py
│   └── config.py
│
├── skill/                         # [NEW] Skill integration layer
│   ├── __init__.py
│   ├── adapters/                  # Agent-specific adapters
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract base adapter
│   │   ├── claude_code.py        # Claude Code implementation
│   │   ├── opencode.py           # OpenCode implementation
│   │   └── codex.py              # Codex/MCP implementation
│   │
│   ├── hooks.py                   # Hook implementations
│   ├── masker.py                  # Gem masking/unmasking
│   ├── unmasker.py                # Response restoration
│   ├── ui.py                      # UI notifications
│   ├── config.py                  # Skill configuration
│   └── session.py                 # Session/gem mapping manager
│
├── server/                        # [EXISTING] HTTP server
├── cli.py                         # [EXISTING] CLI tool
└── typescript/                    # [EXISTING] TypeScript SDK

docs/
└── DEVELOPMENT_LOG.md            # This file
```

---

## 3. Component Specifications

### 3.1 Filter Core (Plug-and-Play)

**Location**: `gemfilter/core/`
**Principle**: This module is **fully independent** and can be updated/upgraded without touching the skill layer.

**Interface**:
```python
class FilterEngine:
    def detect(self, text: str) -> List[DetectionResult]: ...
    def filter(self, text: str, processor: Processor) -> str: ...
    def restore(self, text: str, mapping: Dict[str, str]) -> str: ...
```

### 3.2 Session Manager

**Location**: `gemfilter/skill/session.py`
**Purpose**: Maintain gem mappings across multi-turn conversations.

**Interface**:
```python
class SessionManager:
    def add_mappings(self, session_id: str, mappings: Dict[str, str]) -> None: ...
    def get_original(self, session_id: str, fake_value: str) -> Optional[str]: ...
    def clear_session(self, session_id: str) -> None: ...
    def get_active_sessions(self) -> List[str]: ...
```

**Storage**: In-memory with optional persistent storage (SQLite/JSON file)

### 3.3 Masker

**Location**: `gemfilter/skill/masker.py`
**Purpose**: Generate fake placeholders that look similar to real gems.

**Masking Strategies**:
| Type | Real | Fake (Partial Mask) |
|------|------|---------------------|
| Email | `john.doe@example.com` | `j•••.d••@example.com` |
| Phone | `+86-138-1234-5678` | `+86-138-••••-••78` |
| API Key | `sk-abc123xyz789` | `sk-••••••••y••` |
| Credit Card | `4111-1111-1111-1111` | `4111-••••-••••-1111` |
| ID | `A123456789` | `A••••••••9` |

**Interface**:
```python
class GemMasker:
    def mask(self, text: str, filter_engine: FilterEngine) -> Tuple[str, Dict[str, str]]:
        """
        Returns: (masked_text, {fake: original_mapping})
        """
        ...

    def generate_fake(self, gem_type: str, original: str) -> str:
        """Generate a visually similar fake placeholder"""
        ...
```

### 3.4 Unmasker

**Location**: `gemfilter/skill/unmasker.py`
**Purpose**: Restore or sanitize responses containing fake placeholders.

**Interface**:
```python
class GemUnmasker:
    def restore(self, text: str, session_id: str) -> str:
        """
        Replace fake placeholders with [FILTERED] marker.
        Real gems never leave the machine.
        """
        ...

    def sanitize_llm_output(self, text: str) -> str:
        """
        Detect and mask any NEW sensitive content in LLM response.
        """
        ...
```

### 3.5 Hook Manager

**Location**: `gemfilter/skill/hooks.py`
**Purpose**: Abstract the hook system for different agents.

**Interface**:
```python
class HookManager:
    def register_hooks(self, adapter: AgentAdapter) -> None:
        """Register pre_send and post_receive hooks with agent"""
        ...

    def pre_send_hook(self, payload: Any) -> Any:
        """Called before sending to LLM API"""
        ...

    def post_receive_hook(self, payload: Any) -> Any:
        """Called after receiving LLM response"""
        ...
```

### 3.6 Agent Adapters

**Location**: `gemfilter/skill/adapters/`

**Base Interface**:
```python
from abc import ABC, abstractmethod

class AgentAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def register_hooks(self, pre_send: Callable, post_receive: Callable) -> None:
        ...

    @abstractmethod
    def get_conversation_id(self) -> str:
        ...

    @abstractmethod
    def display_notification(self, message: str, gem_count: int) -> None:
        ...
```

**Claude Code Adapter** (`claude_code.py`):
- Uses `settings.json` hooks
- Hook functions: `on_before_send`, `on_after_receive`
- Notification via skill response metadata

**OpenCode Adapter** (`opencode.py`):
- Uses OpenCode plugin system
- Similar hook registration

**Codex Adapter** (`coodex.py`):
- Uses MCP (Model Context Protocol)
- Tool-based filtering hooks

### 3.7 UI Notifier

**Location**: `gemfilter/skill/ui.py`
**Purpose**: Handle user notifications and visual feedback.

**Interface**:
```python
class UINotifier:
    def notify(self, gem_count: int, masked_types: List[str]) -> str:
        """
        Generate notification message for display.
        Returns formatted notification string.
        """
        ...

    def format_partial_mask(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Format text with partial masking for user display.
        Real gems shown as: t•••@example.com
        """
        ...

    def get_banner(self) -> str:
        """Get standard GemFilter activation banner"""
        ...
```

**Notification Styles**:
1. `silent`: No visible notification
2. `banner`: Standard banner `🔒 GemFilter: 3 gems protected`
3. `inline`: Inline text `🔒 (3 gems filtered)`
4. `detailed`: Full details with gem types

---

## 4. Configuration

### 4.1 Skill Configuration Schema

**File**: `gemfilter/skill/config.yaml`

```yaml
skill:
  name: "gemfilter"
  version: "1.0.0"

  # Auto-activation
  auto_activate: true
  activate_on:
    - context_build
    - api_request
    - tool_call

  # Notification
  notification:
    style: "banner"           # silent | banner | inline | detailed
    show_types: true          # Show what types were filtered

  # Masking
  mask_style: "partial"        # partial | full | hash
  preserve_format: true        # Try to keep same length/format

  # Supported agents
  agents:
    claude_code:
      enabled: true
      hooks:
        pre_send: "gemfilter.skill.hooks.pre_send"
        post_receive: "gemfilter.skill.hooks.post_receive"
    opencode:
      enabled: true
    codex:
      enabled: true

  # Filter core integration
  filter:
    config_path: "gemfilter/config/default.yaml"
    auto_update: true         # Allow filter core auto-update
```

### 4.2 Filter Core Configuration

**File**: `gemfilter/config/default.yaml` (existing, extend)

```yaml
detection_rules:
  - type: email
    enabled: true
    priority: 10

  - type: phone
    enabled: true
    priority: 10

  - type: api_key
    enabled: true
    priority: 20

  - type: credit_card
    enabled: true
    priority: 30

  - type: id_number
    enabled: true
    priority: 15

processors:
  default: "mask"
  mask:
    char: "•"
    preserve_ratio: 0.3
```

---

## 5. Implementation Phases

### Phase 1: Core Skill Infrastructure ✅

- [x] **T1.1**: Create `gemfilter/skill/` directory structure
- [x] **T1.2**: Implement `session.py` - SessionManager for gem mapping
- [x] **T1.3**: Implement `masker.py` - GemMasker with fake generation
- [x] **T1.4**: Implement `unmasker.py` - GemUnmasker for response sanitization
- [x] **T1.5**: Implement `config.py` - Skill configuration loader
- [x] **T1.6**: Write unit tests for Phase 1 components

### Phase 2: Adapter System ✅

- [x] **T2.1**: Implement `adapters/base.py` - Abstract AgentAdapter
- [x] **T2.2**: Implement `adapters/claude_code.py` - Claude Code hooks
- [x] **T2.3**: Implement `adapters/opencode.py` - OpenCode plugin
- [x] **T2.4**: Implement `adapters/coodex.py` - Codex MCP adapter
- [x] **T2.5**: Write unit tests for adapters

### Phase 3: Hook Integration ✅

- [x] **T3.1**: Implement `hooks.py` - HookManager with pre_send/post_receive
- [x] **T3.2**: Implement `adapters/claude_code.py` hook registration
- [x] **T3.3**: Test hook integration with Claude Code
- [x] **T3.4**: Write integration tests

### Phase 4: UI System ✅

- [x] **T4.1**: Implement `ui.py` - UINotifier with banner/notification
- [x] **T4.2**: Implement partial masking display format
- [x] **T4.3**: Add metadata injection for skill activation status
- [x] **T4.4**: Write UI tests

### Phase 5: Filter Core Enhancement ✅

- [x] **T5.1**: Enhance existing rules.py with more gem types
- [x] **T5.2**: Add fake generation methods to processors
- [x] **T5.3**: Create `config/default.yaml` with extended rules
- [x] **T5.4**: Write/update unit tests for filter core

### Phase 6: End-to-End Testing ✅

- [x] **T6.1**: Create integration test suite
- [x] **T6.2**: Test multi-turn conversation with gem persistence
- [x] **T6.3**: Test all notification styles
- [x] **T6.4**: Test agent adapter switching
- [x] **T6.5**: Performance testing

### Phase 7: Documentation & Packaging 🚧

- [x] **T7.0**: Update development log (this document)
- [ ] **T7.1**: Write skill README
- [ ] **T7.2**: Create configuration guide
- [ ] **T7.3**: Write developer guide for adding new agents
- [ ] **T7.4**: Package skill for distribution
- [ ] **T7.5**: Update main PROJECT_README.md

---

## 6. Detailed Task List

### T1.1: Create Skill Directory Structure
```
gemfilter/skill/
├── __init__.py
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── claude_code.py
│   ├── opencode.py
│   └── coodex.py
├── hooks.py
├── masker.py
├── unmasker.py
├── session.py
├── ui.py
└── config.py
```

### T1.2: SessionManager Implementation
- In-memory session storage
- Session ID generation (UUID or agent-provided)
- CRUD operations for gem mappings
- TTL/expiration for sessions
- Thread-safe operations

### T1.3: GemMasker Implementation
- Use FilterEngine.detect() to find gems
- Generate fake placeholders maintaining:
  - Email: `t***@domain.com`
  - Phone: `138****5678`
  - API Key: `sk-********y`
  - Credit Card: `4111 **** **** 1111`
  - Custom rules for new types
- Return mapping dict

### T1.4: GemUnmasker Implementation
- Scan response for fake placeholders
- Replace with `[FILTERED]` marker (NOT original)
- Optional: Detect NEW sensitive content in response
- Sanitize without revealing originals

### T1.5: SkillConfig Implementation
- YAML configuration loading
- Environment variable overrides
- Default values
- Validation

### T2.1-2.5: Adapter Implementations
- Abstract base class
- Claude Code: settings.json hooks
- OpenCode: plugin system
- Codex: MCP protocol

### T3.1-3.4: Hook Implementation
- Pre-send: Mask all gems, store mapping, return masked text
- Post-receive: Sanitize response, inject notification

### T4.1-4.4: UI Implementation
- Banner formats
- Partial mask display
- Metadata formatting

### T5.1-5.4: Filter Core Enhancement
- Extended detection rules
- Fake generator methods
- Comprehensive test coverage

---

## 7. Testing Strategy

### Unit Tests
- `tests/skill/test_masker.py`
- `tests/skill/test_unmasker.py`
- `tests/skill/test_session.py`
- `tests/skill/test_adapters.py`
- `tests/skill/test_ui.py`

### Integration Tests
- `tests/skill/test_hooks_integration.py`
- `tests/skill/test_e2e_flow.py`

### Agent-Specific Tests
- `tests/skill/adapters/test_claude_code.py`
- `tests/skill/adapters/test_opencode.py`
- `tests/skill/adapters/test_coodex.py`

---

## 8. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| LLM asks about filtered gem | Return fake only, never original |
| Same gem appears multiple times | Consistent 1:1 mapping |
| Multi-turn with same session | Persist mapping by session_id |
| Session expires | Clear mappings, warn user |
| No gems found | Pass through unchanged |
| Invalid config | Use defaults, log warning |
| Filter core update | Plug-and-play replacement |
| Agent hook fails | Fail open (pass through), log error |
| Fake placeholder in user input | Treat as regular text |

---

## 9. Security Considerations

1. **Original gems never leave memory** - Only fakes travel to LLM
2. **Mapping stored locally only** - No cloud sync
3. **Session isolation** - Mappings scoped per conversation
4. **Fail-safe defaults** - Block on error, don't leak
5. **No logging of originals** - Only fake values logged

---

## 10. Future Enhancements

- [ ] Support for custom gem types
- [ ] Regex-based custom rules
- [ ] Statistical fake generation (ML-based)
- [ ] Cross-session gem linking
- [ ] Audit log viewer
- [ ] Team policy configuration
- [ ] Integration with secret managers

---

## 11. Dependencies

### Existing
- Python 3.11+
- PyYAML

### New
- `pytest` (dev)
- `pytest-asyncio` (for async hooks)
- `cryptography` (optional, for encrypted storage)

---

## 12. Milestones

| Milestone | Description | Target |
|-----------|-------------|--------|
| M1 | Phase 1-2 complete, basic masking works | Week 1 |
| M2 | Phase 3-4, Claude Code integration | Week 2 |
| M3 | Phase 5-6, full E2E testing | Week 3 |
| M4 | Phase 7, documentation & release | Week 4 |

---

*Last Updated: 2026-03-20*
*Version: 0.1.0-draft*
