# GemFilter Skill

**Privacy protection layer for AI coding agents**

GemFilter Skill is the agent-facing layer on top of the GemFilter detector and masker. It provides hook helpers, local session mapping, tool-output filtering, and agent integration files for privacy-sensitive coding workflows.

---

## Overview

GemFilter Skill provides:

- **Pre-send filtering**: masks sensitive values before they leave the local agent context.
- **Tool-output filtering**: recursively filters strings in command, MCP, or tool results before model ingestion.
- **Post-receive sanitization**: filters model responses that echo secrets or placeholders.
- **Local session mapping**: keeps surrogate-to-original mappings on the local machine.
- **Agent integration helpers**: installs or documents integration surfaces for Claude Code, OpenCode, and Codex/MCP-style workflows.

## Maturity Status

The skill is useful today, but it should be treated as a practical v0.2 integration layer rather than a finished security product.

| Area | Status | Notes |
|------|--------|-------|
| Core masker and hooks | Stable enough for local use | Covered by unit tests; supports strict, balanced, and utility masking modes. |
| Safe CLI/API serialization | Stable enough for local use | Raw matches are hidden by default unless explicitly requested for unsafe debugging. |
| Tool-output filtering | Usable | Recursive string filtering is implemented and tested. |
| Claude Code installer | Usable | Writes project-local hook settings. Verify against your installed Claude Code version. |
| Codex/MCP adapter | Experimental | Provides MCP-style config/schema; real host behavior may vary. |
| OpenCode installer adapter | Legacy compatibility only | Current OpenCode 1.14+ should use the JavaScript plugin approach below, not `--agent opencode`. |

Recommendation: keep the skill module. It is the right place for reusable hook logic and agent adapters. The OpenCode adapter should be modified in a future release to generate the tested JavaScript plugin automatically.

### Supported Gem Types

| Type | Example | Masked As |
|------|---------|-----------|
| Email | `john@example.com` | `<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>` |
| Phone (CN) | `13812345678` | `<PHONE_1>` |
| Phone (US) | `(123) 456-7890` | `<PHONE_1>` |
| API Key | `sk-abc123xyz...` | `<SECRET_1>` |
| OpenAI Key | `sk-proj-...` | `<OPENAI_KEY_1>` |
| Anthropic Key | `sk-ant-...` | `<ANTHROPIC_KEY_1>` |
| GitHub Token | `ghp_...` | `<GITHUB_TOKEN_1>` |
| AWS Key | `AKIAIOSFODNN7...` | `<AWS_ACCESS_KEY_1>` |
| npm Token | `npm_...` | `<NPM_TOKEN_1>` |
| PyPI Token | `pypi-...` | `<PYPI_TOKEN_1>` |
| JWT | `eyJ...` | `<JWT_1>` |
| Password | `password=secret` | `<PASSWORD_1>` |
| `.env` Secret | `SERVICE_TOKEN=...` | `<SECRET_1>` |
| Database URL | `postgres://user:pass@host/db` | `<DATABASE_URL_1>` |
| Credit Card | `4111-1111-1111-1111` | `<CREDIT_CARD_1>` |
| ID Card (CN) | `110101199001011234` | `<ID_CARD_1>` |
| Private Key | `-----BEGIN RSA...` | `<PRIVATE_KEY_1>` |
| IPv4 | `192.168.1.100` | `10.0.1.1` |
| URL | `https://api.example.com` | `https://<HOST_1>` |

---

## Installation

### Prerequisites

- Python 3.11+
- An AI coding agent (Claude Code, OpenCode, Codex)

### Install GemFilter Skill

```bash
# Recommended stable install
pip install gemfilter

# Development install from a local checkout
pip install -e .
```

### Install for Claude Code

```bash
# Navigate to your project
cd your-project

# Install the skill (creates hooks in .claude/settings.json)
pip install gemfilter
python -m gemfilter.skill.install --agent claude_code

# Verify installation
python -m gemfilter.skill.install --agent claude_code --status

# Uninstall
python -m gemfilter.skill.install --agent claude_code --uninstall
```

### Install for OpenCode

For current OpenCode versions, use the JavaScript plugin approach instead of the legacy Python adapter:

```bash
pip install gemfilter
mkdir -p ~/.config/opencode
```

Create `~/.config/opencode/gemfilter-plugin.mjs`:

