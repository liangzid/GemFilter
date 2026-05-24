# GemFilter

<p align="center">
  <img src="https://img.shields.io/badge/GemFilter-0.2.0-6C5CE7?style=for-the-badge" alt="GemFilter 0.2.0">
  <img src="https://img.shields.io/badge/privacy-local_first-00B894?style=for-the-badge" alt="Local first privacy">
  <img src="https://img.shields.io/badge/agents-Claude_Code%20%7C%20OpenCode%20%7C%20Codex-0984E3?style=for-the-badge" alt="Agent integrations">
  <img src="https://img.shields.io/badge/runtime-Python_3.11%2B-FDCB6E?style=for-the-badge" alt="Python 3.11+">
</p>

<p align="center">
  <strong>A local privacy firewall for coding agents.</strong><br>
  GemFilter detects, masks, tracks, and sanitizes sensitive developer data before it reaches LLMs, tools, logs, or agent context.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#agent-privacy-boundary">Agent Privacy Boundary</a> ·
  <a href="#masking-modes">Masking Modes</a> ·
  <a href="#interfaces">Interfaces</a> ·
  <a href="#configuration">Configuration</a>
</p>

---

## Overview

GemFilter started as a sensitive-information redactor. In v0.2, it is moving toward a more practical role: a **local privacy boundary** for AI coding agents.

Coding agents do not only receive user prompts. They inspect repositories, read files, execute shell commands, consume MCP tool results, write transcripts, and echo model responses. Private data can cross any of those boundaries:

| Boundary | Example risk | GemFilter protection |
|---|---|---|
| User prompt | User pastes an API key into a request | Pre-send filtering |
| Tool output | Shell output prints `.env` values | Tool-output filtering |
| Repository context | Config files contain private endpoints | Recursive payload filtering |
| Model response | LLM echoes a surrogate or generates a new secret | Post-receive sanitization |
| CLI / HTTP output | The filter itself returns raw matches | Safe serialization by default |

GemFilter is local, rule-based, and LLM-independent. It is designed to be understandable, auditable, and easy to integrate into agent workflows.

---

## What It Protects

GemFilter includes built-in rules for common developer privacy risks:

| Category | Examples |
|---|---|
| Credentials | API keys, passwords, bearer tokens, JWTs |
| Provider tokens | OpenAI, Anthropic, GitHub, npm, PyPI |
| Cloud secrets | AWS access keys, AWS secret access keys |
| Local config | `.env` secret assignments, database URLs |
| Contact data | Email addresses, Chinese and US phone numbers |
| Personal identifiers | Chinese ID cards, passports, credit cards |
| Network data | URLs, IPv4, IPv6, MAC addresses |

The default output is safe: serialized detections do **not** include raw sensitive matches unless an explicit unsafe debug flag is used.

---

## Agent Privacy Boundary

GemFilter protects three main runtime paths:

```text
User prompt / context
        |
        v
  pre_send hook
        |
        v
Masked context -----------------------> LLM / agent
        |                                  |
        |                                  v
        |                          model response
        |                                  |
        v                                  v
Tool output / MCP result -----> post_receive sanitizer
        |
        v
filter_tool_output hook
```

The same local session is used across these paths, so a surrogate generated during pre-send can be reused later when the same value appears in tool output.

---

## Masking Modes

Different coding tasks need different privacy-utility tradeoffs. GemFilter provides three modes.

| Mode | Example | Best for |
|---|---|---|
| `strict` | `john@example.com` -> `<EMAIL_1>` | Maximum privacy |
| `balanced` | `john@example.com` -> `<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>` | Default coding-agent use |
| `utility` | `john@example.com` -> `user1@example.test` | Tests and examples that need plausible fake data |

Secrets such as API keys, passwords, private keys, bearer tokens, and database URLs remain typed placeholders even in utility-oriented workflows.

Example:

```python
from gemfilter.skill import GemMasker

strict = GemMasker(masking_mode="strict")
balanced = GemMasker(masking_mode="balanced")
utility = GemMasker(masking_mode="utility")

text = "Contact john@example.com with OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"

print(strict.mask(text)[0])
# Contact <EMAIL_1> with OPENAI_API_KEY=<OPENAI_KEY_1>

print(balanced.mask(text)[0])
# Contact <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1> with OPENAI_API_KEY=<OPENAI_KEY_1>

print(utility.mask(text)[0])
# Contact user1@example.test with OPENAI_API_KEY=<OPENAI_KEY_1>
```

---

## Quick Start

### Install

```bash
pip install gemfilter
```

For local development:

```bash
git clone https://github.com/liangzid/GemFilter.git
cd GemFilter
pip install -e .
```

### CLI

```bash
gemfilter filter "Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
```

Output:

```text
Contact [EMAIL] and OPENAI_API_KEY=[OPENAI_API_KEY]
```

JSON output is safe by default:

```bash
gemfilter filter "Contact user@example.com" --json
```

