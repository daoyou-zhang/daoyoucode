# Memory系统快速参考

## 🚀 快速开始

### 运行测试

```bash
# 集成测试（验证所有功能）
python backend/test_memory_integration.py

# 实战调试（模拟真实对话）
python backend/test_memory_debug.py

# 持久化测试（验证数据保存）
python backend/test_persistence.py
```

### 数据存储位置

```
Windows: C:\Users\<用户名>\.daoyoucode\memory\
Linux/Mac: ~/.daoyoucode/memory/
```

持久化文件：
- `preferences.json` - 用户偏好（永久保存）
- `tasks.json` - 任务历史（永久保存）
- `summaries.json` - 对话摘要（永久保存）
- `profiles.json` - 用户画像（永久保存）

对话历史存储在内存中（临时），程序重启后清空。

---

## 📖 常用API

### 基础操作

```python
from daoyoucode.agents.memory import get_memory_manager

memory = get_memory_manager()

# 添加对话
memory.add_conversation(session_id, user_msg, ai_msg)

# 获取历史
history = memory.get_conversation_history(session_id, limit=3)

# 用户偏好
memory.remember_preference(user_id, 'language', 'python')
prefs = memory.get_preferences(user_id)

# 任务历史
memory.add_task(user_id, {'agent': 'MainAgent', 'input': '...'})
tasks = memory.get_task_history(user_id, limit=5)
```

### 智能加载

```python
# 判断追问
is_followup, confidence, reason = await memory.is_followup(
    session_id, user_input
)

# 智能加载上下文
context = await memory.load_context_smart(
    session_id=session_id,
    user_id=user_id,
    user_input=user_input,
    is_followup=is_followup,
    confidence=confidence
)

# 使用上下文
history = context['history']        # 加载的对话历史
summary = context.get('summary')    # 对话摘要（如果有）
profile = context.get('profile')    # 用户画像（如果有）
strategy = context['strategy']      # 使用的策略
cost = context['cost']              # 成本（相对值）
```

### 长期记忆

```python
# 检查是否应该生成摘要
should_generate = memory.long_term_memory.should_generate_summary(
    session_id, current_round
)

# 生成摘要（需要LLM客户端）
summary = await memory.long_term_memory.generate_summary(
    session_id, history, llm_client
)

# 获取摘要
summary = memory.long_term_memory.get_summary(session_id)

# 构建用户画像
profile = await memory.long_term_memory.build_user_profile(
    user_id, all_sessions
)

# 获取用户画像
profile = memory.long_term_memory.get_user_profile(user_id)
```

### 统计信息

```python
# 智能加载统计
loader_stats = memory.smart_loader.get_stats()
print(f"总加载次数: {loader_stats['total_loads']}")
print(f"平均成本: {loader_stats['average_cost']}")

# 存储统计
storage_stats = memory.storage.get_stats()
print(f"总会话数: {storage_stats['total_sessions']}")
print(f"总对话数: {storage_stats['total_conversations']}")
```

---

## 🎯 智能加载策略

| 策略 | 触发条件 | 加载内容 | 成本 |
|------|---------|---------|------|
| new_conversation | 首轮对话 | 无 | 0 |
| simple_followup | 简单追问 | 最近2轮 | 1 |
| medium_followup | 中等追问 | 最近3轮 | 2 |
| complex_followup | 复杂追问 | 摘要+2轮 | 3 |
| cross_session | 跨会话 | 向量检索 | 4 |

---

## 🔍 调试技巧

### 启用详细日志

```python
import logging

# 方法1：全局DEBUG
logging.basicConfig(level=logging.DEBUG)

# 方法2：只启用Memory日志
logging.getLogger('daoyoucode.agents.memory').setLevel(logging.DEBUG)
```

### 关键日志标识

```
📊 - 策略决策
📦 - 上下文构建
🌳 - 智能筛选
🔄 - 摘要生成
📚 - 智能加载
📝 - 加载摘要
👤 - 加载画像
```

### 追踪特定场景

