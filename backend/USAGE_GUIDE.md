# DaoyouCode 使用指南

## 快速开始

### 1. 安装依赖（首次使用）

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装项目（包含所有依赖）
pip install -e .
```

### 2. 配置 API 密钥

编辑 `backend/config/llm_config.yaml`，填入你的 API 密钥：

```yaml
providers:
  qwen:
    api_key: ["你的-API-密钥"]  # 支持多个密钥轮询
    enabled: true
```

### 3. 在其他项目中使用

**不需要特意启动任何服务！** 直接在任何项目目录下运行：

```bash
# 方式 1: 使用完整路径
D:\daoyouspace\daoyoucode\backend\venv\Scripts\daoyoucode.exe chat

# 方式 2: 激活虚拟环境后使用
cd D:\daoyouspace\daoyoucode\backend
.\venv\Scripts\activate
cd D:\your-other-project
daoyoucode chat

# 方式 3: 添加到系统 PATH（推荐）
# 将 D:\daoyouspace\daoyoucode\backend\venv\Scripts 添加到系统 PATH
# 然后在任何地方直接使用
daoyoucode chat
```

## LSP 服务说明

### 自动启动机制

LSP 服务器会在需要时**自动启动**，无需手动管理：

1. **首次使用时启动**
   - 当你使用需要代码分析的功能时（如诊断、跳转定义等）
   - LSP 服务器会自动在后台启动
   - 启动后会保持运行，供后续请求复用

2. **自动管理**
   - 空闲 10 分钟后自动清理
   - 进程死亡时自动重启
   - 多个请求共享同一个服务器实例

3. **无需手动操作**
   - 不需要运行 `lsp_health_check.py`（除非排查问题）
   - 不需要手动启动/停止服务
   - 不需要配置环境变量

### LSP 功能

当 LSP 服务可用时，DaoyouCode 会自动提供：

- ✅ 代码诊断（错误、警告）
- ✅ 跳转到定义
- ✅ 查找引用
- ✅ 符号搜索
- ✅ 代码重命名
- ✅ 代码操作（快速修复）
- ✅ Hover 信息（类型、文档）

### 检查 LSP 状态（可选）

如果遇到问题，可以运行健康检查：

```bash
cd D:\daoyouspace\daoyoucode\backend
.\venv\Scripts\activate
python lsp_health_check.py

# 如果有问题，运行修复
python lsp_health_check.py --fix
```

## 常用命令

### 交互式对话

```bash
# 基本对话
daoyoucode chat

# 指定文件
daoyoucode chat file1.py file2.py

# 指定模型
daoyoucode chat --model qwen-plus

# 指定技能
daoyoucode chat --skill programming
```

### 编辑文件

```bash
# 编辑单个文件
daoyoucode edit file.py "添加类型注解"

# 编辑多个文件
daoyoucode edit file1.py file2.py "重构代码"
```

### 查看技能

```bash
# 列出所有可用技能
daoyoucode skills

# 查看技能详情
daoyoucode skills --detail chat-assistant
```

### 配置管理

```bash
# 查看配置
daoyoucode config show

# 设置默认模型
daoyoucode config set default_model qwen-max
```

## 工作流程示例

### 场景 1: 分析新项目

```bash
# 1. 进入项目目录
cd /path/to/your-project

# 2. 启动对话
daoyoucode chat

# 3. 在对话中使用
> 分析这个项目的架构
> 找出所有的 TODO 注释
> 检查代码质量问题
```

### 场景 2: 代码重构

```bash
# 1. 指定要重构的文件
daoyoucode chat src/main.py

# 2. 使用重构技能
daoyoucode chat --skill refactoring src/main.py

# 3. 在对话中
> 将这个函数拆分成多个小函数
> 添加类型注解
> 优化性能
```

### 场景 3: 编写测试

```bash
# 使用测试技能
daoyoucode chat --skill testing src/utils.py

# 在对话中
> 为这个模块生成单元测试
> 添加边界条件测试
> 生成测试覆盖率报告
```

## 配置文件位置

```
backend/
├── config/
│   ├── llm_config.yaml          # LLM API 配置（必须）
│   ├── agent_router_config.yaml # Agent 路由配置
│   └── embedding_config.yaml    # 向量配置（使用 API 可忽略）
├── .env.example                 # 环境变量示例（备用）
└── venv/                        # 虚拟环境
```

## 故障排查

### 问题 1: 命令找不到

```bash
# 确认安装
pip show daoyoucode

# 重新安装
pip install -e .

# 检查命令
which daoyoucode  # Linux/Mac
where daoyoucode  # Windows
```

### 问题 2: API 密钥错误

```bash
# 检查配置文件
cat backend/config/llm_config.yaml

# 确认密钥格式正确
# 单个密钥: api_key: "sk-xxx"
# 多个密钥: api_key: ["sk-xxx", "sk-yyy"]
```

### 问题 3: LSP 不工作

```bash
# 运行健康检查
python lsp_health_check.py

# 查看详细日志
daoyoucode chat --verbose
```

### 问题 4: 虚拟环境问题

```bash
# 删除旧环境
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 重新创建
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

## 最佳实践

### 1. 使用虚拟环境

始终在虚拟环境中运行，避免依赖冲突：

```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. 配置多个 API 密钥

支持密钥轮询，避免速率限制：

```yaml
qwen:
  api_key: ["key1", "key2", "key3"]
```

### 3. 选择合适的模型

- `qwen-max`: 最强能力，适合复杂任务
- `qwen-plus`: 平衡性能和成本
- `qwen-turbo`: 快速响应，简单任务

### 4. 使用合适的技能

- `chat-assistant`: 通用对话
- `programming`: 编程任务
- `refactoring`: 代码重构
- `testing`: 测试生成
- `code-review`: 代码审查

## 进阶功能

### 自定义技能

在 `skills/` 目录下创建新技能：

```yaml
# skills/my-skill/skill.yaml
name: my-skill
description: 我的自定义技能
agent: main_agent
orchestrator: simple
tools:
  - read_file
  - write_file
```

### 集成到 IDE

可以通过 LSP 协议集成到任何支持的 IDE：

- VS Code
- PyCharm
- Vim/Neovim
- Emacs

### API 模式

启动 HTTP API 服务器：

```bash
daoyoucode serve --port 8000
```

然后通过 HTTP 调用：

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "分析这个项目"}'
```

## 总结

**核心要点：**

1. ✅ 首次安装后，在任何项目中直接使用 `daoyoucode` 命令
2. ✅ LSP 服务会自动启动和管理，无需手动操作
3. ✅ 配置 API 密钥后即可使用
4. ✅ 遇到问题时运行健康检查工具

**不需要：**
- ❌ 手动启动 LSP 服务
- ❌ 每次使用前运行检查脚本
- ❌ 在每个项目中重复安装
- ❌ 配置复杂的环境变量

直接使用即可！🚀
