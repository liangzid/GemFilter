# GemFilter

<p align="center">
  <img src="https://img.shields.io/badge/GemFilter-0.2.2-6C5CE7?style=for-the-badge" alt="GemFilter 0.2.2">
  <img src="https://img.shields.io/badge/privacy-local_first-00B894?style=for-the-badge" alt="Local first privacy">
  <img src="https://img.shields.io/badge/agents-Claude_Code%20%7C%20OpenCode%20%7C%20Codex-0984E3?style=for-the-badge" alt="Agent integrations">
  <img src="https://img.shields.io/badge/runtime-Python_3.11%2B-FDCB6E?style=for-the-badge" alt="Python 3.11+">
</p>

<p align="center">
  <strong>面向 coding agent 的本地隐私防火墙。</strong><br>
  GemFilter 在敏感开发者数据进入 LLM、工具结果、日志或 agent 上下文前，对其进行检测、遮蔽、追踪和净化。
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#复制给-agent-的安装提示词">复制给 Agent 的安装提示词</a> ·
  <a href="#隐私边界模型">隐私边界模型</a> ·
  <a href="#遮蔽模式">遮蔽模式</a> ·
  <a href="#agent-集成">Agent 集成</a>
</p>

---

## 复制给 Agent 的安装提示词

如果你已经在使用 coding agent，可以把下面这段 prompt 复制给 agent，并在你希望启用 GemFilter 的项目根目录中运行：

```text
请为这个 coding-agent 项目安装并配置 GemFilter。

目标：
- 从 https://github.com/liangzid/GemFilter 克隆或查看 GemFilter 项目。
- 使用 pip 安装 GemFilter。
- 在修改我的 agent 配置前，先阅读相关安装和配置文档。
- 根据当前项目使用的 coding agent 配置 GemFilter。
- 只使用 fake secret 运行安全的 smoke test。
- 不要打印、复制、总结或暴露我机器上的任何真实 secret。

步骤：
1. 如果本地没有 GemFilter repo，先临时克隆：
   git clone https://github.com/liangzid/GemFilter.git
2. 阅读 GemFilter repo 中的这些文件：
   - README.md
   - gemfilter/skill/README.md
   - docs/CONFIGURATION.md
3. 安装前先问我希望使用哪个隐私级别：
   - strict：最高隐私，使用 <EMAIL_1> 这类 typed placeholder。
   - balanced：默认选项，保留有用语法结构但隐藏真实值，例如 <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>。
   - utility：更偏任务可用性，使用看起来真实但为假的值，例如 user1@example.test。
   如果我没有回答，使用 balanced。
4. 安装 GemFilter：
   pip install gemfilter
5. 检测当前项目的 coding-agent 环境：
   - Claude Code: .claude/ 或 .claude/settings.json
   - OpenCode: ~/.config/opencode/opencode.json 或 .opencode/
   - Codex/MCP: .codex/ 或 MCP 配置
6. 按照文档配置匹配的集成方式。
7. 在使用 GemFilter 配置文件的地方，把我选择的隐私级别写入 masking_mode: strict、balanced 或 utility。
8. 只用 fake 值运行本地 smoke test：
   python -m gemfilter.cli filter "Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
9. 如果配置 OpenCode，运行一次非交互 opencode 对照测试：
   - GemFilter 启用
   - GEMFILTER_OPENCODE_DISABLED=1
10. 汇报：
   - 配置了哪个 agent 集成，
   - 选择了哪个隐私级别，
   - 修改了哪些配置文件，
   - 如何禁用或卸载，
   - smoke test 是否证明 fake email/API key 被过滤。

如果检测到多个 agent 环境，请先问我应该配置哪一个，再修改配置。
```

---

## 项目概览

GemFilter 最初是一个敏感信息过滤器。到 v0.2，它的定位更接近 **AI coding agent 的本地隐私边界**。

