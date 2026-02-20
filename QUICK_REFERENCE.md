# DaoyouCode 快速参考

## 🚀 立即开始

### 1. 安装依赖

```bash
cd backend
pip install -e .
```

### 2. 配置 API Key

编辑 `backend/config/llm_config.yaml`:

```yaml
providers:
  qwen:
    api_key: ["your-api-key-here"]  # 替换为你的 API Key
    enabled: true
```

### 3. 测试功能

```bash
# 测试 AI 修改代码（重要！）
backend\test_ai_modify.bat

# 或手动测试
daoyoucode chat "你好"
```

### ⚠️ 重要：确保 AI 能真正修改代码

如果 AI 只是在回复中显示代码而不是真正修改文件，请查看：
- `backend/AI_TOOL_CALLING_FIX_SUMMARY.md` - 工具调用修复
- `backend/AI_NOT_CALLING_TOOLS_DIAGNOSIS.md` - 问题诊断

## 📚 核心命令

### 交互式对话

```bash
# 基本对话
daoyoucode chat

# 使用特定 Skill
daoyoucode chat --skill sisyphus-orchestrator
daoyoucode chat --skill oracle
daoyoucode chat --skill librarian

# 加载文件
daoyoucode chat backend/config/llm_config.yaml

# 指定模型
daoyoucode chat --model qwen-max
```

### 对话中的命令

```
/help          - 显示帮助
/skill [name]  - 切换 Skill
/model [name]  - 切换模型
/exit          - 退出对话
```

## 🎯 推荐 Skills

| Skill | 用途 | 编排器 |
|-------|------|--------|
| `chat-assistant` | 日常对话和代码咨询 | simple |
| `sisyphus-orchestrator` | 复杂任务（重构+测试） | react |
| `oracle` | 架构分析（只读） | simple |
| `librarian` | 文档搜索（只读） | simple |
| `programming` | 代码编写 | react |
| `refactoring` | 代码重构 | react |
| `testing` | 测试生成 | react |

## 🛠️ 常见任务

### 修改代码

```bash
daoyoucode chat "修改 backend/config/llm_config.yaml，将 max_tokens 从 4000 改为 8000"
```

### 重构代码

```bash
daoyoucode chat --skill refactoring "重构 backend/cli/commands/chat.py 的 handle_chat 函数"
```

### 分析架构

```bash
daoyoucode chat --skill oracle "分析 backend/daoyoucode/agents/ 的架构设计"
```

### 搜索代码

```bash
daoyoucode chat --skill librarian "找到所有使用 LSP 的代码"
```

### 生成测试

```bash
daoyoucode chat --skill testing "为 backend/daoyoucode/agents/tools/lsp_tools.py 生成测试"
```

## 📁 项目结构

```
daoyoucode/
├── backend/                    # Python 后端
│   ├── cli/                   # CLI 命令
│   ├── config/                # 配置文件
│   │   ├── llm_config.yaml   # LLM API 配置
│   │   └── timeout.yaml      # 超时配置
│   ├── daoyoucode/           # 核心代码
│   │   └── agents/           # Agent 系统
│   │       ├── builtin/      # 内置 Agents
│   │       ├── core/         # 核心组件
│   │       ├── llm/          # LLM 客户端
│   │       ├── memory/       # 记忆系统
│   │       ├── orchestrators/ # 编排器
│   │       └── tools/        # 工具系统
│   ├── tests/                # 测试
│   └── pyproject.toml        # 依赖配置
├── skills/                    # Skill 定义
│   ├── chat-assistant/
│   ├── sisyphus-orchestrator/
│   ├── oracle/
│   └── ...
└── docs/                      # 文档
```

## 🔧 配置文件

### backend/config/llm_config.yaml

```yaml
providers:
  qwen:
    api_key: ["sk-xxx", "sk-yyy"]  # 支持多 Key 轮询
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    models:
      - qwen-max
      - qwen-plus
    enabled: true

default:
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 4000
  timeout: 1800  # 30 分钟
```

### backend/pyproject.toml

```toml
[project]
name = "daoyoucode"
version = "0.1.0"
dependencies = [
    "openai>=1.0.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",
    # ... 更多依赖
]

[project.optional-dependencies]
embedding = [
    "sentence-transformers>=2.2.0",
    "torch>=2.0.0",
]
```

## 🐛 故障排查

### 问题：找不到文件

```
⚠️  工具返回错误: File not found: config/llm_config.yaml
```

**解决**: 使用完整相对路径

```bash
# ❌ 错误
daoyoucode chat "读取 config/llm_config.yaml"

# ✅ 正确
daoyoucode chat "读取 backend/config/llm_config.yaml"
```

### 问题：请求超时

```
警告: 请求超时（120秒）
```

**解决**: 已修复，现在从配置读取（1800 秒）

```bash
# 重新安装
cd backend
pip install -e .
```

### 问题：LSP 服务不稳定

```
LSP server not found
```

**解决**: 已修复，支持虚拟环境检测

