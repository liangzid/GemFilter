# GemFilter

**隐私保护过滤器** — 像从沙子里筛选宝石一样，GemFilter 保护您的敏感信息不被泄露到 LLM 和 AI 服务。

---

## 🎯 GemFilter Skill（AI Agent 集成）

GemFilter 作为**技能（Skill）**直接集成到 AI 编码代理中，提供自动隐私保护：

- **发送前过滤**：在敏感信息离开您的设备前自动遮蔽
- **接收后恢复**：确保敏感信息不会在响应中暴露
- **视觉反馈**：部分遮蔽的内容与用户通知
- **会话跟踪**：映射在多轮对话中保持

### Claude Code 快速开始

```bash
# 安装技能
python -m gemfilter.skill.install --agent claude_code
```

现在您的提示词将自动受到保护：

```
您: 发送邮件到 john@example.com，API密钥是 sk-abc123...
GemFilter: 🔒 GemFilter: 2 个宝石已保护

AI 响应: 我看到您想发送一封邮件...
```

### 支持的代理

| 代理 | 集成方式 | 状态 |
|------|----------|------|
| Claude Code | settings.json hooks | ✅ 稳定 |
| OpenCode | 插件系统 | ✅ 稳定 |
| Codex | MCP 协议 | ✅ 稳定 |

### 工作原理

```
用户输入: "邮箱: john@example.com, 密钥: sk-abc123..."
                    ↓
         ┌─────────────────────┐
         │   发送前钩子       │
         │   (GemMasker)      │
         └─────────────────────┘
                    ↓
遮蔽后:   "邮箱: j***@example.com_ema, 密钥: sk-***123_ema"
                    ↓
              ┌─────────┐
              │ LLM API │
              └─────────┘
                    ↓
LLM 响应: "我看到您的邮箱是 j***@example.com_ema..."
                    ↓
         ┌─────────────────────┐
         │   接收后钩子       │
         │   (GemUnmasker)    │
         └─────────────────────┘
                    ↓
净化后: "我看到您的邮箱是 [FILTERED]..."
```

详细文档：
- [技能 README](gemfilter/skill/README.md)
- [配置指南](docs/CONFIGURATION.md)
- [开发者指南](docs/DEVELOPER_GUIDE.md)

---

## 🌟 宝石隐喻

想象您的数据是沙子和宝石的混合物。敏感信息——如密码、API密钥、邮箱、个人数据——就是**珍贵的宝石**。正如您会从沙子中筛选出宝石以保护它们一样，**GemFilter** 自动检测和保护这些敏感信息，防止它们泄露到 LLM 或 AI 系统中。

## ✨ 为什么选择 GemFilter？

在使用 LLM API 或 AI Agent 时，敏感信息可能会意外发送到外部服务，造成隐私风险。GemFilter 作为**隐私护盾**，自动检测和保护：

| 🔒 保护的宝石 | 📝 使用场景 |
|-------------|-----------|
| 🔑 **凭证信息** | 密码、API密钥、令牌 |
| 📧 **联系方式** | 邮箱、电话号码 |
| 💳 **财务数据** | 信用卡、银行账户 |
| 🆔 **个人身份信息** | 身份证号、护照信息 |
| 🌐 **网络信息** | IP 地址、URL、MAC 地址 |

### 支持的宝石类型

| 类型 | 示例 | 遮蔽后 |
|------|------|--------|
| 邮箱 | `john@example.com` | `j***@example.com` |
| 电话 (中国) | `13812345678` | `138****5678` |
| 电话 (美国) | `(123) 456-7890` | `(***) ***-7890` |
| API 密钥 | `sk-abc123xyz...` | `sk-***xyz` |
| AWS 密钥 | `AKIAIOSFODNN7...` | `AKIA***...7` |
| 密码 | `password=secret` | `[PASSWORD]` |
| 信用卡 | `4111-1111-1111-1111` | `4111 **** **** 1111` |
| 身份证 | `110101199001011234` | `1***********4` |
| 私钥 | `-----BEGIN RSA...` | `[PRIVATE_KEY]` |
| IPv4 | `192.168.1.100` | `192.168.***.***` |
| URL | `https://api.example.com` | `https://***.example.com` |

---

## 🚀 功能特性

- **隐私保护**: 自动检测和保护敏感信息
- **多种处理器**: 替换、部分遮蔽、删除、哈希、加密
- **可扩展**: 使用正则表达式添加自定义检测规则
- **可配置**: 支持 YAML/JSON 配置文件
- **双语言SDK**: Python 和 TypeScript 支持
- **HTTP 服务器**: 提供 REST API 服务
- **命令行工具**: 便捷的命令行界面
- **零依赖LLM**: 纯规则引擎，无需调用大模型

---

## 📦 安装

```bash
pip install gemfilter
# 或
uv pip install gemfilter
```

---

## ⚡ 快速开始

### Python SDK

```python
from gemfilter import SandFilter

sf = SandFilter()
result = sf.filter("我的邮箱是 test@example.com，手机 13800138000")
print(result.text)
# 输出: 我的邮箱是 [EMAIL]，手机 [PHONE_CN]
```

### Python Skill API

```python
from gemfilter.skill import HookManager

manager = HookManager()
result = manager.pre_send("发送到: john@example.com")
print(result.payload)  # "发送到: j***@example.com"
print(result.notification)  # "🔒 GemFilter: 1 个宝石已保护"
```

---

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

---

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

---

## 🌐 HTTP 服务器

```bash
# 启动服务
python -m gemfilter.server.main --port 8080

# 或使用配置
python -m gemfilter.server.main --port 8080 --config config.yaml
```

### API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/rules` | 列出规则 |
| POST | `/filter` | 过滤单个文本 |
| POST | `/filter/batch` | 批量过滤 |

---

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

---

## 🔧 处理器类型

- `ReplaceProcessor` - 替换为自定义文本
- `RuleNameReplaceProcessor` - 替换为 [规则名]
- `PartialMaskProcessor` - 部分遮蔽 (如 u***@***.com)
- `DeleteProcessor` - 完全删除
- `HashProcessor` - SHA256 哈希

---

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

---

## 📄 许可证

MIT — Made with 💎 by [liangzid](https://github.com/liangzid)
