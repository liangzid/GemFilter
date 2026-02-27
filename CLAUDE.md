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

**SandFilter** - A lightweight, zero-dependency LLM filter that detects and masks sensitive information in text without using any LLM APIs.

## Python Version

- Requires Python 3.11+

## Running the Project

```bash
# Run tests
python -m pytest sandfilter/tests/ -v

# CLI usage
python -m sandfilter.cli filter "test@example.com"

# HTTP server
python -m sandfilter.server.main --port 8080
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
sandfilter/
├── core/                    # Core engine (Python)
│   ├── __init__.py
│   ├── rules.py             # Detection rules
│   ├── processors.py        # Text processors
│   ├── filter.py            # Main filter
│   └── config.py            # Config loader
├── python/                  # Python SDK wrapper
├── typescript/              # TypeScript SDK
├── config/                  # Example configs
├── server/                  # HTTP server
│   └── main.py
├── tests/                   # Unit tests
│   └── test_core.py
├── cli.py                   # CLI tool
├── pyproject.toml
└── README.md
```

## Key Components

- **DetectionRule**: Defines patterns to match sensitive info (email, phone, API keys, etc.)
- **Processor**: Handles how matched text is processed (replace, mask, delete, encrypt, hash)
- **SandFilter**: Main class that orchestrates rules and processors
- **FilterPipeline**: Processes text through rules and processors

## Key Commands

```bash
# Filter text via CLI
python -m sandfilter.cli filter "邮箱 test@example.com"

# Start HTTP server
python -m sandfilter.server.main --port 8080

# Load config
python -c "from sandfilter import SandFilter; sf = SandFilter.from_config('config.yaml')"
```
