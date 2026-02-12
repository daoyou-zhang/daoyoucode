# IntelligentRouter 动态适配能力

> 新增Agent时，Router自动适配，无需修改代码

---

## ✅ 动态适配能力

### 1. TaskManager - 完全自动适配 ✅

**无需任何配置**，TaskManager自动适配新增的Agent和Orchestrator：

```python
# 新增Agent后，直接使用
result = await execute_skill("my_skill", "用户输入")

# TaskManager自动记录新Agent
task_info = get_task_info(result['task_id'])
print(task_info['agent'])  # 新Agent的名称
print(task_info['orchestrator'])  # 使用的编排器
```

**原理**：
- TaskManager只记录名称字符串，不依赖具体实现
- 任何Agent/Orchestrator都会被自动追踪

---

### 2. IntelligentRouter - 三种适配方式 ✅

#### 方式1: 动态注册（推荐）

```python
from daoyoucode.agents.core.router import get_intelligent_router

router = get_intelligent_router()

# 注册新Agent的关键词
router.register_agent_keywords(
    'data_scientist',
    ['数据', '分析', '统计', '机器学习', '模型']
)

# 立即可用
decision = await router.route("分析这个数据集")
print(decision.agent)  # data_scientist
```

#### 方式2: 配置文件（推荐）

**步骤1**: 编辑 `config/agent_router_config.yaml`

```yaml
agent_domains:
  # 现有Agent...
  
  # 新增Agent
  data_scientist:
    - 数据
    - 分析
    - 统计
    - 机器学习
    - 模型
    - 训练
  
  security_expert:
    - 安全
    - 漏洞
    - 加密
    - 权限
    - 认证
```

**步骤2**: 加载配置

```python
router = get_intelligent_router(
    config_path='config/agent_router_config.yaml'
)

# 自动加载新Agent
decision = await router.route("检查安全漏洞")
print(decision.agent)  # security_expert
```

#### 方式3: 自动发现（最智能）

```python
# 1. 创建新Agent
class DataScientistAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="data_scientist",
            description="数据科学专家，擅长数据分析、统计建模和机器学习",
            model="qwen-max"
        )
        super().__init__(config)

# 2. 注册Agent
agent = DataScientistAgent()
register_agent(agent)

# 3. Router自动发现（从description提取关键词）
router = get_intelligent_router(auto_discover=True)

# 4. 立即可用
decision = await router.route("分析数据")
print(decision.agent)  # data_scientist
```

**自动发现原理**：
- Router从AgentRegistry获取所有已注册的Agent
- 从Agent的description中提取关键词
- 自动注册到路由规则中

---

## 📊 三种方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **动态注册** | 灵活、即时生效 | 需要代码调用 | 运行时动态添加 |
| **配置文件** | 集中管理、易维护 | 需要重启 | 项目配置 |
| **自动发现** | 零配置、最智能 | 关键词可能不准确 | 快速原型 |

---

## 🎯 推荐实践

### 场景1: 项目初期（快速原型）

使用**自动发现**：

```python
# 只需创建Agent，Router自动适配
class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            description="我的专业Agent，擅长XXX",  # 描述要准确
            model="qwen-max"
        )
        super().__init__(config)

register_agent(MyAgent())

# Router自动发现，无需配置
router = get_intelligent_router(auto_discover=True)
```

### 场景2: 项目稳定期（生产环境）

使用**配置文件**：

```yaml
# config/agent_router_config.yaml
agent_domains:
  my_agent:
    - 关键词1
    - 关键词2
    - 关键词3
```

```python
# 加载配置
router = get_intelligent_router(
    config_path='config/agent_router_config.yaml',
    auto_discover=False  # 关闭自动发现，使用精确配置
)
```

### 场景3: 运行时扩展（插件系统）

使用**动态注册**：

```python
# 插件加载时动态注册
def load_plugin(plugin_agent, keywords):
    register_agent(plugin_agent)
    
    router = get_intelligent_router()
    router.register_agent_keywords(plugin_agent.name, keywords)
```

---

## 🔧 API参考

### IntelligentRouter

#### `register_agent_keywords(agent_name, keywords)`

动态注册Agent关键词

```python
router.register_agent_keywords(
    'data_scientist',
    ['数据', '分析', '统计', '机器学习']
)
```

#### `unregister_agent(agent_name)`

取消注册Agent

```python
router.unregister_agent('temp_agent')
```

#### `list_registered_agents()`

列出所有已注册的Agent

```python
agents = router.list_registered_agents()
print(agents)  # ['code_analyzer', 'test_writer', ...]
```

#### `auto_discover_agents()`

手动触发自动发现

```python
count = router.auto_discover_agents()
print(f"发现了 {count} 个新Agent")
```

---

## 📝 完整示例

### 示例1: 添加数据科学Agent

```python
# 1. 创建Agent
class DataScientistAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="data_scientist",
            description="数据科学专家，擅长数据分析、统计建模和机器学习",
            model="qwen-max",
            temperature=0.3
        )
        super().__init__(config)

# 2. 注册Agent
agent = DataScientistAgent()
register_agent(agent)

# 3. 配置Router（三选一）

# 方式A: 自动发现
router = get_intelligent_router(auto_discover=True)

# 方式B: 动态注册
router = get_intelligent_router()
router.register_agent_keywords(
    'data_scientist',
    ['数据', '分析', '统计', '机器学习', '模型']
)

# 方式C: 配置文件
# 编辑 config/agent_router_config.yaml
router = get_intelligent_router(
    config_path='config/agent_router_config.yaml'
)

# 4. 使用
decision = await router.route("分析这个数据集的统计特征")
print(f"选择的Agent: {decision.agent}")  # data_scientist
print(f"置信度: {decision.confidence}")
print(f"理由: {decision.reasoning}")
```

### 示例2: 批量添加多个Agent

```python
# 定义多个新Agent
new_agents = {
    'security_expert': ['安全', '漏洞', '加密', '权限'],
    'performance_optimizer': ['性能', '优化', '加速', '缓存'],
    'ui_designer': ['界面', '设计', 'ui', 'ux', '用户体验']
}

# 批量注册
router = get_intelligent_router()
for agent_name, keywords in new_agents.items():
    router.register_agent_keywords(agent_name, keywords)

# 立即可用
test_cases = [
    "检查代码中的安全漏洞",      # -> security_expert
    "优化这个函数的性能",        # -> performance_optimizer
    "设计一个用户友好的界面",    # -> ui_designer
]

for user_input in test_cases:
    decision = await router.route(user_input)
    print(f"{user_input} -> {decision.agent}")
```

---

## ✅ 测试验证

运行测试验证动态适配能力：

```bash
cd backend
python test_router_dynamic.py
```

**测试覆盖**：
- ✅ 动态注册Agent
- ✅ 取消注册Agent
- ✅ 自动发现Agent
- ✅ 从配置文件加载
- ✅ 多个新Agent路由

---

## 🎉 总结

### TaskManager
- ✅ **完全自动适配**
- ✅ 无需任何配置
- ✅ 新增Agent/Orchestrator立即可用

### IntelligentRouter
- ✅ **三种适配方式**（动态注册、配置文件、自动发现）
- ✅ 零代码修改
- ✅ 灵活可扩展

### 核心优势
- **零侵入** - 不需要修改Router代码
- **灵活** - 三种方式适应不同场景
- **智能** - 自动发现功能
- **可维护** - 配置文件集中管理

---

**新增Agent时，完全无需修改TaskManager和Router代码！** 🎉

