# DaoyouCode Backend 文档

> 完整的参考文档

---

## 📚 文档导航

### 1. [CLI命令参考.md](./CLI命令参考.md)
**CLI使用指南**
- 三层帮助系统（--help, --examples, examples命令）
- 核心命令（chat, agent, skills, examples）
- 使用场景和示例
- 完整命令树

**适合**：
- 新用户快速上手
- 查找命令用法
- 了解CLI功能

---

### 2. [TOOLS工具参考.md](./TOOLS工具参考.md)
**26个工具完整参考**
- 工具总览和快速查找表
- 按场景选择工具
- 核心工具详解
- 工具组合模式
- 性能和安全提示

**适合**：
- 编写Agent Prompt
- 选择合适的工具
- 了解工具能力

---

### 3. [AGENTS智能体介绍.md](./AGENTS智能体介绍.md)
**10个Agent完整介绍**
- Agent总览和对比
- 核心Agent详解（sisyphus, oracle, librarian等）
- Agent选择指南
- Agent协作模式

**适合**：
- 了解Agent能力
- 选择合适的Agent
- 配置Skill

---

### 4. [ORCHESTRATORS编排器介绍.md](./ORCHESTRATORS编排器介绍.md)
**7个编排器完整介绍**
- 编排器总览和对比
- 核心编排器详解（simple, react, multi_agent等）
- 4种协作模式（sequential, parallel, debate, main_with_helpers）
- 编排器选择指南

**适合**：
- 了解编排器能力
- 选择合适的编排器
- 配置复杂任务

---

## 🚀 快速开始

### 1. 查看所有命令
```bash
python backend/daoyoucode.py --help
```

### 2. 查看使用示例
```bash
python backend/daoyoucode.py examples
```

### 3. 启动对话
```bash
# 默认chat模式
python backend/daoyoucode.py chat

# 使用sisyphus编排（复杂任务）
python backend/daoyoucode.py chat --skill sisyphus-orchestrator

# 使用oracle咨询（架构分析）
python backend/daoyoucode.py chat --skill oracle

# 使用librarian搜索（文档查找）
python backend/daoyoucode.py chat --skill librarian
```

---

## 📖 核心概念

### Agent（智能体）
- 执行具体任务的智能体
- 每个Agent有不同的职责和工具集
- 10个内置Agent

### Skill（技能）
- 配置文件，定义使用哪些Agent、工具和编排器
- 12个内置Skill
- 可自定义Skill

### Orchestrator（编排器）
- 负责协调多个Agent的工作方式
- 7个内置编排器
- 支持4种协作模式

### Tool（工具）
- Agent使用的具体功能
- 26个内置工具
- 涵盖文件操作、搜索、Git、LSP、AST等

---

## 🎯 使用场景

### 场景1：日常对话
```bash
python backend/daoyoucode.py chat
```
- Skill: chat-assistant
- Agent: MainAgent
- 编排器: react

### 场景2：复杂任务（重构+测试）
```bash
python backend/daoyoucode.py chat --skill sisyphus-orchestrator
```
- Skill: sisyphus-orchestrator
- Agent: sisyphus + 4个辅助Agent
- 编排器: multi_agent

### 场景3：架构咨询
```bash
python backend/daoyoucode.py chat --skill oracle
```
- Skill: oracle
- Agent: oracle
- 编排器: react
- 特点: 只读，不修改代码

### 场景4：文档搜索
```bash
python backend/daoyoucode.py chat --skill librarian
```
- Skill: librarian
- Agent: librarian
- 编排器: react
- 特点: 只读，专注搜索

---

## 📊 系统架构

```
用户
 ↓
CLI命令
 ↓
Skill配置
 ↓
编排器（Orchestrator）
 ↓
Agent（智能体）
 ↓
工具（Tools）
```

**数据流**：
```
用户输入 → CLI → Skill → 编排器 → Agent → 工具 → 结果
```

**配置流**：
```
Skill配置 → 编排器 → Agent → LLM/工具
```

---

## 🔧 开发指南

### 添加新Agent
参考：[AGENTS智能体介绍.md](./AGENTS智能体介绍.md)

### 添加新工具
参考：[TOOLS工具参考.md](./TOOLS工具参考.md)

### 配置新Skill
参考：[CLI命令参考.md](./CLI命令参考.md)

### 选择编排器
参考：[ORCHESTRATORS编排器介绍.md](./ORCHESTRATORS编排器介绍.md)

---

## 📝 更新日志

### 2025-02-17
- ✅ 整理文档，合并为4个核心文档
- ✅ 添加CLI三层帮助系统
- ✅ 添加examples命令
- ✅ 完善Agent和编排器介绍

---

## 🤝 贡献

欢迎贡献代码和文档！

---

## 📧 联系

如有问题，请提Issue。
