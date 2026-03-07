# DaoYouCode 文档索引

## 📚 文档结构

### 🏗️ 架构文档 (architecture/)

理解系统核心机制和架构设计

- **TOOL_CALLING_MECHANISM_EXPLAINED.md** - 工具调用机制详解
- **TOOL_RESULT_PASSING_MECHANISM.md** - 工具结果传递机制详解
- **TOOL_CALLING_FLOW_VISUAL.md** - 工具调用流程可视化
- **SISYPHUS_ORCHESTRATION_FLOW.md** - Sisyphus编排流程详解
- **ORCHESTRATOR_COMPARISON.md** - 编排器对比（sisyphus vs chat-assistant）
- **COLLABORATION_MODES_EXPLAINED.md** - 4种协作模式详解
- **CLI_TO_LLM_FLOW_CHECK.md** - CLI到LLM的完整流程
- **LAYERED_STORAGE_IMPLEMENTATION.md** - 分层存储实现

### 🚀 优化文档 (optimization/)

性能优化和功能改进

#### 共享缓存优化
- **SHARED_CACHE_README.md** - 共享缓存快速入门 ⭐ 从这里开始
- **SHARED_CACHE_SUMMARY.md** - 共享缓存功能总结
- **SHARED_CACHE_IMPLEMENTATION.md** - 共享缓存实施细节
- **DUPLICATE_TOOL_CALLS_PROBLEM.md** - 重复工具调用问题分析

#### 编辑工具优化
- **EDIT_TOOLS_GUIDE.md** - 编辑工具使用指南
- **EDIT_TOOLS_OPTIMIZATION_PLAN.md** - 编辑工具优化方案
- **EDIT_TOOLS_PROMPT_SNIPPET.md** - 编辑工具Prompt片段

#### 其他优化
- **PATH_INTELLIGENCE_OPTIMIZATION.md** - 路径智能识别优化
- **INTENT_UNDERSTANDING_OPTIMIZATION.md** - 意图理解优化
- **SMART_TOOL_SELECTION_DESIGN.md** - 智能工具选择设计
- **TOKEN_MANAGEMENT_STRATEGIES.md** - Token管理策略
- **TASK_HISTORY_FIX.md** - 任务历史重复记录修复

### 🧪 测试文档 (testing/)

测试指南和检查清单

- **QUICK_TEST_GUIDE.md** - 快速测试指南 ⭐ 快速验证功能
- **TEST_SHARED_CACHE.md** - 共享缓存完整测试计划
- **IMPLEMENTATION_CHECKLIST.md** - 实施检查清单
- **TEST_COMPLETE_FLOW.md** - 完整流程测试
- **VERIFICATION_REPORT.md** - 共享缓存实现验证报告
- **SISYPHUS_V2_IMPLEMENTATION_COMPLETE.md** - Sisyphus V2 实施完成报告 ⭐ 最新
- **SISYPHUS_V2_TESTING_GUIDE.md** - Sisyphus V2 测试指南 ⭐ 最新

### 📖 指南文档 (guides/)

使用指南和最佳实践

- **PROMPT_BEST_PRACTICES.md** - Prompt最佳实践
- **PROMPT_UPGRADE_GUIDE.md** - Prompt升级指南
- **FILE_PATTERN_EXPLAINED.md** - file_pattern参数说明
- **TOOLS_REFERENCE.md** - 工具参考手册
- **QUICK_REFERENCE.md** - 快速参考
- **GITIGNORE_RULES.md** - Git忽略规则

## 🎯 快速导航

### 新手入门
1. 阅读 `README.md`（根目录）
2. 了解架构：`docs/architecture/ORCHESTRATOR_COMPARISON.md`
3. 快速测试：`docs/testing/QUICK_TEST_GUIDE.md`

### 理解工具调用
1. `docs/architecture/TOOL_CALLING_MECHANISM_EXPLAINED.md` - 基础机制
2. `docs/architecture/TOOL_RESULT_PASSING_MECHANISM.md` - 结果传递
3. `docs/architecture/TOOL_CALLING_FLOW_VISUAL.md` - 可视化流程

### 性能优化
1. `docs/optimization/SHARED_CACHE_README.md` - 共享缓存（推荐）
2. `docs/optimization/TOKEN_MANAGEMENT_STRATEGIES.md` - Token管理
3. `docs/optimization/EDIT_TOOLS_GUIDE.md` - 编辑工具优化

### 开发指南
1. `docs/guides/PROMPT_BEST_PRACTICES.md` - Prompt最佳实践
2. `docs/guides/TOOLS_REFERENCE.md` - 工具参考
3. `CONTRIBUTING.md`（根目录）- 贡献指南

## 📂 根目录保留的文档

### 核心文档
- **README.md** - 项目介绍（中文）
- **README.en.md** - 项目介绍（英文）
- **README.ja.md** - 项目介绍（日文）
- **CONTRIBUTING.md** - 贡献指南
- **LICENSE** - 开源协议

### 项目文档
- **PROJECT_IMPLEMENTATION.md** - 项目实施
- **PROJECT_SHOWCASE.md** - 项目展示
- **AGENT_IMPROVEMENT_PLAN.md** - Agent改进计划
- **DEPENDENCIES_REPORT.md** - 依赖报告
- **daoyoucode_vs_claude_analysis.md** - 对比分析

### 其他
- **完整prompt.md** - 完整Prompt示例
- **hello_world.py** - 示例代码

## 🔍 按主题查找

### 工具调用
- 机制：`docs/architecture/TOOL_CALLING_MECHANISM_EXPLAINED.md`
- 结果传递：`docs/architecture/TOOL_RESULT_PASSING_MECHANISM.md`
- 可视化：`docs/architecture/TOOL_CALLING_FLOW_VISUAL.md`

### 编排器
- 对比：`docs/architecture/ORCHESTRATOR_COMPARISON.md`
- Sisyphus流程：`docs/architecture/SISYPHUS_ORCHESTRATION_FLOW.md`
- 协作模式：`docs/architecture/COLLABORATION_MODES_EXPLAINED.md`

### 性能优化
- 共享缓存：`docs/optimization/SHARED_CACHE_*.md`
- Token管理：`docs/optimization/TOKEN_MANAGEMENT_STRATEGIES.md`
- 编辑工具：`docs/optimization/EDIT_TOOLS_*.md`

### 测试
- 快速测试：`docs/testing/QUICK_TEST_GUIDE.md`
- 完整测试：`docs/testing/TEST_SHARED_CACHE.md`
- 检查清单：`docs/testing/IMPLEMENTATION_CHECKLIST.md`

## 📝 文档更新日志

### 2024-03-07
- 创建文档索引
- 整理文档结构（architecture, optimization, testing, guides）
- 移动所有流程文档到相应目录

---

**提示**：如果找不到某个文档，请查看本索引或使用文件搜索功能。