```js
import { spawnSync } from "node:child_process";

const PYTHON = process.env.GEMFILTER_PYTHON || "python3";
const DISABLED = process.env.GEMFILTER_OPENCODE_DISABLED === "1";

function filterText(text) {
  if (DISABLED || typeof text !== "string" || text.length === 0) return text;
  const result = spawnSync(PYTHON, ["-m", "gemfilter.cli", "filter"], {
    input: text,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });
  if (result.status !== 0 || result.error) return text;
  return result.stdout.endsWith("\n") ? result.stdout.slice(0, -1) : result.stdout;
}

export default async function GemFilterPlugin() {
  return {
    "experimental.chat.messages.transform": async (_input, output) => {
      for (const message of output.messages ?? []) {
        for (const part of message.parts ?? []) {
          if (part?.type === "text" && typeof part.text === "string") {
            part.text = filterText(part.text);
          }
        }
      }
    },
  };
}
```

Then add the plugin path to `~/.config/opencode/opencode.json`:

```json
{
  "plugin": ["/home/YOUR_USER/.config/opencode/gemfilter-plugin.mjs"]
}
```

Test with fake values:

```bash
opencode run --format json \
  "Repeat exactly this one line and nothing else: Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
```

Expected assistant text:

```text
Contact [EMAIL] and OPENAI_API_KEY=[OPENAI_API_KEY]
```

Temporary disable:

```bash
GEMFILTER_OPENCODE_DISABLED=1 opencode
```

The legacy command below is retained for older assumptions and tests, but it is not the recommended path for OpenCode 1.14+:

```bash
python -m gemfilter.skill.install --agent opencode
```

### Install for Codex (MCP)

```bash
cd your-project
pip install gemfilter
python -m gemfilter.skill.install --agent coodex
python -m gemfilter.skill.install --agent coodex --status
python -m gemfilter.skill.install --agent coodex --uninstall
```

### Check All Agent Installations

```bash
python -m gemfilter.skill.install --status
```

---

## Quick Start

### CLI Usage

```bash
# Filter text directly
python -m gemfilter.cli filter "Contact me at john@example.com"

# Filter with config
python -m gemfilter.cli filter "Email: test@example.com" --config custom.yaml
```

### Python API

```python
from gemfilter.skill import GemMasker, GemUnmasker, HookManager

# Initialize components
masker = GemMasker()
unmasker = GemUnmasker()
hook_manager = HookManager()

# Pre-send: Mask gems
result = hook_manager.pre_send("Send to: john@example.com")
print(result.payload)  # "Send to: <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>"
print(result.notification)  # "🔒 GemFilter: 1 gem protected"

# Post-receive: Sanitize response
response = hook_manager.post_receive("I received: j***@example.com_ema")
print(response.payload)  # "I received: [FILTERED]"

# Tool-output: Filter local tool results before model ingestion
tool_result = hook_manager.filter_tool_output({
    "stdout": "OPENAI_API_KEY=sk-proj-...",
    "stderr": "Contact admin@example.com",
})
print(tool_result.payload)
```

### Integration Example

```python
from gemfilter.skill import HookManager

manager = HookManager()

# Process user input before sending to LLM
user_input = """
Please send an email to developer@company.com
and call me at 13912345678.
My API key is sk-abcdefghijk1234567890.
"""

result = manager.pre_send(user_input)
print(f"Gems detected: {result.gems_detected}")
print(f"Masked text: {result.payload}")
print(f"Notification: {result.notification}")

# The masked text is safe to send to the LLM
# Real gems are stored securely in the session
```

---

## Configuration

### Default Configuration

```yaml
# gemfilter/skill/config.yaml
skill:
  name: "gemfilter"
  version: "1.0.0"
  auto_activate: true
  activate_on:
    - context_build
    - api_request
    - tool_call

  notification:
    style: "banner"  # silent | banner | inline | detailed
    show_types: true
    show_count: true

  mask_style: "partial"  # legacy: partial | full | hash
  masking_mode: "balanced"  # strict | balanced | utility
  preserve_format: true

  agents:
    claude_code:
      enabled: true
      hooks:
        pre_send: "gemfilter.skill.hooks.pre_send_hook"
        post_receive: "gemfilter.skill.hooks.post_receive_hook"
```

### Custom Configuration

```python
from gemfilter.skill import SkillConfig, UINotifier, NotificationStyle, MaskingMode

# Create custom config
config = SkillConfig()
config.auto_activate = True
config.notification.style = NotificationStyle.DETAILED
config.masking_mode = MaskingMode.STRICT

# Save to file
save_skill_config(config, "my-config.yaml")

# Load custom config
config = load_skill_config("my-config.yaml")
```

### Masking Modes

GemFilter supports three surrogate strategies:

| Mode | Example | Best for |
|------|---------|----------|
| `strict` | `john@example.com` -> `<EMAIL_1>` | Maximum privacy for high-risk contexts |
| `balanced` | `john@example.com` -> `<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>` | Default coding-agent use; preserves syntax while hiding values |
| `utility` | `john@example.com` -> `user1@example.test` | Tests, examples, and tasks that need plausible fake data |

