# LLM模块架构规范

> **项目**: daoyoucode  
> **模块**: LLM核心模块  
> **状态**: 📝 规范定义阶段  
> **优先级**: ⭐⭐⭐⭐⭐ 核心模块

---

## 📚 文档导航

### 核心文档（按阅读顺序）

1. **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 实施计划 ⭐⭐⭐⭐⭐
   - 唯一实施指南
   - 任务清单和进度
   - 当前状态

2. **[architecture-review.md](architecture-review.md)** - 架构评审 ⭐⭐⭐⭐
   - 设计问题分析
   - 改进建议
   - 代码示例

3. **[requirements.md](requirements.md)** - 需求规范 ⭐⭐⭐
   - 功能需求
   - 非功能需求
   - 验收标准

---

## 🎯 项目目标

设计并实现daoyoucode的核心LLM模块，融合四个来源的最佳实践：

1. **现有ai模块** - Skill插入模式、记忆功能、上下文检索
2. **daoyouCodePilot** - 中文优化、国产LLM深度集成
3. **oh-my-opencode** - 多智能体编排、Hook系统
4. **OpenCode** - 模型无关架构、插件系统

---

## 🏗️ 架构概览

```
用户请求
    ↓
AI编排器 (Orchestrator)
    ↓
智能体层 (13个专业智能体)
    ↓
Skill系统 (配置驱动)
    ↓
上下文管理 (记忆 + 追问判断)
    ↓
LLM客户端池 (连接复用)
    ↓
LLM客户端 (多提供商支持)
    ↓
外部LLM服务
```

---

## ✨ 核心特性

### 1. 多LLM提供商支持
- 通义千问系列（qwen-max, qwen-plus, qwen-turbo, qwen-coder-plus）
- DeepSeek系列（deepseek-chat, deepseek-coder）
- Claude系列（claude-opus-4-5, claude-sonnet-4-5）
- GPT系列（gpt-5.2, gpt-4o）
- Gemini系列（gemini-3-pro, gemini-3-flash）
- 本地模型（Ollama, LM Studio）

### 2. 连接池管理
- 连接复用率 ≥ 95%
- 自动健康检查
- 空闲连接回收
- 统计信息收集

### 3. Skill系统
- YAML + Markdown配置驱动
- 完整模式 + 追问模式
- Token节省率 ≥ 44%
- 易于扩展

### 4. 智能上下文管理
- 三层瀑布式追问判断（准确率 ≥ 92%）
- 短期记忆 + 长期记忆
- 对话树结构
- 智能压缩和摘要

### 5. 多智能体协作
- 13个专业智能体
- 并行执行
- 任务委托
- 结果聚合

### 6. Hook系统
- 25+ 内置Hooks
- 事件驱动
- 自定义Hook支持
- 优先级控制

### 7. 智能模型选择
- 基于任务类型
- 基于语言（中文优先）
- 基于复杂度
- 成本优化

---

## 📊 性能指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| LLM响应时间 | < 3秒 | - |
| 流式首字节 | < 500ms | - |
| 并发支持 | ≥ 100 QPS | - |
| 连接复用率 | ≥ 95% | - |
| 追问判断准确率 | ≥ 92% | - |
| Token节省率 | ≥ 44% | - |
| 单元测试覆盖率 | ≥ 80% | - |

---

## 📅 实施计划

### 阶段1: 基础架构（2周）
- [ ] 创建目录结构
- [ ] 实现基础接口
- [ ] 实现统一LLM客户端
- [ ] 实现连接池管理
- [ ] 单元测试

### 阶段2: Skill系统（1周）
- [ ] 实现Skill加载器
- [ ] 实现Skill执行器
- [ ] 实现模板引擎
- [ ] 创建示例Skills
- [ ] 单元测试

### 阶段3: 上下文管理（1周）
- [ ] 实现上下文管理器
- [ ] 实现追问判断
- [ ] 实现短期/长期记忆
- [ ] 实现对话树
- [ ] 单元测试