```python
# 在代码中添加调试输出
print(f"\n🔍 调试信息:")
print(f"  策略: {context['strategy']}")
print(f"  历史: {len(context['history'])}轮")
print(f"  成本: {context['cost']}")
print(f"  筛选: {'是' if context.get('filtered') else '否'}")
```

---

## 🐛 常见问题

### Q1: 智能加载没有生效？

**检查**：
```python
# 确保传递了追问判断
context = await memory.load_context_smart(
    ...,
    is_followup=is_followup,  # 必须传递
    confidence=confidence      # 必须传递
)
```

### Q2: 摘要没有生成？

**原因**：
- 对话轮数 < 5
- LLM客户端未配置
- 没有调用生成方法

**解决**：
```python
# 检查触发条件
history = memory.get_conversation_history(session_id)
should_generate = memory.long_term_memory.should_generate_summary(
    session_id, len(history)
)
print(f"应该生成摘要: {should_generate}")
```

### Q3: 向量检索报错？

**原因**：依赖未安装（默认禁用）

**解决**：
```bash
# 方案1：安装依赖
pip install sentence-transformers

# 方案2：保持禁用（推荐）
# 向量检索默认禁用，不影响其他功能
```

---

## 📊 性能监控

### Token使用估算

```python
# 估算历史token数（粗略：4字符=1token）
history_tokens = sum(
    len(h['user']) + len(h['ai'])
    for h in context['history']
) // 4

print(f"历史tokens: {history_tokens}")
```

### 策略分布

```python
stats = memory.smart_loader.get_stats()

for strategy in ['new_conversation', 'simple_followup', 
                 'medium_followup', 'complex_followup']:
    count = stats.get(strategy, 0)
    if count > 0:
        percentage = count / stats['total_loads'] * 100
        print(f"{strategy}: {count} ({percentage:.1f}%)")
```

---

## ⚙️ 配置调整

### 调整加载策略

编辑 `backend/daoyoucode/agents/memory/smart_loader.py`：

```python
self.strategies = {
    'simple_followup': {
        'history_limit': 2,  # 改为3可以加载更多历史
        'cost': 1
    },
    'medium_followup': {
        'history_limit': 3,  # 改为4可以加载更多历史
        'cost': 2
    },
    # ...
}
```

### 调整摘要触发

编辑 `backend/daoyoucode/agents/memory/long_term_memory.py`：

```python
self.summary_interval = 5  # 改为10可以减少摘要生成频率
self.summary_min_messages = 3  # 最少对话轮数
```

---

## 📁 文件位置

```
backend/
├── daoyoucode/agents/memory/
│   ├── manager.py              # 统一管理器
│   ├── storage.py              # 存储层
│   ├── smart_loader.py         # 智能加载
│   ├── long_term_memory.py     # 长期记忆
│   ├── vector_retriever.py     # 向量检索
│   ├── detector.py             # 追问检测
│   └── shared.py               # 多智能体共享
│
├── test_memory_integration.py  # 集成测试
├── test_memory_debug.py        # 实战调试
│
└── 文档/
    ├── MEMORY_MIGRATION_COMPLETE.md      # 迁移完成
    ├── MEMORY_INTEGRATION_SUCCESS.md     # 集成成功
    ├── MEMORY_DEBUG_GUIDE.md             # 调试指南
    └── MEMORY_QUICK_REFERENCE.md         # 快速参考（本文档）
```

---

## 🎯 使用建议

1. **日常使用**：无需修改，Agent已自动集成
2. **调试问题**：启用DEBUG日志，查看决策过程
3. **性能监控**：定期检查统计信息
4. **配置优化**：根据实际使用调整策略参数

---

## 💡 提示

- 智能加载会自动选择最优策略，无需手动干预
- 摘要生成每5轮自动触发，无需手动调用
- 向量检索默认禁用，不影响其他功能
- 所有功能向后兼容，旧代码仍然可用

---

## 📞 获取帮助

- 查看详细文档：`MEMORY_DEBUG_GUIDE.md`
- 运行测试验证：`python backend/test_memory_integration.py`
- 实战调试：`python backend/test_memory_debug.py`
- 查看日志：启用DEBUG级别日志

---

**最后更新**: 2026-02-15
