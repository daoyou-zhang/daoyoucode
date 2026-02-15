# 对话树（Conversation Tree）设计文档

## 🎯 设计目标

对话树用于：
1. 维护对话的树形结构（分支、话题切换）
2. 支持多分支对话（用户可以在不同话题间切换）
3. 智能识别话题切换和分支创建
4. 提供基于树结构的上下文检索
5. 可扩展：可以被其他Agent复用

---

## 📊 核心概念

### 1. 对话节点（ConversationNode）

每个对话是树中的一个节点：

```python
node = {
    'conversation_id': 'conv-abc123',    # 对话ID
    'user_message': '我的猫不吃饭',      # 用户消息
    'ai_response': '可能是肠胃问题...',  # AI响应
    'parent_id': 'conv-xyz789',          # 父对话ID
    'branch_id': 'branch-1',             # 分支ID
    'topic': '猫-肠胃问题',              # 话题标签
    'depth': 1,                          # 树深度
    'is_branch_start': False,            # 是否为分支起点
    'timestamp': '2026-02-15T12:00:00'   # 时间戳
}
```

### 2. 分支（Branch）

分支表示一个连续的话题：

```
Branch-1: 猫-肠胃问题
├─ Conv-1: 我的猫不吃饭
├─ Conv-2: 需要去医院吗？
└─ Conv-3: 吃什么药？

Branch-2: 狗-皮肤问题
├─ Conv-4: 狗的皮肤有红点
└─ Conv-5: 用什么药膏？
```

### 3. 树结构

完整的对话树：

```
Root
├─ Branch-1: 猫-肠胃问题
│  ├─ Conv-1: 我的猫不吃饭
│  ├─ Conv-2: 需要去医院吗？
│  └─ Conv-3: 吃什么药？
│
├─ Branch-2: 狗-皮肤问题
│  ├─ Conv-4: 狗的皮肤有红点
│  └─ Conv-5: 用什么药膏？
│
└─ Branch-3: 猫-疫苗
   └─ Conv-6: 猫需要打疫苗吗？
```

---

## 🔧 核心功能

### 1. 话题检测

自动检测话题切换：

```python
# 当前分支：猫-肠胃问题
# 关键词：{猫, 吃饭, 肠胃}

# 新消息：狗的皮肤有红点
# 关键词：{狗, 皮肤, 红点}

# 重叠度：0 / 3 = 0% < 30%
# 判断：话题切换 ✅
```

**算法**：
1. 提取当前消息的关键词
2. 与当前分支的话题关键词对比
3. 如果重叠度 < 30%，判断为话题切换

### 2. 分支管理

自动创建和维护分支：

```python
tree = get_conversation_tree(enabled=True)

# 添加对话1（创建分支1）
node1 = tree.add_conversation(
    user_message="我的猫不吃饭",
    ai_response="可能是肠胃问题..."
)
# branch_id: branch-abc123

# 添加对话2（同一分支）
node2 = tree.add_conversation(
    user_message="需要去医院吗？",
    ai_response="建议观察..."
)
# branch_id: branch-abc123 (相同)

# 添加对话3（话题切换，创建分支2）
node3 = tree.add_conversation(
    user_message="狗的皮肤有红点",
    ai_response="可能是过敏..."
)
# branch_id: branch-xyz789 (新分支)
```

### 3. 智能检索

基于树结构的上下文检索：

```python
# 策略1：当前分支
# 只返回当前分支的对话
convs = tree.get_relevant_conversations(
    current_message="猫的肠胃问题怎么办？",
    limit=5,
    strategy='current_branch'
)

# 策略2：关键词匹配
# 在所有分支中查找包含相同关键词的对话
convs = tree.get_relevant_conversations(
    current_message="猫的肠胃问题怎么办？",
    limit=5,
    strategy='keyword'
)

# 策略3：树结构
# 优先当前分支，不足时从相关分支补充
convs = tree.get_relevant_conversations(
    current_message="猫的肠胃问题怎么办？",
    limit=5,
    strategy='tree'
)

# 策略4：自动选择（推荐）
# 根据分支数量自动选择最佳策略
convs = tree.get_relevant_conversations(
    current_message="猫的肠胃问题怎么办？",
    limit=5,
    strategy='auto'
)
```

