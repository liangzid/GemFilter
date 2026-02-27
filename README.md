# GemFilter

<p align="center">
  <img src="https://img.shields.io/pypi/v/gemfilter?style=flat-square" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/l/gemfilter?style=flat-square" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/gemfilter?style=flat-square" alt="Python Version">
  <a href="https://github.com/liangzid/GemFilter/actions"><img src="https://img.shields.io/github/actions/workflow/status/liangzid/GemFilter/test.yml?style=flat-square" alt="Tests"></a>
</p>

**Privacy Protection Filter** — Like filtering gems from sand, GemFilter protects your sensitive information.

---

## 💎 The Gem Metaphor

> *Imagine your data as a mixture of sand and gems. Sensitive information — passwords, API keys, emails, personal data — are **gems**, precious and private. Just as you'd filter gems from sand to keep them safe, **GemFilter** automatically detects and protects these sensitive pieces, preventing them from leaking into LLM prompts or AI systems.*

```
    ┌─────────────────────────────────────┐
    │           🏜️  Sand  🏜️              │
    │  ┌──────┐  ┌──────┐  ┌──────┐     │
    │  │ 💎   │  │ 🔑   │  │ 📧   │     │  ← Sensitive "Gems"
    │  └──────┘  └──────┘  └──────┘     │    need protection!
    │  ┌──────┐  ┌──────┐  ┌──────┐     │
    │  │text  │  │text  │  │text  │     │  ← Safe "Sand"
    │  └──────┘  └──────┘  └──────┘     │
    └─────────────────────────────────────┘
                    ↓
              ┌───────────┐
              │ GemFilter │
              └───────────┘
                    ↓
    ┌─────────────────────────────────────┐
    │           🏜️  Sand  🏜️              │
    │  ┌──────┐  ┌──────┐  ┌──────┐     │
    │  │[KEY] │  │[EMAIL]│  │[PHONE│     │  ← Protected!
    │  └──────┘  └──────┘  └──────┘     │
    │  ┌──────┐  ┌──────┐  ┌──────┐     │
    │  │text  │  │text  │  │text  │     │  ← Still safe
    │  └──────┘  └──────┘  └──────┘     │
    └─────────────────────────────────────┘
```

---

## ✨ Why GemFilter?

When using LLM APIs or AI agents, sensitive information can **accidentally leak** to external services, creating serious **privacy risks**. GemFilter acts as a **privacy shield**:

| 🔒 Protect These Gems | 📝 Use Cases |
|---------------------|--------------|
| 🔑 **Credentials** | Passwords, API keys, tokens, secrets |
| 📧 **Contact Info** | Emails, phone numbers, addresses |
| 💳 **Financial Data** | Credit cards, bank accounts |
| 🆔 **PII** | Names, ID numbers, passport info |
| 🌐 **Network Info** | IP addresses, URLs, MAC addresses |

---

## 🚀 Features

- 🛡️ **Privacy Protection** — Auto-detect and protect sensitive data
- 🔄 **Multiple Processors** — Replace, partial mask, delete, hash, encrypt
- 🧩 **Extensible** — Add custom rules with regex patterns
- ⚙️ **Configurable** — YAML/JSON configuration support
- 🐍 **Python SDK** — Full Python library support
- 📦 **TypeScript SDK** — Full TypeScript support
- 🌐 **HTTP Server** — REST API for filtering
- 💻 **CLI Tool** — Command-line interface
- ⚡ **Zero LLM Dependency** — Pure rule-based, no AI needed

---

## 📦 Installation

```bash
pip install gemfilter
# or
uv pip install gemfilter
```

---

## ⚡ Quick Start

```python
from gemfilter import SandFilter

sf = SandFilter()
result = sf.filter("My email is test@example.com, phone 13800138000")
print(result.text)
# Output: My email is [EMAIL], phone [PHONE_CN]
```

---

## 📚 Python SDK

