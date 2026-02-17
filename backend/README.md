# DaoyouCode Backend 文档

> 完整的参考文档。**代码级快速理解**请先看仓库根目录 [ARCHITECTURE.md](../ARCHITECTURE.md)（一页式架构与 Cursor/aider/DaoyouCode 对比）。

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

### 5. [模型配置架构说明.md](./模型配置架构说明.md) ⭐
**模型配置最佳实践**
- 模型配置应该在Skill配置文件中
- 配置优先级和架构流程
- 代码实现详解
- 常见问题和解决方案

**适合**：
- 配置Skill使用的模型
- 理解模型配置架构
- 解决模型配置问题

---

### 6. [如何配置模型.md](./如何配置模型.md) 🚀
**快速配置指南**
- 3步配置模型
- 常见场景和示例
- 常见错误和解决方案
- 完整示例和检查清单

**适合**：
- 快速上手配置模型
- 查找配置示例
- 解决配置问题

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

### 1. Skill（技能）- CLI传参的对象 ⭐
- **配置文件**，定义使用哪些Agent、工具和编排器
- **CLI通过`--skill`参数指定Skill**
- 12个内置Skill
- 可自定义Skill

**Skill配置示例**：
```yaml
name: sisyphus-orchestrator
orchestrator: multi_agent        # 指定编排器
agents:                          # 指定Agent列表
  - sisyphus
  - code_analyzer
tools:                           # 指定工具列表
  - repo_map
  - read_file
```

### 2. Orchestrator（编排器）- Skill指定的协调者
- 负责协调多个Agent的工作方式
- **由Skill配置文件指定**（orchestrator字段）
- 7个内置编排器
- 支持4种协作模式

### 3. Agent（智能体）- 执行者
- 执行具体任务的智能体
- **由Skill配置文件指定**（agents字段）
- 每个Agent有不同的职责和工具集
- 10个内置Agent

### 4. Tool（工具）- Agent使用的功能
- Agent使用的具体功能
- **由Skill配置文件指定**（tools字段）
- 26个内置工具
- 涵盖文件操作、搜索、Git、LSP、AST等

---

## 🏗️ 架构关系图

```
用户执行命令
 ↓
python daoyoucode.py chat --skill sisyphus-orchestrator
                            ↓
                    Skill配置文件
                    (skills/sisyphus-orchestrator/skill.yaml)
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
  orchestrator:       agents:              tools:
  multi_agent         - sisyphus           - repo_map
                      - code_analyzer      - read_file
                      - programmer         - text_search
                            ↓
                    编排器（Orchestrator）
                    协调Agent工作方式
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
    Agent1              Agent2              Agent3
    (sisyphus)      (code_analyzer)     (programmer)
        ↓                   ↓                   ↓
    使用工具            使用工具            使用工具
        ↓                   ↓                   ↓
                    返回结果给用户
```

**关键点**：
1. ✅ CLI传的是**Skill名称**（不是Agent名称）
2. ✅ Skill配置文件指定使用哪个**编排器**
3. ✅ Skill配置文件指定使用哪些**Agent**
4. ✅ 编排器负责协调Agent的工作方式
5. ✅ Agent使用工具完成具体任务

**编排器的意义**：
- 决定Agent的**协作方式**（顺序、并行、辩论、主从）
- 控制Agent的**执行流程**（重试、超时、回滚）
- 管理Agent的**结果聚合**（如何组合多个Agent的输出）

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