---

## 🚀 使用方法

### 方法1：独立使用

```python
from daoyoucode.agents.memory import get_conversation_tree

# 创建对话树
tree = get_conversation_tree(enabled=True)

# 添加对话
node = tree.add_conversation(
    user_message="我的猫不吃饭",
    ai_response="可能是肠胃问题..."
)

# 获取当前分支的对话
convs = tree.get_branch_conversations(limit=5)

# 智能检索
relevant_convs = tree.get_relevant_conversations(
    current_message="猫的肠胃问题怎么办？",
    limit=5
)

# 获取统计信息
stats = tree.get_tree_stats()
print(f"总对话数: {stats['total_conversations']}")
print(f"总分支数: {stats['total_branches']}")
```

### 方法2：通过MemoryManager（推荐）

```python
from daoyoucode.agents.memory import get_memory_manager

# 创建记忆管理器（自动启用树结构）
memory = get_memory_manager()

# 添加对话（自动维护树结构）
memory.add_conversation(
    session_id="session-123",
    user_message="我的猫不吃饭",
    ai_response="可能是肠胃问题...",
    user_id="user-abc"
)

# 获取历史（包含树结构元数据）
history = memory.get_conversation_history("session-123")

# 智能加载（自动使用树结构检索）
context = await memory.load_context_smart(
    session_id="session-123",
    user_id="user-abc",
    user_input="猫的肠胃问题怎么办？",
    is_followup=True
)

# 检查是否使用了树结构
if context.get('tree_based'):
    print("✅ 使用了树结构检索")
```

### 方法3：在Agent中使用

```python
# Agent会自动使用树结构（如果启用）
result = await agent.execute(
    prompt_source={'use_agent_default': True},
    user_input="猫的肠胃问题怎么办？",
    context={'session_id': 'session-123'}
)

# 树结构会自动：
# 1. 检测话题切换
# 2. 创建新分支
# 3. 智能检索相关对话
```

---

## 📋 数据结构

### 对话历史格式

```python
conversation = {
    'user': '我的猫不吃饭',
    'ai': '可能是肠胃问题...',
    'timestamp': '2026-02-15T12:00:00',
    'metadata': {
        'conversation_id': 'conv-abc123',
        'parent_id': None,
        'branch_id': 'branch-1',
        'topic': '猫-肠胃问题',
        'depth': 0,
        'is_branch_start': True
    }
}
```

### 树统计信息

```python
stats = {
    'enabled': True,
    'total_conversations': 6,
    'total_branches': 3,
    'current_branch_id': 'branch-3',
    'max_depth': 2,
    'branches': {
        'branch-1': 3,  # 3个对话
        'branch-2': 2,  # 2个对话
        'branch-3': 1   # 1个对话
    }
}
```

---

## 🎨 检索策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| current_branch | 单一话题，分支少 | 简单快速 | 可能遗漏相关对话 |
| keyword | 多话题，需要跨分支 | 语义相关性高 | 可能误匹配 |
| tree | 多分支，需要平衡 | 兼顾当前和相关 | 稍复杂 |
| auto | 通用场景（推荐） | 自动选择最佳 | - |

### 自动选择逻辑

```python
if 分支数 == 1:
    使用 current_branch  # 只有一个分支，直接返回
elif 分支数 <= 3:
    使用 tree  # 分支较少，使用树结构
else:
    使用 keyword  # 分支较多，使用关键词匹配
```

---

## 🔄 与Memory系统的集成

### 数据流

```
用户输入
  ↓
MemoryManager.add_conversation()
  ↓
ConversationTree.add_conversation()
  ├─ 检测话题切换
  ├─ 创建/更新分支
  └─ 添加树结构元数据
  ↓
MemoryStorage.add_conversation()
  ↓
保存到内存（包含元数据）
```

### 智能加载流程

```
SmartLoader.load_context()
  ↓
检查是否启用树结构
  ↓
是 → ConversationTree.get_relevant_conversations()
  ├─ 自动选择检索策略
  ├─ 查找相关对话
  └─ 返回结果
  ↓
否 → 降级到关键词匹配
  ↓
返回上下文
```

