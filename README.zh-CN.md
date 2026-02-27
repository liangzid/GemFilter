# GemFilter

**隐私保护过滤器** — 像从沙子里筛选宝石一样，GemFilter 保护您的敏感信息。

## 🌟 宝石隐喻

想象您的数据是沙子和宝石的混合物。敏感信息——如密码、API密钥、邮箱、个人数据——就是**珍贵的宝石**。正如您会从沙子中筛选出宝石以保护它们一样，**GemFilter** 自动检测和保护这些敏感信息，防止它们泄露到 LLM 或 AI 系统中。

> "不要让宝石落入沙中" — 在敏感信息传送到云端之前保护它们。

## ✨ 为什么选择 GemFilter？

在使用 LLM API 或 AI Agent 时，敏感信息可能会意外发送到外部服务，造成隐私风险。GemFilter 作为**隐私护盾**，自动检测和保护：

- **个人身份信息 (PII)**: 姓名、地址、电话号码
- **凭证信息**: 密码、API 密钥、令牌
- **财务数据**: 信用卡、银行账户
- **网络信息**: IP 地址、URL

GemFilter 确保您的珍贵数据保持私密，同时允许安全内容通过。

## 🚀 功能特性

- **隐私保护**: 自动检测和保护敏感信息
- **多种处理器**: 替换、部分遮蔽、删除、哈希、加密
- **可扩展**: 使用正则表达式添加自定义检测规则
- **可配置**: 支持 YAML/JSON 配置文件
- **双语言SDK**: Python 和 TypeScript 支持
- **HTTP 服务器**: 提供 REST API 服务
- **命令行工具**: 便捷的命令行界面
- **零依赖LLM**: 纯规则引擎，无需调用大模型

## 📦 安装

```bash
pip install gemfilter
# 或
uv pip install gemfilter
```

## ⚡ 快速开始

```python
from gemfilter import SandFilter

sf = SandFilter()
result = sf.filter("我的邮箱是 test@example.com，手机 13800138000")
print(result.text)
# 输出: 我的邮箱是 [EMAIL]，手机 [PHONE_CN]
```

## 📚 Python SDK

### 基础用法

```python
from gemfilter import SandFilter, Processors, DetectionRule

# 默认: 替换为 [规则名]
sf = SandFilter()
result = sf.filter("邮箱: user@example.com")
print(result.text)  # 邮箱: [EMAIL]

# 使用自定义处理器
sf.set_processor("email", Processors.partial_mask())
result = sf.filter("邮箱: user@example.com")
print(result.text)  # 邮箱: u***@*******.com

# 添加自定义规则
rule = DetectionRule(
    name="student_id",
    pattern=r"STU\d{8}",
    priority=1,
)
sf.add_rule(rule)
result = sf.filter("学生ID: STU20240001")
print(result.text)  # 学生ID: [STUDENT_ID]

# 获取检测详情
result = sf.filter("邮箱: test@example.com")
print(result.detections)  # [Detection(...)]
print(result.summary)      # {'email': 1}
```

### 配置文件

创建 `config.yaml`:

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
```

加载配置:

```python
sf = SandFilter.from_config("config.yaml")
```

## 💻 命令行工具

```bash
# 过滤文本
gemfilter filter "邮箱 test@example.com"

# 从文件过滤
gemfilter filter -i input.txt

# 详细输出
gemfilter filter "手机 13800138000" -v

# 列出所有规则
gemfilter rules

# 禁用指定规则
gemfilter filter "test" --disable email phone_cn
```

## 🌐 HTTP 服务器

```bash
# 启动服务
python -m gemfilter.server.main --port 8080

# 或 -m gemfilter使用配置
python.server.main --port 8080 --config config.yaml
```

### API 端点

- `GET /health` - 健康检查
- `GET /rules` - 列出规则
- `POST /filter` - 过滤单个文本
- `POST /filter/batch` - 批量过滤

## 📋 内置规则

| 规则 | 描述 |
|------|------|
| email | 邮箱地址 |
| phone_cn | 中国手机号 |
| phone_us | 美国电话 |
| id_card_cn | 身份证号 |
| passport | 护照号码 |
| credit_card | 信用卡号 |
| password | 密码 |
| api_key | API 密钥 |
| api_key_generic | 通用 API Key |
| bearer_token | JWT 令牌 |
| aws_access_key | AWS 访问密钥 |
| ipv4 | IPv4 地址 |
| ipv6 | IPv6 地址 |
| mac_address | MAC 地址 |
| url | URL 链接 |

## 🔧 处理器类型

- `ReplaceProcessor` - 替换为自定义文本
- `RuleNameReplaceProcessor` - 替换为 [规则名]
- `PartialMaskProcessor` - 部分遮蔽 (如 u***@***.com)
- `DeleteProcessor` - 完全删除
- `HashProcessor` - SHA256 哈希

## 💡 使用场景

### 保护 LLM 提示

```python
# 发送敏感数据到 LLM 前进行过滤
user_input = "我的邮箱是 test@example.com，请帮我分析这份文档"
filtered = sf.filter(user_input)
# 将 filtered.text 发送给 LLM - 敏感信息已被保护
```

### API 网关中间件

```python
# 作为 API 请求的中间件
@app.post("/chat")
async def chat(request: Request):
    body = await request.body()
    filtered = sf.filter(body)
    # 继续处理过滤后的内容
```

## 📄 许可证

MIT
