# Memory系统调试指南

## 🎯 快速开始

### 运行集成测试

```bash
# 在项目根目录运行
python backend/test_memory_integration.py
```

测试会验证：
- ✅ 基础记忆功能
- ✅ 智能加载策略
- ✅ 摘要生成触发
- ✅ 用户画像
- ✅ Agent集成
- ✅ 统计信息

---

## 🔍 调试方法

### 方法1：启用详细日志

```python
import logging

# 设置日志级别为DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 或只启用Memory相关日志
logging.getLogger('daoyoucode.agents.memory').setLevel(logging.DEBUG)
```

### 方法2：使用测试脚本

创建 `test_my_scenario.py`：

```python
import asyncio
import logging
from daoyoucode.agents.memory import get_memory_manager

logging.basicConfig(level=logging.DEBUG)

async def test():
    memory = get_memory_manager()
    
    # 你的测试场景
    session_id = "debug-session"
    user_id = "debug-user"
    
    # 添加对话
    memory.add_conversation(
        session_id,
        "你好",
        "你好！我是DaoyouCode。"
    )
    
    # 智能加载
    context = await memory.load_context_smart(
        session_id=session_id,
        user_id=user_id,
        user_input="这个项目的结构是什么？",
        is_followup=False
    )
    
    print(f"策略: {context['strategy']}")
    print(f"历史: {len(context['history'])}轮")
    print(f"成本: {context['cost']}")

asyncio.run(test())
```

### 方法3：在实际使用中调试

修改 `backend/daoyoucode/agents/core/agent.py`，添加调试输出：

```python
async def execute(self, ...):
    # ... 前面的代码 ...
    
    # 智能加载
    context = await self.memory.load_context_smart(...)
    
    # 添加调试输出
    print(f"\n🔍 Memory调试信息:")
    print(f"  策略: {context['strategy']}")
    print(f"  历史轮数: {len(context['history'])}")
    print(f"  成本: {context['cost']}")
    print(f"  智能筛选: {'是' if context.get('filtered') else '否'}")
    
    if context.get('summary'):
        print(f"  摘要: {context['summary'][:100]}...")
    
    if context.get('profile'):
        print(f"  用户画像: {context['profile'].get('common_topics', [])}")
    
    # ... 后面的代码 ...
```

---

## 📊 关键日志说明

### 智能加载日志

```
INFO - 📊 判断为新话题但有历史，尝试筛选: 策略=simple_followup, 成本=1
INFO - 📦 构建结果: 0轮相关 + 2轮最近 = 2轮
INFO - 🌳 智能筛选: 从6轮中筛选出2轮相关对话
```

**解读**：
- 判断为新话题（不是追问）
- 使用 simple_followup 策略
- 从6轮历史中筛选出2轮相关对话
- 成本为1（相对值）

### 摘要生成日志

```
INFO - 🔄 触发摘要生成: session=xxx, round=5
INFO - ✅ 摘要已生成: 150字符
```

**解读**：
- 在第5轮对话时触发摘要生成
- 生成的摘要长度为150字符

### Agent执行日志

```
INFO - 📚 智能加载: 策略=medium_followup, 历史=3轮, 成本=2, 筛选=是
INFO - 📝 加载摘要: 150字符
INFO - 👤 加载画像: 5个话题
```

**解读**：
- 使用 medium_followup 策略
- 加载了3轮历史对话
- 加载了摘要（150字符）
- 加载了用户画像（5个常讨论话题）

---

## 🐛 常见问题

### 问题1：智能加载没有生效

**症状**：每次都加载全部历史，没有智能筛选

**检查**：
```python
# 检查是否正确调用
context = await memory.load_context_smart(
    session_id=session_id,
    user_id=user_id,
    user_input=user_input,
    is_followup=is_followup,  # 确保传递了追问判断
    confidence=confidence
)

# 检查日志
# 应该看到 "📊 判断为..." 的日志
```

**解决**：
- 确保传递了 `is_followup` 和 `confidence` 参数
- 检查 `FollowupDetector` 是否正常工作

### 问题2：摘要没有生成

**症状**：对话超过5轮，但没有生成摘要