---

## ⚙️ 配置选项

### 启用/禁用树结构

```python
# 方法1：在MemoryManager初始化时
from daoyoucode.agents.memory.manager import MemoryManager

memory = MemoryManager(enable_tree=True)  # 启用
memory = MemoryManager(enable_tree=False)  # 禁用

# 方法2：直接创建ConversationTree
from daoyoucode.agents.memory import get_conversation_tree

tree = get_conversation_tree(enabled=True)  # 启用
tree = get_conversation_tree(enabled=False)  # 禁用
```

### 调整话题检测阈值

```python
# 在conversation_tree.py中修改
def _detect_topic_switch(self, current_message: str):
    # ...
    overlap_ratio = overlap / len(current_keywords)
    
    # 阈值：30%（可调整）
    if overlap_ratio < 0.3:  # ← 修改这里
        return True, new_topic
```

---

## 📊 性能考虑

### 内存占用

```
单个对话节点：~1KB
100个对话：~100KB
1000个对话：~1MB
```

### 检索性能

| 操作 | 时间复杂度 | 说明 |
|------|-----------|------|
| 添加对话 | O(1) | 直接添加到字典 |
| 话题检测 | O(k) | k为关键词数量 |
| 当前分支检索 | O(n) | n为分支对话数 |
| 关键词检索 | O(m*k) | m为总对话数，k为关键词数 |
| 树结构检索 | O(b*n) | b为分支数，n为每分支对话数 |

### 优化建议

1. **限制分支数量**：超过10个分支时，自动合并旧分支
2. **缓存关键词**：避免重复提取
3. **异步检测**：话题检测可以异步执行
4. **批量加载**：一次性加载多个分支

---

## 🧪 测试

### 运行测试

```bash
python backend/test_conversation_tree.py
```

### 测试内容

- ✅ 基础树结构
- ✅ 分支检索
- ✅ 话题检测
- ✅ 导出和导入
- ✅ 与Memory系统集成
- ✅ 与SmartLoader集成

---

## 🔮 扩展性

### 1. 自定义话题检测

```python
class CustomConversationTree(ConversationTree):
    def _detect_topic_switch(self, current_message: str):
        # 自定义检测逻辑
        # 例如：使用LLM判断
        # 例如：使用向量相似度
        pass
```

### 2. 自定义检索策略

```python
class CustomConversationTree(ConversationTree):
    def get_relevant_conversations(self, current_message: str, limit: int, strategy: str):
        if strategy == 'my_custom_strategy':
            # 自定义检索逻辑
            pass
        else:
            return super().get_relevant_conversations(current_message, limit, strategy)
```

### 3. 多Agent共享

```python
# Agent1使用树结构
tree = get_conversation_tree(enabled=True)
agent1_memory = MemoryManager(enable_tree=True)

# Agent2复用同一个树
agent2_memory = MemoryManager(enable_tree=True)
# 它们会共享同一个树实例（单例模式）
```

---

## 📚 相关文档

- `MEMORY_LEVELS.md` - 两级数据模型
- `MEMORY_USER_ID.md` - 用户ID管理
- `MEMORY_PERSISTENCE.md` - 持久化说明
- `MEMORY_USER_PROFILE_DESIGN.md` - 用户画像设计

---

## ✅ 总结

**对话树的核心价值**：

1. ✅ 自动检测话题切换
2. ✅ 维护多分支对话
3. ✅ 智能检索相关对话
4. ✅ 可扩展的设计
5. ✅ 可选启用，不强制依赖

**设计原则**：

- 轻量级：通过元数据标记，不改变核心数据结构
- 可扩展：支持多种检索策略，可以自定义
- 可选：不强制依赖，可以禁用
- 通用：可以被其他Agent复用

**使用建议**：

- 对于简单场景（单一话题），可以禁用树结构
- 对于复杂场景（多话题切换），建议启用树结构
- 使用`strategy='auto'`让系统自动选择最佳策略

这个设计既保证了功能的完整性，又保持了系统的灵活性！🎉