Coding agent 不只是读取用户 prompt。它们会查看仓库、读取文件、执行 shell 命令、接收 MCP 工具结果、保存 transcript，并在模型响应中复述上下文。敏感信息可能从多个边界泄露：

| 边界 | 风险示例 | GemFilter 保护 |
|---|---|---|
| 用户 prompt | 用户把 API key 粘贴进请求 | 发送前过滤 |
| 工具输出 | shell 输出包含 `.env` 值 | tool-output 过滤 |
| 仓库上下文 | 配置文件包含内部 endpoint | 递归 payload 过滤 |
| 模型响应 | LLM 复述 surrogate 或生成新 secret | 接收后净化 |
| CLI / HTTP 输出 | 过滤器自己返回 raw match | 默认安全序列化 |

GemFilter 是本地、规则驱动、独立于 LLM 的工具，目标是可理解、可审计、易集成。

---

## 保护哪些内容

| 类别 | 示例 |
|---|---|
| 凭证 | API key、密码、Bearer token、JWT |
| Provider token | OpenAI、Anthropic、GitHub、npm、PyPI |
| 云凭证 | AWS access key、AWS secret access key |
| 本地配置 | `.env` secret、database URL |
| 联系方式 | 邮箱、中国/美国电话号码 |
| 个人标识 | 中国身份证、护照、信用卡 |
| 网络信息 | URL、IPv4、IPv6、MAC 地址 |

默认输出是安全的：序列化检测结果默认不包含原始敏感 match，除非显式开启 unsafe debug flag。

---

## 隐私边界模型

```text
用户 prompt / 上下文
        |
        v
  pre_send hook
        |
        v
遮蔽后的上下文 -----------------------> LLM / agent
        |                                  |
        |                                  v
        |                              模型响应
        |                                  |
        v                                  v
工具输出 / MCP 结果 -----------> post_receive sanitizer
        |
        v
filter_tool_output hook
```

同一个本地 session 会在这些路径中复用 surrogate，因此 pre-send 里生成的 surrogate 可以在后续 tool output 中复用。

---

## 遮蔽模式

不同 coding 任务需要不同的隐私/可用性权衡。

| 模式 | 示例 | 适合场景 |
|---|---|---|
| `strict` | `john@example.com` -> `<EMAIL_1>` | 最大隐私 |
| `balanced` | `john@example.com` -> `<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>` | 默认 coding-agent 使用 |
| `utility` | `john@example.com` -> `user1@example.test` | 需要假数据格式有效的测试/示例 |

API key、密码、私钥、Bearer token、database URL 等高风险 secret 即使在 utility 场景下也会保留为 typed placeholder。

---

## 快速开始

### 安装

```bash
pip install gemfilter
```

本地开发：

```bash
git clone https://github.com/liangzid/GemFilter.git
cd GemFilter
pip install -e .
```

### CLI

```bash
gemfilter filter "Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
```

输出：

```text
Contact [EMAIL] and OPENAI_API_KEY=[OPENAI_API_KEY]
```

JSON 输出默认不包含 raw match：

```bash
gemfilter filter "Contact user@example.com" --json
```

如需本地调试 raw match，必须显式使用：

```bash
gemfilter filter "Contact user@example.com" --json --unsafe-include-matches
```

### Python SDK

```python
from gemfilter import SandFilter

sf = SandFilter()
result = sf.filter("我的邮箱是 test@example.com，手机 13800138000")

print(result.text)
# 我的邮箱是 [EMAIL]，手机 [PHONE_CN]
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
```

---

## 接口

| 接口 | 命令 / API | 用途 |
|---|---|---|
| Python SDK | `SandFilter` | 库内过滤 |
| Skill API | `HookManager` | agent pre-send、tool-output、post-receive hook |
| CLI | `gemfilter filter` | shell 工作流和脚本 |
| HTTP server | `gemfilter-server` | 本地 REST 过滤 |
| MCP / Codex schema | `gemfilter_filter_tool_output` | agent tool result 过滤 |