Secrets such as API keys, passwords, bearer tokens, and private keys use typed placeholders even in balanced mode.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Coding Agent Host                          │
│                    (Claude Code / OpenCode / Codex)              │
├─────────────────────────────────────────────────────────────────┤
│                      Skill Integration Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claude Code  │  │   OpenCode   │  │       Codex          │  │
│  │   Adapter    │  │   Adapter    │  │      Adapter         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Skill Core                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    HookManager                             │   │
│  │              pre_send_hook / post_receive_hook             │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │  GemMasker │ │ GemUnmasker│ │ UINotifier │ │   Config   │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Filter Core (Plug-and-Play)                  │
│  ┌────────────┐ ┌──────────────┐ ┌─────────────────────────┐  │
│  │   Rules    │ │  Processors  │  │       SandFilter        │  │
│  └────────────┘ └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Pre-send Hook

When you send text to an LLM:

1. **Detection**: `GemMasker` scans the text for sensitive patterns
2. **Masking**: Real gems are replaced with typed, structure-preserving, or format-preserving surrogates
3. **Mapping**: Fake → original mapping stored in the local session
4. **Notification**: User is notified of protection

```
Input:  "Email: john.doe@example.com"
Output: "Email: <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>"
        "🔒 GemFilter: 1 gem protected"
```

### 1.5. Tool-output Hook

Before shell output, file reads, MCP tool results, or other local tool outputs are added to model context:

1. **Recursive filtering**: strings inside dicts and lists are scanned.
2. **Session reuse**: existing surrogates are reused within the same session.
3. **Structured preservation**: non-string metadata such as exit codes is preserved.

```python
result = manager.filter_tool_output({
    "tool": "shell",
    "stdout": "DATABASE_URL=postgres://user:pass@db.internal:5432/app",
    "exit_code": 0,
})

print(result.payload["stdout"])  # "DATABASE_URL=<DATABASE_URL_1>"
print(result.payload["exit_code"])  # 0
```

Tool-output filtering can reduce coding-agent utility if a public string must be passed to the model exactly. You can disable it globally:

```yaml
filter:
  filter_tool_outputs: false
```

Or skip one structured payload explicitly:

```python
result = manager.filter_tool_output({
    "gemfilter_skip": True,
    "stdout": "public value that must remain exact",
})
```

### 2. Post-receive Hook

When you receive a response from LLM:

1. **Detection**: Scans for fake placeholders
2. **Sanitization**: Replaces fakes with `[FILTERED]`
3. **Gem Check**: Detects any NEW sensitive content in response
4. **Restoration**: Ensures no real gems leak through

```
Input:  "I see your email is j***@example.com_ema"
Output: "I see your email is [FILTERED]"
```

### 3. Session Management

- Sessions track gem mappings across multi-turn conversations
- Mappings are isolated per session (UUID-based)
- Sessions auto-expire after TTL (default: 1 hour)
- Original gems never leave memory

---

## Notification Styles

| Style | Example Output |
|-------|---------------|
| `silent` | (No visible notification) |
| `banner` | `🔒 GemFilter: 3 gems protected` |
| `inline` | `🔒 (3 gems filtered)` |
| `detailed` | `🔒 GemFilter Active`<br>`Protected: 3 gem(s)`<br>`Types: email, phone` |

---

## CLI Reference

```bash
# Filter text
python -m gemfilter.cli filter "text with gems"

# Start HTTP server
python -m gemfilter.server.main --port 8080

# Install for agent
python -m gemfilter.skill.install --agent claude_code

# Uninstall
python -m gemfilter.skill.install --agent claude_code --uninstall
```

---

## Testing

```bash
# Run all tests
python -m pytest gemfilter/skill/tests/ -v

# Run specific test module
python -m pytest gemfilter/skill/tests/test_masker.py -v

# Run with coverage
python -m pytest gemfilter/skill/tests/ --cov=gemfilter.skill
```

---

## Troubleshooting

### Gems not being masked

1. Check that the skill is installed: `python -m gemfilter.skill.install --status`
2. Verify detection rules are enabled in config
3. Try with CLI to confirm detection works

### Gems appearing in responses

1. Ensure post_receive hook is properly registered
2. Check session hasn't expired
3. Verify notification style isn't set to `silent`

### Import errors

```bash
# Reinstall in development mode
pip install -e .
```

---

## License

MIT License - See LICENSE file for details

---

## Links

- [Documentation](docs/)
- [API Reference](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Development Log](docs/DEVELOPMENT_LOG.md)