**检查**：
```python
# 检查触发条件
history = memory.get_conversation_history(session_id)
should_generate = memory.long_term_memory.should_generate_summary(
    session_id, len(history)
)
print(f"应该生成摘要: {should_generate}")

# 检查是否有LLM客户端
from daoyoucode.agents.llm import get_client_manager
client_manager = get_client_manager()
print(f"LLM客户端: {client_manager}")
```

**解决**：
- 确保对话轮数 >= 5
- 确保LLM客户端已配置
- 检查 `agent.py` 中的摘要生成逻辑

### 问题3：用户画像为空

**症状**：`context['profile']` 为 None

**原因**：用户画像需要手动构建，不会自动生成

**解决**：
```python
# 手动构建用户画像
profile = await memory.long_term_memory.build_user_profile(
    user_id=user_id,
    all_sessions=["session-1", "session-2", "session-3"]
)

# 或在Agent中添加定期构建逻辑
# 例如：每10轮对话构建一次
```

### 问题4：向量检索报错

**症状**：`ModuleNotFoundError: No module named 'sentence_transformers'`

**原因**：向量检索依赖未安装（默认禁用）

**解决**：
```bash
# 方案1：安装依赖
pip install sentence-transformers

# 方案2：确保向量检索保持禁用状态
# 在 vector_retriever.py 中检查：
# self.enabled = False  # 应该是 False
```

---

## 🔬 深度调试

### 追踪智能加载决策

```python
# 在 smart_loader.py 的 decide_load_strategy 中添加断点
async def decide_load_strategy(self, ...):
    print(f"\n🔍 决策输入:")
    print(f"  is_followup: {is_followup}")
    print(f"  confidence: {confidence}")
    print(f"  history_count: {history_count}")
    print(f"  has_summary: {has_summary}")
    
    # ... 决策逻辑 ...
    
    print(f"\n🔍 决策输出:")
    print(f"  strategy: {strategy}")
    print(f"  config: {config}")
    
    return strategy, config
```

### 追踪关键词筛选

```python
# 在 smart_loader.py 的 _filter_relevant_history 中添加断点
async def _filter_relevant_history(self, ...):
    print(f"\n🔍 筛选输入:")
    print(f"  current_message: {current_message}")
    print(f"  history_count: {len(history)}")
    
    # 提取关键词
    keywords = self._extract_keywords(current_message)
    print(f"  keywords: {keywords}")
    
    # ... 筛选逻辑 ...
    
    print(f"\n🔍 筛选输出:")
    print(f"  relevant_count: {len(relevant)}")
    print(f"  recent_count: {len(recent)}")
    
    return combined
```

### 追踪摘要生成

```python
# 在 long_term_memory.py 的 generate_summary 中添加断点
async def generate_summary(self, ...):
    print(f"\n🔍 摘要生成:")
    print(f"  session_id: {session_id}")
    print(f"  history_count: {len(history)}")
    
    # 构建prompt
    prompt = self._build_summary_prompt(history)
    print(f"  prompt_length: {len(prompt)}")
    
    # 调用LLM
    summary = await llm_client.chat(...)
    print(f"  summary_length: {len(summary)}")
    
    return summary
```

---

## 📈 性能监控

### 监控Token使用

```python
# 在 agent.py 中添加token统计
async def execute(self, ...):
    # 记录开始时间
    import time
    start_time = time.time()
    
    # 智能加载
    context = await self.memory.load_context_smart(...)
    
    # 计算token数（估算）
    history_tokens = sum(
        len(h['user']) + len(h['ai']) 
        for h in context['history']
    ) // 4  # 粗略估算：4字符=1token
    
    summary_tokens = len(context.get('summary', '')) // 4
    
    print(f"\n📊 Token统计:")
    print(f"  历史: {history_tokens} tokens")
    print(f"  摘要: {summary_tokens} tokens")
    print(f"  总计: {history_tokens + summary_tokens} tokens")
    
    # ... 执行任务 ...
    
    # 记录结束时间
    end_time = time.time()
    print(f"  耗时: {end_time - start_time:.2f}秒")
```

### 监控策略分布

