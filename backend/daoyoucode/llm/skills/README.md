# Skill系统

Skill系统提供了灵活的LLM能力封装和管理机制，支持多种Skill格式，提供完整的加载、执行、监控功能。

## 核心特性

- **多格式支持**: 兼容YAML、OpenCode Markdown等多种Skill格式
- **双模式执行**: 完整模式（首次调用）和追问模式（节省tokens）
- **智能管理**: 版本管理、热更新、优先级控制
- **高可用**: 集成限流、熔断、降级策略
- **全面监控**: 执行统计、性能分析、告警检查

## 快速开始

### 1. 加载Skill

```python
from daoyoucode.llm.skills import get_skill_loader

# 初始化加载器
loader = get_skill_loader()

# 加载所有Skill
skills = loader.load_all_skills()

# 获取特定Skill
skill = loader.get_skill("documentation")
```

### 2. 执行Skill

```python
from daoyoucode.llm.skills import get_skill_executor

# 初始化执行器
executor = get_skill_executor()

# 完整模式执行
context = {
    'user_message': '帮我写一个README文档',
    'content_type': 'README'
}

result = await executor.execute(skill, context, user_id=123)
print(result['document'])

# 追问模式执行（节省tokens）
followup_context = {
    'user_message': '再加上安装说明'
}

history_context = {
    'summary': '之前生成了README的基础结构'
}

result = await executor.execute_followup(
    skill,
    followup_context,
    history_context,
    user_id=123
)
```

### 3. 监控Skill

```python
from daoyoucode.llm.skills import get_skill_monitor

# 获取监控器
monitor = get_skill_monitor()

# 查看统计信息
stats = monitor.get_stats()
print(f"总执行次数: {stats['total_executions']}")
print(f"成功率: {stats['successful_executions'] / stats['total_executions']:.2%}")

# 查看热门Skill
top_skills = monitor.get_top_skills(limit=5)
for skill in top_skills:
    print(f"{skill['name']}: {skill['executions']}次")

# 查看性能报告
report = monitor.get_performance_report(time_range=3600)  # 最近1小时
print(f"平均耗时: {report['avg_duration']:.2f}s")
print(f"平均成本: ¥{report['avg_cost']:.4f}")

# 检查告警
alerts = monitor.check_alerts()
for alert in alerts:
    print(f"[{alert['severity']}] {alert['message']}")
```

## Skill格式

### YAML格式（推荐）

```yaml
# skill.yaml
name: my_skill
version: "1.0.0"
description: "我的Skill描述"

triggers:
  keywords:
    - "关键词1"
    - "关键词2"

llm:
  model: qwen-max
  temperature: 0.7
  max_tokens: 2000

inputs:
  - name: user_message
    type: string
    required: true

outputs:
  - name: response
    type: string
```

```markdown
<!-- prompt.md -->
你是一个专业的助手。

用户消息: {{ user_message }}

请提供专业的回复。
```

### OpenCode Markdown格式

```markdown
---
description: My skill description
model: qwen-max
temperature: 0.7
---

You are a professional assistant.

User message: {{ user_message }}

Please provide a professional response.
```

## 目录结构

```
skills/
├── loader.py          # Skill加载器
├── executor.py        # Skill执行器
├── monitor.py         # Skill监控器
├── __init__.py        # 导出接口
├── examples/          # 示例Skills
│   ├── documentation/ # 文档编写Skill
│   └── code_review/   # 代码审查Skill
└── README.md          # 本文档
```

## 高级特性

### 1. 热更新

```python
# 重新加载Skill
loader.reload_skill("my_skill")
```

### 2. 搜索Skill

```python
# 按关键词搜索
results = loader.search_skills("文档")
for skill in results:
    print(f"{skill.name}: {skill.description}")
```

### 3. 自定义后处理

```yaml
# skill.yaml
post_process:
  - validate_output
  - save_to_database
```

### 4. 输出验证

```yaml
outputs:
  - name: status
    type: enum
    values: [ok, error, pending]
```

## 最佳实践

1. **命名规范**: 使用小写字母和下划线，如 `code_review`
2. **版本管理**: 使用语义化版本号，如 `1.0.0`
3. **Prompt设计**: 清晰的角色定义和任务描述
4. **输入验证**: 标记必需参数，提供类型信息
5. **追问优化**: 合理使用追问模式节省tokens
6. **监控告警**: 定期检查性能指标和告警

## 示例Skills

### documentation Skill

专业的技术文档编写助手，遵循最佳实践。

```python
skill = loader.get_skill("documentation")
result = await executor.execute(skill, {
    'user_message': '写一个API文档',
    'content_type': 'API'
})
```

### code_review Skill

代码审查专家，提供质量、安全、性能建议。

```python
skill = loader.get_skill("code_review")
result = await executor.execute(skill, {
    'code': '...',
    'language': 'python',
    'focus_areas': ['security', 'performance']
})
```

## 测试

运行Skill系统测试：

```bash
cd backend
python -m pytest tests/llm/skills/ -v
```

测试覆盖：
- Skill加载器: 10个测试
- Skill执行器: 12个测试
- Skill监控器: 14个测试
- 总计: 36个测试

## 性能指标

- **加载速度**: <100ms（单个Skill）
- **执行延迟**: 取决于LLM响应时间
- **追问优化**: tokens节省50%+
- **监控开销**: <1ms（记录单次执行）

## 故障排查

### Skill加载失败

1. 检查 `skill.yaml` 格式是否正确
2. 确认必需字段（name、version、description）
3. 验证 `prompt.md` 文件存在

### 执行超时

1. 检查网络连接
2. 调整 `timeout` 参数
3. 查看熔断器状态

### 成功率低

1. 查看监控告警
2. 检查Prompt设计
3. 验证输入参数

## 更多信息

- [LLM模块文档](../README.md)
- [实施计划](../../../../.kiro/specs/llm-module-architecture/IMPLEMENTATION_PLAN.md)
- [架构评审](../../../../.kiro/specs/llm-module-architecture/architecture-review.md)
