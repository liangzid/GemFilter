# SandFilter

A lightweight, zero-dependency LLM filter that detects and masks sensitive information in text without using any LLM APIs.

## Features

- **Multiple Processor Types**: Replace, partial mask, delete, hash, encrypt
- **Extensible**: Add custom detection rules with regex patterns
- **Configurable**: YAML/JSON configuration support
- **Dual SDK**: Python and TypeScript support
- **HTTP Server**: REST API for filtering
- **CLI Tool**: Command-line interface
- **Zero LLM Dependency**: Pure rule-based detection

## Installation

```bash
pip install sandfilter
# or
uv pip install sandfilter
```

## Quick Start

```python
from sandfilter import SandFilter

sf = SandFilter()
result = sf.filter("我的邮箱是 test@example.com，手机 13800138000")
print(result.text)
# Output: 我的邮箱是 [EMAIL]，手机 [PHONE_CN]
```

## Python SDK

### Basic Usage

```python
from sandfilter import SandFilter, Processors, DetectionRule

# Default: replace with [RULE_NAME]
sf = SandFilter()
result = sf.filter("邮箱: user@example.com")
print(result.text)  # 邮箱: [EMAIL]

# Use custom processor
sf.set_processor("email", Processors.partial_mask())
result = sf.filter("邮箱: user@example.com")
print(result.text)  # 邮箱: u***@*******.com

# Add custom rule
rule = DetectionRule(
    name="student_id",
    pattern=r"STU\d{8}",
    priority=1,
)
sf.add_rule(rule)
result = sf.filter("学生ID: STU20240001")
print(result.text)  # 学生ID: [STUDENT_ID]

# Get detection details
result = sf.filter("邮箱: test@example.com")
print(result.detections)  # [Detection(...)]
print(result.summary)      # {'email': 1}
```

### Configuration File

Create `config.yaml`:

```yaml
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

  - name: student_id
    pattern: "STU\\d{8}"
    priority: 10
    processor: replace
    processor_config:
      replacement: "[STUDENT_ID]"
```

Load config:

```python
sf = SandFilter.from_config("config.yaml")
```

## CLI Tool

```bash
# Filter text
sandfilter filter "邮箱 test@example.com"

# Filter from file
sandfilter filter -i input.txt

# Filter with verbose output
sandfilter filter "手机 13800138000" -v

# List all rules
sandfilter rules

# Disable specific rules
sandfilter filter "test" --disable email phone_cn

# Use config file
sandfilter filter "test" -c config.yaml
```

## HTTP Server

```bash
# Start server
python -m sandfilter.server.main --port 8080

# Or use config
python -m sandfilter.server.main --port 8080 --config config.yaml
```

### API Endpoints

- `GET /health` - Health check
- `GET /rules` - List enabled/disabled rules
- `POST /filter` - Filter single text
- `POST /filter/batch` - Filter multiple texts

### API Examples

```bash
# Filter single text
curl -X POST http://localhost:8080/filter \
  -H "Content-Type: application/json" \
  -d '{"text": "邮箱 test@example.com"}'

# Filter batch
curl -X POST http://localhost:8080/filter/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["email test", "phone 13800138000"]}'
```

## Built-in Rules

| Rule | Pattern | Description |
|------|---------|-------------|
| email | Email address | email@example.com |
| phone_cn | Chinese mobile | 1[3-9]\d{9} |
| phone_us | US phone | +1-xxx-xxx-xxxx |
| id_card_cn | Chinese ID | 18-digit ID |
| passport | Passport | Letter+digits |
| credit_card | Credit card | 16-digit |
| password | Password | password=xxx |
| api_key | API key | api_key=xxx |
| api_key_generic | Generic API | sk-xxx |
| bearer_token | JWT token | Bearer xxx |
| aws_access_key | AWS key | AKIAxxx |
| ipv4 | IPv4 address | xxx.xxx.xxx.xxx |
| ipv6 | IPv6 address | IPv6 format |
| mac_address | MAC address | xx:xx:xx:xx:xx:xx |
| url | URL | http(s)://... |

## Processor Types

- `ReplaceProcessor` - Replace with custom text
- `RuleNameReplaceProcessor` - Replace with [RULE_NAME]
- `PartialMaskProcessor` - Partially mask (e.g., u***@***.com)
- `DeleteProcessor` - Remove completely
- `HashProcessor` - SHA256 hash

## Rule Priority

Rules are processed by priority (lower number = higher priority). When a match is found, other rules cannot match overlapping portions.

## TypeScript SDK

```typescript
import { SandFilter, Processors, createRule } from 'sandfilter';

const sf = new SandFilter();
const result = sf.filter('My email is test@example.com');
console.log(result.text); // My email is [EMAIL]
```

See `sandfilter/typescript/` for more details.
