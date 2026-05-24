# GemFilter Skill Configuration Guide

This guide covers all configuration options for GemFilter Skill.

---

## Configuration File Locations

GemFilter looks for configuration files in this order:

1. Path specified in `GEMFILTER_SKILL_CONFIG` environment variable
2. `./config/skill.yaml`
3. `./gemfilter/skill/config.yaml`
4. `~/.gemfilter/skill.yaml`

---

## Configuration Schema

### Top-Level Configuration

```yaml
skill:
  # Skill identification
  name: "gemfilter"           # Skill name
  version: "1.0.0"            # Skill version

  # Auto-activation settings
  auto_activate: true         # Enable skill automatically
  activate_on:                 # Events that trigger activation
    - context_build          # When building context/prompt
    - api_request            # When sending to LLM API
    - tool_call              # When calling tools

  # Notification settings
  notification:
    style: "banner"           # silent | banner | inline | detailed
    show_types: true          # Show gem types in notification
    show_count: true          # Show gem count in notification
    custom_banner: null       # Custom banner template (optional)

  # Masking settings
  mask_style: "partial"       # legacy: partial | full | hash
  masking_mode: "balanced"    # strict | balanced | utility
  preserve_format: true       # Preserve text length/format

  # Agent-specific configuration
  agents:
    claude_code:
      enabled: true
      hooks:
        pre_send: "gemfilter.skill.hooks.pre_send_hook"
        post_receive: "gemfilter.skill.hooks.post_receive_hook"

    opencode:
      enabled: true

    coodex:
      enabled: true

  # Filter core integration
  filter:
    config_path: null          # Path to filter config
    auto_update: true          # Allow auto-update of filter core
    enabled_types: []          # Only enable specific gem types
    filter_tool_outputs: true  # Filter shell/tool/MCP results before model context
```

---

## Notification Styles

### Silent

No visible notification to user.

```yaml
notification:
  style: "silent"
```

### Banner (Default)

Standard notification banner.

```yaml
notification:
  style: "banner"
```

**Output:**
```
🔒 GemFilter: 3 gems protected
```

### Inline

Compact inline notification.

```yaml
notification:
  style: "inline"
```

**Output:**
```
🔒 (3 gems filtered)
```

### Detailed

Full details with gem types.

```yaml
notification:
  style: "detailed"
```

**Output:**
```
🔒 GemFilter Active
Protected: 3 gem(s)
Types: email, phone, api_key
```

---

## Masking Modes

Masking mode controls how GemFilter balances privacy and coding-agent utility.

### Strict

Maximum privacy. Replaces sensitive values with typed placeholders.

```yaml
masking_mode: "strict"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `<EMAIL_1>` |
| API Key | `sk-proj-abc...` | `<OPENAI_KEY_1>` |

### Balanced (Default)

Preserves useful syntax while hiding sensitive values.

```yaml
masking_mode: "balanced"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>` |
| URL | `https://api.internal/v1` | `https://<HOST_1>/<PATH_1_1>` |
| API Key | `sk-proj-abc...` | `<OPENAI_KEY_1>` |

### Utility

Uses plausible fake values for contexts that need valid-looking test data.

```yaml
masking_mode: "utility"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `user1@example.test` |
| IPv4 | `10.1.2.3` | `192.0.2.2` |

Secrets such as passwords, API keys, private keys, and database URLs remain typed placeholders even when utility mode is used.

## Legacy Mask Styles

### Partial (Default)

Preserves some characters for visual recognition.

```yaml
mask_style: "partial"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `j***@example.com` |
| Phone | `13812345678` | `138****5678` |
| API Key | `sk-abc123xyz789` | `sk-***789` |

### Full

Complete masking with no visual similarity.

```yaml
mask_style: "full"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `[EMAIL]` |
| Phone | `13812345678` | `[PHONE]` |
| API Key | `sk-abc123xyz789` | `[API_KEY]` |

### Hash

One-way hash that preserves uniqueness.

```yaml
mask_style: "hash"
```

| Type | Real | Masked |
|------|------|--------|
| Email | `john.doe@example.com` | `[HASH:a1b2c3d4]` |
| Phone | `13812345678` | `[HASH:e5f6g7h8]` |

---

## Agent Configuration

### Claude Code

```yaml
agents:
  claude_code:
    enabled: true
    hooks:
      pre_send: "gemfilter.skill.hooks.pre_send_hook"
      post_receive: "gemfilter.skill.hooks.post_receive_hook"
```

Claude Code uses `settings.json` hooks. The adapter automatically registers these hooks when you run:

```bash
python -m gemfilter.skill.install --agent claude_code
```

### OpenCode

Current OpenCode versions use a JavaScript plugin array in `~/.config/opencode/opencode.json`. The recommended setup is documented in the main README and `gemfilter/skill/README.md`.

```yaml
agents:
  opencode:
    enabled: true
    # Legacy adapter config; current OpenCode should use the JS plugin.