```python
# 获取统计信息
memory = get_memory_manager()
stats = memory.smart_loader.get_stats()

print("\n📊 策略分布:")
for strategy, count in stats.items():
    if strategy.startswith('total_'):
        continue
    percentage = count / stats['total_loads'] * 100
    print(f"  {strategy}: {count} ({percentage:.1f}%)")

print(f"\n平均成本: {stats['average_cost']:.2f}")
```

---

## 🧪 单元测试

### 测试智能加载

```python
# test_smart_loader.py
import pytest
from daoyoucode.agents.memory import get_memory_manager

@pytest.mark.asyncio
async def test_smart_loading_new_conversation():
    memory = get_memory_manager()
    
    context = await memory.load_context_smart(
        session_id="test-new",
        user_id="user-1",
        user_input="你好",
        is_followup=False,
        confidence=0.0
    )
    
    assert context['strategy'] == 'simple_followup'
    assert len(context['history']) == 0

@pytest.mark.asyncio
async def test_smart_loading_followup():
    memory = get_memory_manager()
    
    # 添加历史
    memory.add_conversation("test-followup", "问题1", "回答1")
    memory.add_conversation("test-followup", "问题2", "回答2")
    
    context = await memory.load_context_smart(
        session_id="test-followup",
        user_id="user-1",
        user_input="能详细说说吗？",
        is_followup=True,
        confidence=0.9
    )
    
    assert context['strategy'] in ['simple_followup', 'medium_followup']
    assert len(context['history']) > 0
```

### 测试摘要生成

```python
# test_summary.py
import pytest
from daoyoucode.agents.memory import get_memory_manager

@pytest.mark.asyncio
async def test_summary_trigger():
    memory = get_memory_manager()
    session_id = "test-summary"
    
    # 添加5轮对话
    for i in range(5):
        memory.add_conversation(
            session_id,
            f"问题{i+1}",
            f"回答{i+1}"
        )
    
    # 检查是否应该生成摘要
    history = memory.get_conversation_history(session_id)
    should_generate = memory.long_term_memory.should_generate_summary(
        session_id, len(history)
    )
    
    assert should_generate == True
```

---

## 🎯 实战场景

### 场景1：调试追问判断

```python
# 测试追问判断准确性
import asyncio
from daoyoucode.agents.memory import get_memory_manager

async def test_followup_detection():
    memory = get_memory_manager()
    session_id = "test-followup"
    
    # 添加历史
    memory.add_conversation(
        session_id,
        "这个项目的结构是什么？",
        "项目包含以下模块..."
    )
    
    # 测试不同的输入
    test_cases = [
        ("能详细说说吗？", True),  # 应该是追问
        ("今天天气怎么样？", False),  # 不是追问
        ("Agent系统在哪里？", True),  # 相关问题
    ]
    
    for message, expected in test_cases:
        is_followup, confidence, reason = await memory.is_followup(
            session_id, message
        )
        
        print(f"\n输入: {message}")
        print(f"判断: {is_followup} (期望: {expected})")
        print(f"置信度: {confidence:.2f}")
        print(f"原因: {reason}")
        
        if is_followup != expected:
            print("❌ 判断错误！")
        else:
            print("✅ 判断正确")

asyncio.run(test_followup_detection())
```

### 场景2：调试关键词筛选

```python
# 测试关键词筛选效果
import asyncio
from daoyoucode.agents.memory import get_memory_manager

async def test_keyword_filtering():
    memory = get_memory_manager()
    session_id = "test-filter"
    
    # 添加多样化的历史
    conversations = [
        ("这个项目的结构是什么？", "项目包含..."),
        ("Agent系统在哪里？", "Agent系统在..."),
        ("今天天气怎么样？", "天气很好..."),
        ("Memory系统有什么功能？", "Memory系统支持..."),
    ]
    
    for user_msg, ai_msg in conversations:
        memory.add_conversation(session_id, user_msg, ai_msg)
    
    # 测试筛选
    context = await memory.load_context_smart(
        session_id=session_id,
        user_id="user-1",
        user_input="Memory系统的智能加载是怎么工作的？",
        is_followup=False
    )
    
    print(f"\n筛选结果:")
    print(f"策略: {context['strategy']}")
    print(f"加载轮数: {len(context['history'])}")
    print(f"加载的对话:")
    for idx, h in enumerate(context['history'], 1):
        print(f"  {idx}. {h['user']}")

asyncio.run(test_keyword_filtering())
```

