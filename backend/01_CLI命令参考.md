# CLI命令参考

> DaoyouCode CLI完整使用指南

---

## 快速开始

```bash
# 查看所有命令
python backend/daoyoucode.py --help

# 查看使用示例
python backend/daoyoucode.py examples

# 启动对话
python backend/daoyoucode.py chat --skill <skill_name>
```

---

## 三层帮助系统

### Level 1: --help（快速参考）
显示命令参数和选项
```bash
python backend/daoyoucode.py chat --help
```

### Level 2: --examples（详细示例）
显示使用示例和最佳实践
```bash
python backend/daoyoucode.py chat --examples
```

### Level 3: examples命令（全局视图）
显示所有命令概览
```bash
python backend/daoyoucode.py examples
```

---

## 核心命令

### 1. chat - 启动对话

```bash
# 基本用法
python backend/daoyoucode.py chat

# 指定Skill
python backend/daoyoucode.py chat --skill sisyphus-orchestrator
python backend/daoyoucode.py chat --skill oracle
python backend/daoyoucode.py chat --skill librarian

# 指定模型
python backend/daoyoucode.py chat --model deepseek-coder

# 加载文件
python backend/daoyoucode.py chat main.py utils.py

# 组合使用
python backend/daoyoucode.py chat --skill oracle --model qwen-max main.py
```

**参数**：
- `--skill, -s` - 使用的Skill（默认：chat-assistant）
  - **注意**：传的是Skill名称，不是Agent名称！
  - Skill配置文件指定使用哪些Agent和编排器
- `--model, -m` - 使用的模型（默认：qwen-max）
- `--repo, -r` - 仓库路径（默认：.）
- `--examples` - 显示使用示例

**Skill、Agent、编排器的关系**：
```
CLI --skill sisyphus-orchestrator
    ↓
Skill配置文件（skills/sisyphus-orchestrator/skill.yaml）
    ↓
指定编排器：orchestrator: multi_agent
指定Agent列表：agents: [sisyphus, code_analyzer, programmer, ...]
    ↓
编排器协调这些Agent工作
```

**交互式命令**：
- `/skill [name]` - 切换Skill
- `/model [name]` - 切换模型
- `/add <file>` - 添加文件
- `/help` - 显示帮助
- `/exit` - 退出对话

---

### 2. agent - Agent管理

```bash
# 列出所有Agent
python backend/daoyoucode.py agent

# 查看Agent详情
python backend/daoyoucode.py agent sisyphus

# 查看Agent工具
python backend/daoyoucode.py agent sisyphus --tools
```

**参数**：
- `agent_name` - Agent名称（可选）
- `--tools, -t` - 显示Agent的工具列表
- `--examples` - 显示使用示例

---

### 3. skills - Skill管理

```bash
# 列出所有Skill
python backend/daoyoucode.py skills

# 查看Skill详情
python backend/daoyoucode.py skills sisyphus-orchestrator

# 查看所有编排器
python backend/daoyoucode.py skills --orchestrators
```

**参数**：
- `skill_name` - Skill名称（可选）
- `--orchestrators, -o` - 显示编排器列表和说明
- `--examples` - 显示使用示例

---

### 4. examples - 查看示例

```bash
# 查看所有示例
python backend/daoyoucode.py examples

# 查看特定命令示例
python backend/daoyoucode.py examples chat
python backend/daoyoucode.py examples agent
python backend/daoyoucode.py examples skills
```

---

## 使用场景

### 场景1：了解系统
```bash
python backend/daoyoucode.py agent                    # 查看所有Agent
python backend/daoyoucode.py skills                   # 查看所有Skill
python backend/daoyoucode.py skills --orchestrators   # 查看编排器
```

### 场景2：日常对话
```bash
python backend/daoyoucode.py chat
```

### 场景3：复杂任务
```bash
python backend/daoyoucode.py chat --skill sisyphus-orchestrator
```

### 场景4：架构咨询
```bash
python backend/daoyoucode.py chat --skill oracle
```

### 场景5：文档搜索
```bash
python backend/daoyoucode.py chat --skill librarian
```

### 场景6：交互式切换
```bash
python backend/daoyoucode.py chat
你 › /skill oracle
你 › 分析架构
```

---

## 完整命令树

```
daoyoucode
├── chat [OPTIONS] [FILES]               # 启动对话
│   ├── --skill TEXT                     # 指定Skill
│   ├── --model TEXT                     # 指定模型
│   ├── --repo PATH                      # 指定仓库
│   └── --examples                       # 查看示例
│
├── agent [name] [--tools] [--examples]  # Agent管理
│   ├── agent                            # 列出所有Agent
│   ├── agent <name>                     # 查看Agent详情
│   └── agent <name> --tools             # 查看Agent工具
│
├── skills [name] [--orchestrators] [--examples]  # Skill管理
│   ├── skills                           # 列出所有Skill
│   ├── skills <name>                    # 查看Skill详情
│   └── skills --orchestrators           # 查看编排器
│
├── examples [command]                   # 查看示例
│   ├── examples                         # 所有示例
│   ├── examples chat                    # chat示例
│   ├── examples agent                   # agent示例
│   └── examples skills                  # skills示例
│
├── models                               # 查看模型
├── doctor [--fix]                       # 系统诊断
├── config                               # 配置管理
├── session                              # 会话管理
└── version                              # 查看版本
```

---

## 推荐Skill

| Skill | 编排器 | 用途 | 使用场景 |
|-------|--------|------|---------|
| chat-assistant | react | 日常对话 | 代码咨询、问题解答 |
| sisyphus-orchestrator | multi_agent | 复杂任务 | 重构+测试、多文件修改 |
| oracle | react | 架构咨询 | 架构分析、技术建议（只读） |
| librarian | react | 文档搜索 | 文档查找、代码搜索（只读） |
| programming | simple | 编程专家 | 代码编写、功能实现 |
| refactoring | simple | 重构专家 | 代码重构、优化 |
| testing | simple | 测试专家 | 测试编写、修复 |

---

## 相关文档

- [AGENTS.md](./AGENTS.md) - Agent详细介绍
- [ORCHESTRATORS.md](./ORCHESTRATORS.md) - 编排器详细介绍
- [TOOLS.md](./TOOLS.md) - 工具参考手册