### 阶段4: 智能体系统（1-2周）
- [ ] 实现基础智能体框架
- [ ] 实现5个核心智能体
- [ ] 实现智能体协作
- [ ] 实现任务路由器
- [ ] 集成测试

### 阶段5: Hook系统（1周）
- [ ] 实现Hook管理器
- [ ] 实现10个核心Hooks
- [ ] Hook配置管理
- [ ] 单元测试

### 阶段6: 集成和优化（1周）
- [ ] 端到端集成测试
- [ ] 性能优化
- [ ] 成本优化
- [ ] 文档完善
- [ ] 部署准备

**总计**: 6-8周

---

## 📁 目录结构

```
backend/daoyoucode/llm/
├── __init__.py
├── base.py                    # 基础接口
├── orchestrator.py            # AI编排器
├── router.py                  # 任务路由
├── model_selector.py          # 模型选择
│
├── clients/                   # LLM客户端
│   ├── base.py
│   ├── unified.py
│   ├── qwen.py
│   ├── deepseek.py
│   ├── claude.py
│   └── openai.py
│
├── pool/                      # 连接池
│   ├── client_pool.py
│   ├── health_checker.py
│   └── stats_collector.py
│
├── agents/                    # 智能体
│   ├── base.py
│   ├── sisyphus.py
│   ├── chinese_editor.py
│   └── ...
│
├── skills/                    # Skill系统
│   ├── loader.py
│   ├── executor.py
│   └── registry.py
│
├── context/                   # 上下文管理
│   ├── manager.py
│   ├── followup_detector.py
│   ├── intent_tree.py
│   └── bm25_matcher.py
│
├── hooks/                     # Hook系统
│   ├── manager.py
│   ├── base.py
│   └── builtin/
│
└── utils/                     # 工具函数
    ├── token_counter.py
    ├── cost_calculator.py
    └── logger.py
```

---

## 🔗 参考资料

### 现有ai模块
- `ai/orchestrator.py`
- `ai/llm_client_pool.py`
- `ai/skill_loader.py`
- `ai/unified_matcher.py`
- `ai/docs/01_LLM_ARCHITECTURE.md`
- `ai/docs/02_CONTEXT_MATCHING.md`

### 参考项目
- **daoyouCodePilot**: `daoyouCodePilot/daoyou/core/llm/`
- **oh-my-opencode**: `oh-my-opencode/src/agents/`
- **OpenCode**: `opencode/packages/opencode/`

---

## ✅ 验收标准

### 功能验收
- [ ] 支持所有列出的LLM提供商
- [ ] 连接池正常工作
- [ ] Skill系统可配置化
- [ ] 追问判断准确率达标
- [ ] 智能体协作正常
- [ ] Hook系统工作正常

### 性能验收
- [ ] 响应时间达标
- [ ] 并发支持达标
- [ ] Token节省率达标

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] 性能测试通过
- [ ] 代码审查通过
- [ ] 文档完整

---

## 🚀 后续扩展

### Phase 2: Tool & MCP集成（3-4周）
- MCP协议集成
- 工具注册与发现
- 工具链编排

### Phase 3: Memory系统（3-4周）
- 知识图谱
- 记忆检索与更新
- 跨会话信息关联

### Phase 4: Knowledge Base（3-4周）
- RAG检索增强生成
- 向量化与索引
- 混合检索

### Phase 5: 推理与规划（3-4周）
- ReAct模式
- Chain-of-Thought
- 多步骤规划

---

## 📞 联系方式

- **负责人**: AI Team
- **创建日期**: 2026-02-10
- **最后更新**: 2026-02-10
- **版本**: v1.0

---

## 📝 变更日志

### v1.0 (2026-02-10)
- 初始版本
- 完成需求规范
- 完成设计文档
- 完成实施指南

---

**开始阅读**: 建议从 [requirements.md](requirements.md) 开始，了解完整需求和验收标准。