### Basic Usage

```python
from gemfilter import SandFilter, Processors, DetectionRule

# Default: replace with [RULE_NAME]
sf = SandFilter()
result = sf.filter("Email: user@example.com")
print(result.text)  # Email: [EMAIL]

# Custom processor
sf.set_processor("email", Processors.partial_mask())
result = sf.filter("Email: user@example.com")
print(result.text)  # Email: u***@*******.com

# Custom rule
rule = DetectionRule(name="student_id", pattern=r"STU\d{8}", priority=1)
sf.add_rule(rule)
result = sf.filter("Student ID: STU20240001")
print(result.text)  # Student ID: [STUDENT_ID]

# Get detection details
result = sf.filter("Email: test@example.com")
print(result.summary)  # {'email': 1}
```

### Configuration File

```yaml
# config.yaml
settings:
  default_processor: rule_name

rules:
  - name: email
    enabled: false
  - name: phone_cn
    processor: partial_mask
    processor_config:
      preserve_prefix: 3
      preserve_suffix: 4
```

```python
sf = SandFilter.from_config("config.yaml")
```

---

## 💻 CLI Tool

```bash
# Filter text
gemfilter filter " test@example.com"

Email# Filter from file
gemfilter filter -i input.txt

# Verbose output
gemfilter filter "Phone 13800138000" -v

# List rules
gemfilter rules

# Disable specific rules
gemfilter filter "test" --disable email phone_cn
```

---

## 🌐 HTTP Server

```bash
# Start server
python -m gemfilter.server.main --port 8080
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/rules` | List rules |
| POST | `/filter` | Filter single text |
| POST | `/filter/batch` | Filter multiple texts |

### API Examples

```bash
# Filter single
curl -X POST http://localhost:8080/filter \
  -H "Content-Type: application/json" \
  -d '{"text": "Email test@example.com"}'

# Filter batch
curl -X POST http://localhost:8080/filter/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["email test", "phone 13800138000"]}'
```

---

## 📋 Built-in Rules

| Rule | Pattern | Description |
|------|---------|-------------|
| `email` | Email address | user@example.com |
| `phone_cn` | Chinese mobile | 1[3-9]xxxxxxxx |
| `phone_us` | US phone | +1-xxx-xxx-xxxx |
| `id_card_cn` | Chinese ID | 18-digit ID |
| `passport` | Passport | Letter+digits |
| `credit_card` | Credit card | 16-digit |
| `password` | Password | password=xxx |
| `api_key` | API key | api_key=xxx |
| `api_key_generic` | Generic API | sk-xxx |
| `bearer_token` | JWT token | Bearer xxx |
| `aws_access_key` | AWS key | AKIAxxx |
| `ipv4` | IPv4 | xxx.xxx.xxx.xxx |
| `ipv6` | IPv6 | IPv6 format |
| `mac_address` | MAC | xx:xx:xx:xx:xx:xx |
| `url` | URL | http(s)://... |

---

## 🔧 Processor Types

- `ReplaceProcessor` — Replace with custom text
- `RuleNameReplaceProcessor` — Replace with [RULE_NAME]
- `PartialMaskProcessor` — Partially mask (u***@***.com)
- `DeleteProcessor` — Remove completely
- `HashProcessor` — SHA256 hash

---

## 💡 Use Cases

### Protect LLM Prompts

```python
# Filter before sending to LLM
user_input = "My email is test@example.com, please analyze this"
filtered = sf.filter(user_input)
# Send filtered.text to LLM - sensitive info protected!
```

### API Gateway Middleware

```python
@app.post("/chat")
async def chat(request: Request):
    body = await request.body()
    filtered = sf.filter(body)
    # Proceed with filtered content
```

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=liangzid/GemFilter&type=Date)](https://star-history.com/#liangzid/GemFilter&Date)

---

## 📄 License

MIT — Made with 💎 by [liangzid](https://github.com/liangzid)