```json
{
  "text": "Contact [EMAIL]",
  "detections": [
    {
      "rule": "email",
      "start": 8,
      "end": 24,
      "sensitive_type": "contact",
      "replacement": "[EMAIL]",
      "match_length": 16
    }
  ],
  "summary": {
    "email": 1
  }
}
```

Raw matches require an explicit unsafe opt-in:

```bash
gemfilter filter "Contact user@example.com" --json --unsafe-include-matches
```

### Python SDK

```python
from gemfilter import SandFilter

sf = SandFilter()
result = sf.filter("My email is test@example.com, phone 13800138000")

print(result.text)
# My email is [EMAIL], phone [PHONE_CN]

print(result.summary)
# {'email': 1, 'phone_cn': 1}
```

### Agent Hook API

```python
from gemfilter.skill import HookManager

manager = HookManager()

pre = manager.pre_send(
    "Send the report to john@example.com. The token is sk-proj-abcdefghijklmnopqrstuvwxyz123456.",
    session_id="demo",
)

print(pre.payload)
# Send the report to <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>. The token is <OPENAI_KEY_1>.

tool = manager.filter_tool_output(
    {
        "tool": "shell",
        "stdout": "DATABASE_URL=postgres://user:pass@db.internal:5432/app",
        "exit_code": 0,
    },
    session_id="demo",
)

print(tool.payload["stdout"])
# DATABASE_URL=<DATABASE_URL_1>

post = manager.post_receive(
    "I saw <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1> in the logs.",
    session_id="demo",
)

print(post.payload)
# I saw [FILTERED] in the logs.
```

---

## Interfaces

GemFilter can be used through several local interfaces.

| Interface | Command / API | Use case |
|---|---|---|
| Python SDK | `SandFilter` | Library filtering |
| Skill API | `HookManager` | Agent pre-send, tool-output, post-receive hooks |
| CLI | `gemfilter filter` | Shell workflows and scripts |
| HTTP server | `gemfilter-server` | Local REST filtering |
| MCP / Codex schema | `gemfilter_filter_tool_output` | Tool-result filtering for agent contexts |

### HTTP Server

```bash
gemfilter-server --host localhost --port 8080
```

Endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/rules` | Enabled and disabled rules |
| `POST` | `/filter` | Filter one text field |
| `POST` | `/filter/batch` | Filter multiple text fields |

Example:

```bash
curl -X POST http://localhost:8080/filter \
  -H "Content-Type: application/json" \
  -d '{"text": "Email user@example.com"}'
```

---

## Agent Integrations

Install GemFilter into the coding-agent project where you want local privacy protection. The installer writes agent-specific hook configuration in the current working directory.

### Copy-paste Agent Setup Prompt

If you are already using a coding agent, you can copy this prompt and send it to the agent from the root of your project:

```text
Please install and configure GemFilter for this coding-agent project.

Goal:
- Protect my local privacy before prompts, tool outputs, file contents, shell outputs, or MCP results enter model context.
- Use GemFilter's local hooks where supported.
- Do not print or expose any real secrets while configuring or testing.

Steps:
1. Detect which agent environment this project uses:
   - Claude Code if .claude/ exists or settings should be written to .claude/settings.json.
   - OpenCode if .opencode/ exists or config should be written to .opencode/config.json.
   - Codex/MCP if .codex/ exists or MCP config should be written to .codex/mcp_config.json.
2. Install GemFilter if needed:
   pip install gemfilter
3. Configure the matching adapter:
   - Claude Code:
     python -m gemfilter.skill.install --agent claude_code
   - OpenCode:
     python -m gemfilter.skill.install --agent opencode
   - Codex/MCP:
     python -m gemfilter.skill.install --agent coodex
4. Verify installation:
   python -m gemfilter.skill.install --status
5. Run a safe local smoke test without using real secrets:
   python -m gemfilter.cli filter "Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
6. Report exactly:
   - which adapter was installed,
   - which config file changed,
   - whether status checks passed,
   - whether the smoke test masked the email and fake API key.

