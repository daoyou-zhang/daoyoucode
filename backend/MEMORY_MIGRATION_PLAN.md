# Memory系统迁移计划

## 目标

将 `ai/memory/` 的完整设计迁移到 `backend/daoyoucode/agents/memory/`，同时保留当前的Agent记忆功能。

## 当前状态分析

### 当前实现 (backend/daoyoucode/agents/memory/)

**优点**：
- ✅ Agent层记忆（用户偏好、任务历史）
- ✅ 多智能体共享接口
- ✅ 简单清晰

**缺点**：
- ❌ 只有基础的对话历史存储
- ❌ 没有智能加载策略
- ❌ 没有摘要生成
- ❌ 没有向量检索
- ❌ 没有Intent Tree

### 原本设计 (ai/memory/)

**优点**：
- ✅ 分层记忆（短期/中期/长期）
- ✅ 智能加载策略（节省50-70% token）
- ✅ 自动摘要生成
- ✅ 向量检索
- ✅ Intent Tree智能筛选
- ✅ 用户画像构建

**缺点**：
- ❌ 没有Agent层记忆
- ❌ 没有多智能体共享接口

## 迁移策略

### 方案：合并两个系统的优点

```
backend/daoyoucode/agents/memory/
├── __init__.py              # 导出接口
├── manager.py               # ✅ 保留并增强（合并功能）
├── storage.py               # ✅ 保留并增强（添加摘要、画像）
├── long_term_memory.py      # ← 迁移（摘要、关键信息、画像）
├── smart_loader.py          # ← 迁移（智能加载策略）
├── vector_retriever.py      # ← 迁移（向量检索）
├── detector.py              # ✅ 保留（追问检测）
└── shared.py                # ✅ 保留（多智能体共享）
```

## 详细迁移步骤

### 阶段1：迁移核心组件（不破坏现有功能）

1. **迁移 long_term_memory.py**
   - 复制文件
   - 调整导入路径
   - 集成到 MemoryManager

2. **迁移 smart_loader.py**
   - 复制文件
   - 调整导入路径
   - 集成到 MemoryManager

3. **迁移 vector_retriever.py**
   - 复制文件
   - 调整导入路径
   - 作为可选依赖

### 阶段2：增强 MemoryManager

```python
class MemoryManager:
    """统一的记忆管理器（合并版）"""
    
    def __init__(self):
        self.storage = MemoryStorage()
        self.detector = FollowupDetector()
        
        # ← 新增：长期记忆
        self.long_term_memory = LongTermMemory()
        
        # ← 新增：智能加载器
        self.smart_loader = SmartLoader()
        
        # ← 新增：向量检索器（可选）
        self.vector_retriever = VectorRetriever()
    
    # ========== 保留：LLM层记忆 ==========
    def add_conversation(...)
    def get_conversation_history(...)
    async def is_followup(...)
    
    # ========== 保留：Agent层记忆 ==========
    def remember_preference(...)
    def get_preferences(...)
    def add_task(...)
    def get_task_history(...)
    
    # ========== 保留：多智能体共享 ==========
    def get_shared_context(...)
    def update_shared_context(...)
    def create_shared_memory(...)
    
    # ========== 新增：长期记忆 ==========
    async def generate_summary(...)
    async def get_summary(...)
    async def extract_key_info(...)
    async def build_user_profile(...)
    async def get_user_profile(...)
    
    # ========== 新增：智能加载 ==========
    async def load_context_smart(...)
    async def decide_load_strategy(...)
```

### 阶段3：增强 MemoryStorage

```python
class MemoryStorage:
    """记忆存储（增强版）"""
    
    def __init__(self):
        # 保留：现有存储
        self._conversations = {}
        self._preferences = {}
        self._tasks = {}
        self._shared_contexts = {}
        
        # 新增：摘要存储
        self._summaries = {}
        
        # 新增：关键信息存储
        self._key_info = {}
        
        # 新增：用户画像存储
        self._user_profiles = {}
    
    # ========== 保留：现有方法 ==========
    def add_conversation(...)
    def get_conversation_history(...)
    def add_preference(...)
    def get_preferences(...)
    def add_task(...)
    def get_task_history(...)
    def get_shared_context(...)
    def update_shared_context(...)
    
    # ========== 新增：摘要方法 ==========
    def save_summary(...)
    def get_summary(...)
    
    # ========== 新增：关键信息方法 ==========
    def save_key_info(...)
    def get_key_info(...)
    
    # ========== 新增：用户画像方法 ==========
    def save_user_profile(...)
    def get_user_profile(...)
```