```

The legacy Python adapter may create this older shape:

```json
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

For OpenCode 1.14+, prefer:

```json
{
  "plugin": ["/home/YOUR_USER/.config/opencode/gemfilter-plugin.mjs"]
}
```

### Codex (MCP)

```yaml
agents:
  coodex:
    enabled: true
```

Codex uses MCP (Model Context Protocol). The adapter registers:

```json
{
  "tools": {
    "gemfilter": {
      "type": "filter",
      "handler": "gemfilter.skill.mcp_handler"
    }
  }
}
```

---

## Filter Configuration

### Using Default Filter Rules

```yaml
filter:
  auto_update: true
```

### Custom Filter Config Path

```yaml
filter:
  config_path: "/path/to/my-filter-config.yaml"
  auto_update: false
```

### Enabling Specific Gem Types Only

```yaml
filter:
  enabled_types:
    - email
    - phone
    - api_key
```

Available types: `email`, `phone_cn`, `phone_us`, `id_card_cn`, `passport`, `credit_card`, `api_key`, `api_key_generic`, `password`, `bearer_token`, `aws_access_key`, `private_key`, `ipv4`, `ipv6`, `mac_address`, `url`

### Tool-output Filtering

Tool-output filtering protects shell output, file reads, MCP results, and other local tool responses before they enter model context.

```yaml
filter:
  filter_tool_outputs: true
```

Disable it if a workflow requires exact public strings to be passed to the model:

```yaml
filter:
  filter_tool_outputs: false
```

A single structured tool payload can also opt out:

```json
{
  "gemfilter_skip": true,
  "stdout": "public example output"
}
```

Use this only for content you are confident is public or intentionally shareable.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMFILTER_SKILL_CONFIG` | Path to config file | (none) |
| `GEMFILTER_SESSION_TTL` | Session timeout in seconds | `3600` |
| `GEMFILTER_LOG_LEVEL` | Logging level | `INFO` |

Example:

```bash
export GEMFILTER_SKILL_CONFIG="/path/to/config.yaml"
export GEMFILTER_SESSION_TTL="7200"  # 2 hours
export GEMFILTER_LOG_LEVEL="DEBUG"
```

---

## Programmatic Configuration

### Python API

```python
from gemfilter.skill import SkillConfig, UINotifier, NotificationStyle, MaskStyle

# Create custom configuration
config = SkillConfig()
config.auto_activate = True
config.notification.style = NotificationStyle.DETAILED
config.notification.show_types = True
config.notification.show_count = True
config.mask_style = MaskStyle.PARTIAL
config.preserve_format = True

# Use with HookManager
from gemfilter.skill import HookManager
manager = HookManager(skill_config=config)

# Use with UINotifier
notifier = UINotifier.from_config(config)
```

### Save/Load Configuration

```python
from gemfilter.skill.config import load_skill_config, save_skill_config

# Save configuration
save_skill_config(config, "my-config.yaml")

# Load configuration
config = load_skill_config("my-config.yaml")

# Validate configuration
from gemfilter.skill.config import validate_skill_config
errors = validate_skill_config(config)
if errors:
    print(f"Config errors: {errors}")
```

---

## Example Configurations

### Minimal Configuration

```yaml
skill:
  name: "gemfilter"
  version: "1.0.0"
  auto_activate: true
```

### Maximum Protection

```yaml
skill:
  name: "gemfilter"
  version: "1.0.0"
  auto_activate: true
  activate_on:
    - context_build
    - api_request
    - tool_call

  notification:
    style: "detailed"
    show_types: true
    show_count: true

  mask_style: "full"
  preserve_format: true

  filter:
    enabled_types:
      - email
      - phone_cn
      - phone_us
      - api_key
      - api_key_generic
      - password
      - credit_card
      - id_card_cn
```

### Minimal Notifications

```yaml
skill:
  name: "gemfilter"
  auto_activate: true

  notification:
    style: "silent"
```

### Development/Debug Mode

```yaml
skill:
  name: "gemfilter"
  auto_activate: true

  notification:
    style: "detailed"
    show_types: true
    show_count: true

  filter:
    auto_update: false
```

---

## Validation

Configuration is validated on load. Common issues:

| Error | Cause | Fix |
|-------|-------|-----|
| `name cannot be empty` | Missing skill name | Set `name: "gemfilter"` |
| `auto_activate without activate_on` | No events specified | Add `activate_on` list |
| `Invalid notification style` | Wrong style value | Use `silent\|banner\|inline\|detailed` |
| `Invalid hook path` | Malformed hook module path | Use `module.function` format |

---

## Next Steps

- [Developer Guide](DEVELOPER_GUIDE.md) - Adding custom adapters
- [API Reference](API.md) - Python API documentation
- [Development Log](DEVELOPMENT_LOG.md) - Implementation history