### HTTP Server

```bash
gemfilter-server --host localhost --port 8080
```

| Method | Endpoint | 描述 |
|---|---|---|
| `GET` | `/health` | 健康检查 |
| `GET` | `/rules` | 规则列表 |
| `POST` | `/filter` | 过滤单条文本 |
| `POST` | `/filter/batch` | 批量过滤文本 |

---

## Agent 集成

### Claude Code

在 coding 项目根目录运行：

```bash
pip install gemfilter
python -m gemfilter.skill.install --agent claude_code
python -m gemfilter.skill.install --agent claude_code --status
```

会创建或更新：

```text
.claude/settings.json
```

卸载：

```bash
python -m gemfilter.skill.install --agent claude_code --uninstall
```

### OpenCode

OpenCode 1.14+ 使用真实的 JavaScript plugin API。推荐方式是在 `experimental.chat.messages.transform` 中过滤 text part，让内容进入模型上下文前先经过 GemFilter。

创建 `~/.config/opencode/gemfilter-plugin.mjs`：

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

然后把插件路径加入 `~/.config/opencode/opencode.json`：

```json
{
  "plugin": ["/home/YOUR_USER/.config/opencode/gemfilter-plugin.mjs"]
}
```

用 fake secret 做真实非交互测试：

```bash
opencode run --format json \
  "Repeat exactly this one line and nothing else: Contact user@example.com and OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
```

期望模型返回：

```text
Contact [EMAIL] and OPENAI_API_KEY=[OPENAI_API_KEY]
```

临时禁用：

```bash
GEMFILTER_OPENCODE_DISABLED=1 opencode
```

### Codex / MCP

```bash
pip install gemfilter
python -m gemfilter.skill.install --agent coodex
python -m gemfilter.skill.install --agent coodex --status
```

会创建或更新：

```text
.codex/mcp_config.json
```

注意：Codex adapter 目前内部名称仍为 `coodex`，这是为了兼容旧实现；用户面向的是 Codex/MCP 集成。

---

## 配置

GemFilter 按以下顺序查找 skill 配置：

1. `GEMFILTER_SKILL_CONFIG`
2. `./config/skill.yaml`
3. `./gemfilter/skill/config.yaml`
4. `~/.gemfilter/skill.yaml`

示例：

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

如果某些 public/example 字符串必须原样进入模型上下文，可以关闭 tool-output filtering：

```yaml
filter:
  filter_tool_outputs: false
```

或者让单个 structured payload 跳过过滤：

```python
manager.filter_tool_output({
    "gemfilter_skip": True,
    "stdout": "public example value that must stay exact",
})
```

---

## 内置规则

| 规则 | 描述 |
|---|---|
| `email` | 邮箱地址 |
| `phone_cn`, `phone_us` | 中国/美国电话号码 |
| `id_card_cn`, `passport` | 个人标识 |
| `credit_card`, `bank_account_cn` | 金融标识 |
| `password`, `dotenv_secret` | 密码和 `.env` secret |
| `api_key`, `api_key_generic` | API key 和通用 `sk-...` key |
| `openai_api_key`, `anthropic_api_key` | LLM provider API key |
| `github_token`, `npm_token`, `pypi_token` | 开发平台 token |
| `bearer_token`, `jwt` | Bearer token 和 JWT |
| `aws_access_key`, `aws_secret_key` | AWS 凭证 |
| `private_key` | 私钥头 |
| `database_url` | PostgreSQL、MySQL、MongoDB、Redis URL |
| `ipv4`, `ipv6`, `mac_address`, `url` | 网络标识 |

---

## 开发

```bash
python -m pytest -q
```

更多文档：

- [Skill README](gemfilter/skill/README.md)
- [配置指南](docs/CONFIGURATION.md)
- [开发者指南](docs/DEVELOPER_GUIDE.md)
- [发布指南](docs/PUBLISHING.md)

---

## License

MIT.