### 阶段4：集成到Agent

```python
# backend/daoyoucode/agents/core/agent.py

async def execute(self, ...):
    # 使用智能加载策略
    strategy, config = await self.memory.smart_loader.decide_load_strategy(
        is_followup=is_followup,
        history_count=len(history),
        has_summary=await self.memory.long_term_memory.get_summary(session_id) is not None
    )
    
    # 加载上下文
    context = await self.memory.smart_loader.load_context(
        strategy_name=strategy,
        strategy_config=config,
        memory_manager=self.memory,
        session_id=session_id,
        user_id=user_id,
        current_message=user_input
    )
    
    # 使用加载的上下文
    history = context['history']
    summary = context['summary']
    profile = context['profile']
```

## 兼容性保证

### 1. 向后兼容

```python
# 旧代码仍然可以工作
history = memory.get_conversation_history(session_id, limit=3)

# 新代码使用智能加载
context = await memory.load_context_smart(
    session_id=session_id,
    user_input=user_input,
    is_followup=True
)
```

### 2. 渐进式启用

```python
# 配置文件控制功能开关
config = {
    'enable_smart_loading': True,   # 智能加载
    'enable_summary': True,          # 自动摘要
    'enable_vector_search': False,   # 向量检索（可选）
    'enable_user_profile': True      # 用户画像
}
```

## 测试计划

### 单元测试

```python
# test_long_term_memory.py
async def test_generate_summary():
    memory = get_memory_manager()
    summary = await memory.generate_summary(...)
    assert summary is not None

# test_smart_loader.py
async def test_decide_strategy():
    loader = SmartLoader()
    strategy, config = await loader.decide_load_strategy(...)
    assert strategy in ['new_conversation', 'simple_followup', ...]

# test_vector_retriever.py
async def test_find_relevant():
    retriever = VectorRetriever()
    relevant = await retriever.find_relevant_history(...)
    assert len(relevant) > 0
```

### 集成测试

```python
# test_memory_integration.py
async def test_full_workflow():
    # 1. 添加对话
    memory.add_conversation(...)
    
    # 2. 智能加载
    context = await memory.load_context_smart(...)
    
    # 3. 生成摘要
    summary = await memory.generate_summary(...)
    
    # 4. 构建画像
    profile = await memory.build_user_profile(...)
```

## 迁移时间表

### Week 1: 迁移核心组件
- Day 1-2: 迁移 long_term_memory.py
- Day 3-4: 迁移 smart_loader.py
- Day 5: 迁移 vector_retriever.py

### Week 2: 集成和测试
- Day 1-2: 增强 MemoryManager
- Day 3-4: 增强 MemoryStorage
- Day 5: 编写测试

### Week 3: 集成到Agent
- Day 1-2: 修改 Agent.execute()
- Day 3-4: 端到端测试
- Day 5: 文档和优化

## 风险和缓解

### 风险1：破坏现有功能
**缓解**：
- 保留所有现有接口
- 新功能作为可选项
- 充分测试

### 风险2：性能下降
**缓解**：
- 智能加载默认关闭
- 向量检索作为可选依赖
- 性能测试和优化

### 风险3：依赖问题
**缓解**：
- sentence-transformers 作为可选依赖
- 降级方案（关键词匹配）
- 清晰的错误提示

## 成功标准

1. ✅ 所有现有功能正常工作
2. ✅ 智能加载策略可用
3. ✅ 自动摘要生成可用
4. ✅ 向量检索可用（可选）
5. ✅ 用户画像构建可用
6. ✅ 所有测试通过
7. ✅ 文档完善

## 下一步

开始迁移！
