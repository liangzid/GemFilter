# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Section：注意事项！

当你需要进行代码撰写时，请遵循以下守则：
- 不要每次完成代码修改都git commit一下。但是每次实现并调试成功了一个功能，都需要commit一下以实现备份。
- 永远避免将某一个函数写的过长或过大。如果一个功能过于复杂，那么它应当被进行拆解以获得若干个文件或者文件里地若干个函数，以此实现功能清晰、脑负担压力中等的代码阅读。
- 你每代码实现一个功能，你都应当撰写对应的测试用例，并撰写相关领域的代码进行功能的测试，一直迭代到该部分的功能实现成功为止。
- 你的代码注释应当是英文的。 （非论文代码可以删除这一行）

---

## Project Overview

**GemFilter** - Privacy Protection Filter. Like filtering gems from sand, GemFilter protects your sensitive information from leaking to LLM and AI services.

**GemFilter Skill** - An AI agent integration that provides automatic pre-send filtering and post-receive restoration for Claude Code, OpenCode, Codex, and other AI coding agents.

## Python Version

- Requires Python 3.11+

## Running the Project

```bash
# Run all tests (core + skill)
python -m pytest gemfilter/ -v

# Run core tests only
python -m pytest gemfilter/tests/ -v

# Run skill tests only
python -m pytest gemfilter/skill/tests/ -v

# CLI usage
python -m gemfilter.cli filter "test@example.com"

# HTTP server
python -m gemfilter.server.main --port 8080
```

## Development Commands

Install the package in development mode:
```bash
pip install -e .
# or
uv pip install -e .
```

## Project Structure

```
gemfilter/
├── core/                    # Core engine (Python)
│   ├── __init__.py
│   ├── rules.py             # Detection rules
│   ├── processors.py        # Text processors
│   ├── filter.py           # Main filter
│   └── config.py            # Config loader
├── skill/                   # [NEW] AI Agent Skill Integration
│   ├── __init__.py
│   ├── session.py           # SessionManager for gem mappings
│   ├── masker.py            # GemMasker - generates fake placeholders
│   ├── unmasker.py         # GemUnmasker - sanitizes responses
│   ├── hooks.py            # HookManager - pre/post hooks
│   ├── config.py           # Skill configuration
│   ├── ui.py               # UINotifier - user notifications
│   ├── adapters/            # Agent-specific adapters
│   │   ├── base.py         # Abstract AgentAdapter
│   │   ├── claude_code.py  # Claude Code adapter
│   │   ├── opencode.py     # OpenCode adapter
│   │   └── coodex.py       # Codex/MCP adapter
│   └── tests/              # Skill unit tests
├── python/                  # Python SDK wrapper
├── typescript/              # TypeScript SDK
├── config/                  # Example configs
├── server/                  # HTTP server
│   └── main.py
├── tests/                   # Core unit tests
├── cli.py                   # CLI tool
├── pyproject.toml
└── README.md
```

## Key Components

### Core Engine
- **DetectionRule**: Defines patterns to match sensitive info (email, phone, API keys, etc.)
- **Processor**: Handles how matched text is processed (replace, mask, delete, encrypt, hash)
- **SandFilter**: Main class that orchestrates rules and processors
- **FilterPipeline**: Processes text through rules and processors

### Skill Module
- **SessionManager**: Manages gem mappings across multi-turn conversations
- **GemMasker**: Detects gems and generates visually similar fake placeholders
- **GemUnmasker**: Sanitizes responses containing fake placeholders
- **HookManager**: Orchestrates pre_send and post_receive hooks
- **UINotifier**: User notification system with multiple styles
- **AgentAdapter**: Abstract interface for agent integrations

## Key Commands

```bash
# Filter text via CLI
python -m gemfilter.cli filter "邮箱 test@example.com"

# Start HTTP server
python -m gemfilter.server.main --port 8080

# Load config
python -c "from gemfilter import SandFilter; sf = SandFilter.from_config('config.yaml')"
```

## Skill Integration Commands

```bash
# Install skill for Claude Code
python -m gemfilter.skill.install --agent claude_code

# Use Skill API
python -c "
from gemfilter.skill import HookManager
manager = HookManager()
result = manager.pre_send('Email: test@example.com')
print(result.payload)  # Masked text
print(result.notification)  # '🔒 GemFilter: 1 gem protected'
"
```

## Testing

```bash
# All tests (266 total)
python -m pytest gemfilter/ -v

# Core tests (19 tests)
python -m pytest gemfilter/tests/ -v

# Skill tests (247 tests)
python -m pytest gemfilter/skill/tests/ -v
```

## Documentation

- [Main README](README.md) - English overview
- [中文 README](README.zh-CN.md) - 中文概述
- [Skill README](gemfilter/skill/README.md) - Skill details
- [Configuration Guide](docs/CONFIGURATION.md) - Configuration options
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Adding new adapters
- [Development Log](docs/DEVELOPMENT_LOG.md) - Implementation history