If multiple agent environments are present, ask me which one to configure before making changes.
```

| Agent | Integration surface | Hook coverage |
|---|---|---|
| Claude Code | `settings.json` hooks | pre-send, post-receive, tool-output |
| OpenCode | plugin hooks | pre-send, post-receive, tool-output |
| Codex | MCP-style tool/resource schema | filter, restore, tool-output filter |

### Claude Code

From the root of your coding project:

```bash
pip install gemfilter
python -m gemfilter.skill.install --agent claude_code
python -m gemfilter.skill.install --agent claude_code --status
```

This creates or updates:

```text
.claude/settings.json
```

Registered hooks:

```text
onBeforeSend   -> gemfilter.skill.hooks.pre_send_hook
onAfterReceive -> gemfilter.skill.hooks.post_receive_hook
onToolOutput   -> gemfilter.skill.hooks.tool_output_hook
```

Uninstall:

```bash
python -m gemfilter.skill.install --agent claude_code --uninstall
```

### OpenCode

From the root of your coding project:

```bash
pip install gemfilter
python -m gemfilter.skill.install --agent opencode
python -m gemfilter.skill.install --agent opencode --status
```

This creates or updates:

```text
.opencode/config.json
```

Registered hooks:

```text
pre_send     -> gemfilter.skill.hooks.pre_send_hook
post_receive -> gemfilter.skill.hooks.post_receive_hook
tool_output  -> gemfilter.skill.hooks.tool_output_hook
```

Uninstall:

```bash
python -m gemfilter.skill.install --agent opencode --uninstall
```

### Codex / MCP

From the root of your coding project:

```bash
pip install gemfilter
python -m gemfilter.skill.install --agent coodex
python -m gemfilter.skill.install --agent coodex --status
```

This creates or updates:

```text
.codex/mcp_config.json
```

Registered resources and tools:

```text
gemfilter://filter      -> pre-send filtering
gemfilter://restore     -> response sanitization
gemfilter://tool-output -> tool-output filtering
gemfilter_filter_tool_output
```

Uninstall:

```bash
python -m gemfilter.skill.install --agent coodex --uninstall
```

### Check All Agents

```bash
python -m gemfilter.skill.install --status
```

Note: the Codex adapter is currently named `coodex` internally for backwards compatibility. The user-facing integration target is Codex/MCP.

Adapter behavior should still be validated against the exact live hook format of each host agent. The internal GemFilter APIs and tests are stable, but host-agent hook contracts can change.

---

## Configuration

GemFilter looks for skill configuration in this order:

1. `GEMFILTER_SKILL_CONFIG`
2. `./config/skill.yaml`
3. `./gemfilter/skill/config.yaml`
4. `~/.gemfilter/skill.yaml`

Example:

```yaml
name: "gemfilter"
version: "1.0.0"
auto_activate: true

notification:
  style: "banner"
  show_types: true
  show_count: true

masking_mode: "balanced"  # strict | balanced | utility
preserve_format: true

filter:
  config_path: null
  auto_update: true
  enabled_types: []
  filter_tool_outputs: true
```

Tool-output filtering can affect coding-agent utility when public/example strings need to remain exact. Disable it globally:

```yaml
filter:
  filter_tool_outputs: false
```

Or skip one structured payload:

```python
manager.filter_tool_output({
    "gemfilter_skip": True,
    "stdout": "public example value that must stay exact",
})
```

Full details: [Configuration Guide](docs/CONFIGURATION.md)

---

## Custom Rules

Add project-specific rules with regex patterns.

```python
from gemfilter import DetectionRule, SandFilter

sf = SandFilter()

sf.add_rule(
    DetectionRule(
        name="student_id",
        pattern=r"STU\d{8}",
        priority=1,
        sensitive_type="education",
        group="custom",
    )
)

print(sf.filter("Student ID: STU20240001").text)
# Student ID: [STUDENT_ID]
```

YAML configuration:

```yaml
settings:
  default_processor: rule_name

rules:
  - name: student_id
    pattern: "STU\\d{8}"
    priority: 10
    sensitive_type: education
    group: custom
    processor: replace
    processor_config:
      replacement: "[STUDENT_ID]"
```

---

## Built-in Rules

| Rule | Description |
|---|---|
| `email` | Email address |
| `phone_cn`, `phone_us` | Chinese and US phone numbers |
| `id_card_cn`, `passport` | Personal identifiers |
| `credit_card`, `bank_account_cn` | Financial identifiers |
| `password`, `dotenv_secret` | Passwords and `.env` secret assignments |
| `api_key`, `api_key_generic` | API key assignments and generic `sk-...` keys |
| `openai_api_key`, `anthropic_api_key` | Provider-specific LLM API keys |
| `github_token`, `npm_token`, `pypi_token` | Developer platform tokens |
| `bearer_token`, `jwt` | Bearer tokens and JWTs |
| `aws_access_key`, `aws_secret_key` | AWS credentials |
| `private_key` | Private key headers |
| `database_url` | PostgreSQL, MySQL, MongoDB, Redis URLs |
| `ipv4`, `ipv6`, `mac_address`, `url` | Network identifiers |

---

## Design Principles

| Principle | Meaning |
|---|---|
| Local first | Sensitive text is processed before it leaves the machine. |
| Safe by default | CLI and HTTP outputs do not reveal raw matches by default. |
| Agent-aware | Prompt, tool-output, and response paths are treated separately. |
| Session-aware | Surrogates are reused across a local multi-turn session. |
| Utility-conscious | Strict, balanced, and utility modes make tradeoffs explicit. |
| LLM-independent | The core engine is deterministic and rule-based. |

---

## Development

Run tests:

```bash
python -m pytest -q
```

Current v0.2 hardening coverage includes:

```text
safe CLI/HTTP serialization
session mapping correctness
strict/balanced/utility surrogate modes
stronger developer secret detection
tool-output filtering
CLI and HTTP smoke tests
```

Project documentation:

- [Skill README](gemfilter/skill/README.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Publishing Guide](docs/PUBLISHING.md)

---

## License

MIT. See the repository license for details.
