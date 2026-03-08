# Skills 目录说明

## 核心 Skills (6个)

### 1. sisyphus-orchestrator
**用途**: 全能编排器，支持所有功能

**特点**:
- 包含 13 个工作流
- 支持代码分析、编写、测试、重构等所有功能
- 默认 Skill，适合大多数场景

**使用场景**:
- 不确定用哪个 Skill 时的默认选择
- 需要多种功能组合的复杂任务
- 需要智能意图识别和工作流切换

**配置**:
- 编排器: core
- 工作流: 13 个（自有）
- 权限: 读写
- 工具: 全部

---

### 2. programming
**用途**: 专注于代码开发

**特点**:
- 专注于编写新代码
- 理解需求并生成实现
- 考虑代码质量和最佳实践

**使用场景**:
- 实现新功能
- 编写新模块
- 生成代码框架

**配置**:
- 编排器: core
- 工作流: 继承自 sisyphus-orchestrator
- 权限: 读写
- 工具: 全部

---

### 3. testing
**用途**: 专注于测试

**特点**:
- 编写单元测试
- 编写集成测试
- 运行和分析测试结果

**使用场景**:
- 为现有代码编写测试
- 修复失败的测试
- 提高测试覆盖率

**配置**:
- 编排器: core
- 工作流: 继承自 sisyphus-orchestrator
- 权限: 读写
- 工具: 全部

---

### 4. refactoring
**用途**: 专注于代码重构

**特点**:
- 改进代码结构
- 优化性能
- 提高可维护性

**使用场景**:
- 重构遗留代码
- 优化代码结构
- 消除代码异味

**配置**:
- 编排器: core
- 工作流: 继承自 sisyphus-orchestrator
- 权限: 读写
- 工具: 全部

---

### 5. code-review
**用途**: 代码审查

**特点**:
- 审查代码质量
- 发现潜在问题
- 提供改进建议

**使用场景**:
- PR 代码审查
- 代码质量检查
- 安全审查

**配置**:
- 编排器: core
- 工作流: 继承自 sisyphus-orchestrator
- 权限: 读写
- 工具: 全部

---

### 6. chat-assistant
**用途**: 普通问答

**特点**:
- 友好的对话助手
- 回答技术问题
- 提供建议和指导

**使用场景**:
- 技术咨询
- 概念解释
- 一般性问答

**配置**:
- 编排器: core
- 工作流: 继承自 sisyphus-orchestrator
- 权限: 读写
- 工具: 全部

---

## 使用方式

### CLI 使用

```bash
# 使用默认 Skill (sisyphus-orchestrator)
daoyoucode chat

# 使用特定 Skill
daoyoucode chat --skill programming
daoyoucode chat --skill testing
daoyoucode chat --skill refactoring
daoyoucode chat --skill code-review
daoyoucode chat --skill chat-assistant
```

### 配置文件

每个 Skill 的配置文件位于 `skills/<skill-name>/skill.yaml`

**配置结构**:
```yaml
name: "skill-name"
version: "1.0.0"
description: "Skill 描述"
orchestrator: "core"

# 工作流配置
workflows:
  source: "sisyphus-orchestrator"  # 继承工作流
  preferred_intents: []             # 可选：过滤工作流

# 项目理解配置
project_understanding:
  level: "medium"  # full/medium/light/none

# 工具配置
tools: []  # 空表示使用所有工具

# LLM 配置
llm:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000
```

---

## 工作流继承

所有 Skills（除了 sisyphus-orchestrator）都继承 sisyphus-orchestrator 的 13 个工作流：

1. **general_chat** - 简单寒暄
2. **need_code_context** - 需要代码上下文
3. **understand_project** - 理解项目
4. **write_code** - 编写代码
5. **write_test** - 编写测试
6. **refactor_code** - 重构代码
7. **run_test** - 运行测试
8. **debug_code** - 调试代码
9. **analyze_code** - 分析代码
10. **find_unused_code** - 查找未使用代码
11. **search_code** - 搜索代码
12. **review_code** - 审查代码
13. **optimize_code** - 优化代码

---

## 添加新 Skill

如果需要添加新的 Skill：

1. 创建目录: `skills/<skill-name>/`
2. 创建配置: `skills/<skill-name>/skill.yaml`
3. 配置继承: `workflows.source: "sisyphus-orchestrator"`
4. 测试验证: `daoyoucode chat --skill <skill-name>`

**最小配置示例**:
```yaml
name: "my-skill"
version: "1.0.0"
description: "我的自定义 Skill"
orchestrator: "core"

workflows:
  source: "sisyphus-orchestrator"

project_understanding:
  level: "medium"

tools: []

llm:
  model: "gpt-4"
  temperature: 0.7
```

---

## 设计原则

1. **专注单一职责**: 每个 Skill 专注于特定领域
2. **继承复用**: 通过继承避免重复配置
3. **配置驱动**: 通过配置文件而不是代码定义行为
4. **简单优先**: 保持最小数量的 Skills，避免过度设计

---

## 已删除的 Skills

以下 Skills 已被删除（功能可通过 sisyphus-orchestrator 实现）：

- code-analysis（分析功能已集成）
- code-exploration（探索功能已集成）
- oracle（咨询功能已集成）
- librarian（文档搜索已集成）
- translation（翻译功能已集成）
- edit-single（编辑功能已集成）
- complex-refactor（重构功能已集成）
- parallel-analysis（分析功能已集成）
- test-core-orchestrator（测试用，已删除）

---

## 维护指南

### 何时添加新 Skill

只在以下情况添加新 Skill：
- 有明确的、独特的使用场景
- 需要特殊的权限配置（如只读）
- 需要特殊的工具集合
- 需要特殊的 LLM 配置

### 何时不添加新 Skill

避免在以下情况添加新 Skill：
- 功能可以通过现有 Skill 实现
- 只是为了组织代码
- 功能重复或相似

### 定期审查

定期审查 Skills 目录：
- 删除不常用的 Skills
- 合并功能相似的 Skills
- 保持 Skills 数量在 5-10 个

---

**最后更新**: 2024-03-08
**维护者**: DaoyouCode Team