### 场景3：调试完整流程

```python
# 模拟完整的对话流程
import asyncio
from daoyoucode.agents.memory import get_memory_manager

async def test_full_flow():
    memory = get_memory_manager()
    session_id = "test-full"
    user_id = "user-1"
    
    # 模拟多轮对话
    conversations = [
        ("这个项目是做什么的？", "这是一个AI代码助手..."),
        ("有哪些核心功能？", "核心功能包括..."),
        ("Agent系统是怎么工作的？", "Agent系统使用..."),
        ("能详细说说吗？", "详细来说..."),
        ("工具系统有哪些工具？", "工具系统有25个工具..."),
    ]
    
    for idx, (user_msg, ai_msg) in enumerate(conversations, 1):
        print(f"\n{'='*60}")
        print(f"第{idx}轮对话")
        print(f"{'='*60}")
        
        # 判断追问
        if idx > 1:
            is_followup, confidence, reason = await memory.is_followup(
                session_id, user_msg
            )
            print(f"追问判断: {is_followup} (置信度: {confidence:.2f})")
        else:
            is_followup, confidence = False, 0.0
        
        # 智能加载
        context = await memory.load_context_smart(
            session_id=session_id,
            user_id=user_id,
            user_input=user_msg,
            is_followup=is_followup,
            confidence=confidence
        )
        
        print(f"加载策略: {context['strategy']}")
        print(f"历史轮数: {len(context['history'])}")
        print(f"成本: {context['cost']}")
        
        # 添加对话
        memory.add_conversation(session_id, user_msg, ai_msg)
        
        # 检查摘要
        history = memory.get_conversation_history(session_id)
        if memory.long_term_memory.should_generate_summary(session_id, len(history)):
            print(f"🔄 应该生成摘要（当前{len(history)}轮）")
    
    # 最终统计
    print(f"\n{'='*60}")
    print("最终统计")
    print(f"{'='*60}")
    
    stats = memory.smart_loader.get_stats()
    print(f"总加载次数: {stats['total_loads']}")
    print(f"平均成本: {stats['average_cost']:.2f}")
    
    storage_stats = memory.storage.get_stats()
    print(f"总对话数: {storage_stats['total_conversations']}")

asyncio.run(test_full_flow())
```

---

## 📝 调试检查清单

使用这个检查清单来系统地调试问题：

- [ ] 基础功能
  - [ ] 能添加对话
  - [ ] 能获取历史
  - [ ] 能保存用户偏好
  - [ ] 能保存任务历史

- [ ] 智能加载
  - [ ] 能判断追问
  - [ ] 能选择正确的策略
  - [ ] 能筛选相关对话
  - [ ] 能计算成本

- [ ] 长期记忆
  - [ ] 能触发摘要生成
  - [ ] 能生成摘要（需要LLM）
  - [ ] 能保存摘要
  - [ ] 能加载摘要

- [ ] Agent集成
  - [ ] Agent能访问Memory
  - [ ] 能在execute中使用智能加载
  - [ ] 能自动生成摘要
  - [ ] 能保存任务历史

- [ ] 性能
  - [ ] Token使用合理
  - [ ] 响应时间可接受
  - [ ] 策略分布合理

---

## 🚀 下一步

1. **运行测试**: `python backend/test_memory_integration.py`
2. **启用日志**: 在你的代码中添加 `logging.basicConfig(level=logging.DEBUG)`
3. **实际使用**: 在CLI中测试 `daoyoucode chat`
4. **监控性能**: 使用统计功能监控token使用和策略分布
5. **优化配置**: 根据实际使用情况调整策略配置

---

## 💡 提示

- 使用 `logging.DEBUG` 可以看到详细的决策过程
- 使用 `get_stats()` 可以监控系统运行状态
- 使用测试脚本可以快速验证特定场景
- 在Agent中添加调试输出可以追踪实际使用情况

祝调试顺利！🎉