```bash
# 安装 LSP 服务
pip install pyright python-lsp-server

# 运行健康检查
python backend/lsp_health_check.py
```

### 问题：API Key 错误

```
Error: Invalid API key
```

**解决**: 检查配置文件

```bash
# 编辑配置
notepad backend/config/llm_config.yaml

# 确保格式正确
providers:
  qwen:
    api_key: ["sk-your-key-here"]  # 注意是列表格式
```

## 📖 文档索引

### 核心文档

- `README.md` - 项目介绍
- `ARCHITECTURE.md` - 架构设计
- `backend/QUICK_START.md` - 快速开始
- `backend/USAGE_GUIDE.md` - 使用指南

### 配置文档

- `backend/CONFIG_GUIDE.md` - 配置指南
- `backend/TIMEOUT_CONFIG_GUIDE.md` - 超时配置
- `backend/PATH_USAGE_GUIDE.md` - 路径使用规范

### 技术文档

- `backend/01_CLI命令参考.md` - CLI 命令
- `backend/02_ORCHESTRATORS编排器介绍.md` - 编排器
- `backend/03_AGENTS智能体介绍.md` - Agents
- `backend/04_TOOLS工具参考.md` - 工具
- `backend/05_LSP和AST技术说明.md` - LSP/AST

### 测试文档

- `backend/TEST_REPORT.md` - 测试报告
- `backend/TEST_STRATEGY.md` - 测试策略
- `backend/SKILLS_REPORT.md` - Skills 测试

### 修复文档

- `backend/LSP_STABILITY_GUIDE.md` - LSP 稳定性
- `backend/TIMEOUT_FIX_SUMMARY.md` - 超时修复
- `backend/TOOL_PATH_FIX_SUMMARY.md` - 路径修复
- `backend/AI_MODIFICATION_REVIEW.md` - AI 修改评审
- `backend/AI_MODIFICATION_FINAL_STATUS.md` - 最终状态

## 🎓 学习路径

### 1. 新手入门

1. 阅读 `README.md`
2. 运行 `backend\test_ai_modify.bat`
3. 尝试基本对话：`daoyoucode chat "你好"`
4. 查看 Skills：`/skill`

### 2. 进阶使用

1. 学习不同 Skills 的用途
2. 尝试修改代码
3. 使用 oracle 分析架构
4. 使用 librarian 搜索代码

### 3. 高级功能

1. 阅读架构文档
2. 理解编排器系统
3. 自定义 Skills
4. 开发新工具

## 💡 最佳实践

### 1. 路径使用

```bash
# ✅ 使用完整相对路径
backend/config/llm_config.yaml
backend/daoyoucode/agents/core/agent.py

# ❌ 不要使用不完整路径
config/llm_config.yaml
agents/core/agent.py
```

### 2. Skill 选择

```bash
# 日常对话 → chat-assistant
daoyoucode chat "解释这段代码"

# 复杂任务 → sisyphus-orchestrator
daoyoucode chat --skill sisyphus-orchestrator "重构并测试"

# 只读分析 → oracle 或 librarian
daoyoucode chat --skill oracle "分析架构"
```

### 3. 模型选择

```bash
# 复杂任务 → qwen-max
daoyoucode chat --model qwen-max

# 简单任务 → qwen-plus
daoyoucode chat --model qwen-plus

# 快速响应 → qwen-turbo
daoyoucode chat --model qwen-turbo
```

### 4. 文件管理

```bash
# 加载关键文件
daoyoucode chat backend/ARCHITECTURE.md backend/README.md

# 对话中添加文件
/add backend/config/llm_config.yaml

# 查看已加载文件
/files
```

## 🔗 相关链接

- **项目仓库**: (你的仓库地址)
- **文档**: `docs/`
- **Issues**: (你的 Issues 地址)
- **通义千问**: https://dashscope.aliyuncs.com/

## 📞 获取帮助

### 命令行帮助

```bash
daoyoucode --help
daoyoucode chat --help
```

### 对话中帮助

```
/help
```

### 文档

查看 `backend/` 目录下的各种 `.md` 文档

### 测试

运行测试验证功能：

```bash
cd backend
pytest tests/ -v
```

## 🎉 快速示例

### 示例 1: 修改配置

```bash
daoyoucode chat "修改 backend/config/llm_config.yaml，将 temperature 从 0.7 改为 0.5"
```

### 示例 2: 分析代码

```bash
daoyoucode chat --skill oracle "分析 backend/daoyoucode/agents/core/ 的设计模式"
```

### 示例 3: 搜索功能

```bash
daoyoucode chat --skill librarian "找到所有使用 asyncio 的代码"
```

### 示例 4: 重构代码

```bash
daoyoucode chat --skill refactoring "重构 backend/cli/commands/chat.py，提取重复代码"
```

### 示例 5: 生成测试

```bash
daoyoucode chat --skill testing "为 backend/daoyoucode/agents/tools/file_tools.py 生成单元测试"
```

---

**提示**: 这是一个快速参考，详细信息请查看各个文档文件。
