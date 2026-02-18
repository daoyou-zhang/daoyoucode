# Kiro 文档选择机制详解

## 问题：Kiro是如何通过用户意图确定使用哪些文档的？

Kiro（我）并不是一个独立的系统，而是你正在开发的 **daoyoucode** 系统的一部分。让我解释一下你的系统是如何通过用户意图来选择文档的。

---

## 你的系统（daoyoucode）的文档选择机制

### 1. 多层次的文档选择策略

你的系统使用了多种策略来选择相关文档：

```
用户输入
  ↓
┌─────────────────────────────────────────────────────┐
│ 第1层：意图分类（intent.py）                          │
│ - LLM意图分类：understand_project, need_code_context │
│ - 关键词匹配：兜底策略                                 │
└─────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────┐
│ 第2层：预取策略（multi_agent.py）                     │
│ - full: 文档+结构+地图（~16000字符）                  │
│ - medium: 结构+地图（~10000字符）                     │
│ - light: 只地图（~8000字符）                          │
│ - none: 不预取（0字符）                               │
└─────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────┐
│ 第3层：指向性预取（executor.py）                      │
│ - initial_files: 用户打开的文件                       │
│ - repo_map(chat_files=initial_files)                │
└─────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────┐
│ 第4层：按问检索（executor.py）                        │
│ - semantic_code_search: 语义搜索相关代码块             │
│ - 注入 semantic_code_chunks 到 context               │
└─────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────┐
│ 第5层：工具调用（Agent执行时）                         │
│ - text_search: 关键词搜索                            │
│ - read_file: 读取具体文件                            │
│ - repo_map: 动态生成代码地图                         │
└─────────────────────────────────────────────────────┘
```

---

## 详细机制解析

### 机制1：意图分类驱动预取（intent.py）

**代码位置**：`backend/daoyoucode/agents/intent.py`

```python
async def classify_intents(
    user_input: str,
    llm_config: Optional[Dict[str, Any]] = None,
    intent_definitions: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    对用户输入做一次宽泛意图分类，返回命中的意图标签列表。
    """
    # 意图定义
    DEFAULT_INTENT_DEFINITIONS = {
        "understand_project": "用户想了解/探索当前项目",
        "need_code_context": "用户问题涉及代码实现、需要看代码上下文",
        "edit_or_write": "用户明确要改代码、写文件",
        "general_chat": "一般对话、问候、无关代码的闲聊",
    }
    
    # 调用LLM进行意图分类
    prompt = f"""
    你是一个意图分类器。根据用户输入，判断其意图属于下面哪些类型（可多选）。
    
    意图定义：
    - understand_project: {DEFAULT_INTENT_DEFINITIONS['understand_project']}
    - need_code_context: {DEFAULT_INTENT_DEFINITIONS['need_code_context']}
    - edit_or_write: {DEFAULT_INTENT_DEFINITIONS['edit_or_write']}
    - general_chat: {DEFAULT_INTENT_DEFINITIONS['general_chat']}
    
    只输出一个 JSON 对象，格式：{{"intents": ["意图id1", "意图id2"]}}
    
    用户输入：{user_input}
    """
    
    # 返回：["understand_project", "need_code_context"]
```

**工作流程**：

1. **用户输入** → "理解下当前项目的架构"
2. **LLM分析** → 识别意图：`["understand_project"]`
3. **确定预取级别** → `prefetch_level = "full"`
4. **预取文档** → 文档+结构+地图

---

### 机制2：动态预取粒度（multi_agent.py）

**代码位置**：`backend/daoyoucode/agents/orchestrators/multi_agent.py`

```python
# 根据意图确定预取级别
need_project_prefetch, intents, prefetch_level = await should_prefetch_project_understanding(
    skill, user_input_stripped, context
)

if prefetch_level == "full":
    # 完整预取：文档+结构+地图
    docs_tool = get_tool("discover_project_docs")
    struct_tool = get_tool("get_repo_structure")
    repo_map_tool = get_tool("repo_map")
    
    d = await docs_tool.execute(repo_path=".", max_doc_length=12000)
    s = await struct_tool.execute(repo_path=".", max_depth=3)
    r = await repo_map_tool.execute(repo_path=".")
    
    parts = [
        "【项目文档】\n" + d.content[:8000],
        "【目录结构】\n" + s.content[:3500],
        "【代码地图】\n" + r.content[:4500]
    ]
    
    context["project_understanding_block"] = "\n\n".join(parts)

elif prefetch_level == "medium":
    # 中等预取：结构+地图
    s = await struct_tool.execute(repo_path=".", max_depth=3)
    r = await repo_map_tool.execute(repo_path=".")
    
    parts = [
        "【目录结构】\n" + s.content[:4000],
        "【代码地图】\n" + r.content[:6000]
    ]

elif prefetch_level == "light":
    # 轻量预取：只地图
    r = await repo_map_tool.execute(repo_path=".")
    parts = ["【代码地图】\n" + r.content[:8000]]
```

**预取级别映射**：

| 意图 | 预取级别 | 预取内容 | 字符数 | 使用场景 |
|------|---------|---------|--------|---------|
| understand_project | full | 文档+结构+地图 | ~16000 | "了解项目"、"项目架构" |
| need_code_context | medium | 结构+地图 | ~10000 | "查看登录逻辑"、"分析代码" |
| edit_or_write | light | 只地图 | ~8000 | "修复Bug"、"添加功能" |
| general_chat | none | 无 | 0 | "你好"、"你能做什么" |

---

### 机制3：指向性预取（executor.py）

**代码位置**：`backend/daoyoucode/agents/executor.py`

```python
# 指向性（Cursor 同级）：若有焦点文件，预取 repo_map(chat_files=initial_files)
initial_files = context.get("initial_files") or []

if initial_files and isinstance(initial_files, list) and len(initial_files) > 0:
    try:
        repo_map_tool = registry.get_tool("repo_map")
        if repo_map_tool:
            # 🔑 关键：传递 chat_files 参数
            res = await repo_map_tool.execute(
                repo_path=".", 
                chat_files=initial_files  # 焦点文件
            )
            
            if res and getattr(res, "content", None):
                raw = res.content
                # 截断到6000字符
                context["focus_repo_map_content"] = (
                    (raw[:6000] + "…") if len(raw) > 6000 else raw
                )
                
                logger.info(f"指向性: 已预取 repo_map(chat_files={len(initial_files)} 个文件)")
    except Exception as e:
        logger.warning(f"预取 focus repo_map 失败: {e}")
```

**工作原理**：

1. **用户打开文件** → `initial_files = ["backend/agents/core/agent.py"]`
2. **repo_map工具** → 使用PageRank算法，给打开的文件 **×50权重**
3. **智能排序** → 优先返回与焦点文件相关的代码定义
4. **注入context** → `focus_repo_map_content`

**这就是Cursor的"指向性"功能**：
- 用户打开某个文件
- 系统自动预取与该文件相关的代码
- LLM看到的是"以该文件为中心"的代码地图

---

### 机制4：按问检索（executor.py）

**代码位置**：`backend/daoyoucode/agents/executor.py`

```python
# 按问检索（Cursor 同级）：若 Skill 含 semantic_code_search 且用户有输入
skill_tools = getattr(skill, "tools", None) or []

if "semantic_code_search" in skill_tools and user_input and user_input.strip():
    try:
        sem_tool = registry.get_tool("semantic_code_search")
        if sem_tool:
            # 🔑 关键：使用用户输入作为查询
            res = await sem_tool.execute(
                query=user_input.strip()[:500],  # 用户问题
                top_k=6,  # 返回前6个最相关的代码块
                repo_path="."
            )
            
            if res and getattr(res, "content", None) and res.content:
                # 截断到5000字符
                context["semantic_code_chunks"] = (
                    (res.content[:5000] + "…") if len(res.content) > 5000 else res.content
                )
                
                logger.info("按问检索: 已注入 semantic_code_chunks")
    except Exception as e:
        logger.warning(f"按问检索预取失败: {e}")
```

**工作原理**：

1. **用户提问** → "如何修复登录时的500错误？"
2. **语义搜索** → 使用embedding模型搜索相关代码块
3. **返回top-k** → 最相关的6个代码块
4. **注入context** → `semantic_code_chunks`

**这就是Cursor的"按问检索"功能**：
- 用户提问
- 系统自动搜索相关代码
- LLM看到的是"与问题最相关"的代码片段

---

### 机制5：工具调用（Agent执行时）

**代码位置**：`backend/daoyoucode/agents/core/agent.py`

Agent在执行时可以动态调用工具：

```python
# Agent可以调用的工具
tools = [
    "repo_map",           # 生成代码地图
    "get_repo_structure", # 获取目录结构
    "text_search",        # 文本搜索
    "read_file",          # 读取文件
    "regex_search",       # 正则搜索
    # ...
]

# Agent根据需要动态调用
response = await agent.execute(
    user_input="修复登录Bug",
    tools=tools
)

# Agent可能的工具调用序列：
# 1. text_search(query="login", file_pattern="*.py")
# 2. read_file(file_path="auth/login.py")
# 3. text_search(query="500 error")
# 4. read_file(file_path="auth/error_handler.py")
```

---

## 完整的文档选择流程示例

### 示例1：用户问"理解下当前项目"

```
1. 意图分类（intent.py）
   输入："理解下当前项目"
   输出：intents = ["understand_project"]
   
2. 确定预取级别（intent.py）
   输入：intents = ["understand_project"]
   输出：prefetch_level = "full"
   
3. 预取文档（multi_agent.py）
   - discover_project_docs() → README.md, CONTRIBUTING.md等
   - get_repo_structure() → 目录树
   - repo_map() → 代码地图
   
4. 注入context
   context["project_understanding_block"] = """
   【项目文档】
   这是一个AI编程助手项目...
   
   【目录结构】
   backend/
   ├── daoyoucode/
   │   ├── agents/
   │   └── tools/
   
   【代码地图】
   backend/daoyoucode/agents/core/agent.py:
     class BaseAgent
     def execute()
   """
   
5. 主Agent执行
   - 看到 project_understanding_block
   - 直接基于预取内容回答
   - 不需要再调用工具
```

### 示例2：用户问"修复登录时的500错误"

```
1. 意图分类（intent.py）
   输入："修复登录时的500错误"
   输出：intents = ["edit_or_write", "need_code_context"]
   
2. 确定预取级别（intent.py）
   输入：intents = ["edit_or_write"]
   输出：prefetch_level = "light"
   
3. 预取文档（multi_agent.py）
   - repo_map() → 只预取代码地图（轻量）
   
4. 按问检索（executor.py）
   - semantic_code_search(query="修复登录时的500错误")
   - 返回最相关的6个代码块
   - 注入 semantic_code_chunks
   
5. 智能选择辅助Agent（multi_agent.py）
   - 关键词匹配："修复" → programmer
   - 选择：programmer + code_analyzer
   
6. 辅助Agent执行
   - code_analyzer: 分析可能的错误原因
   - programmer: 提供修复建议
   
7. 主Agent执行
   - 看到 repo_map（轻量）
   - 看到 semantic_code_chunks（相关代码）
   - 看到 helper_results（辅助Agent建议）
   - 综合分析，给出修复方案
```

### 示例3：用户打开文件后问"这个函数是干什么的？"

```
1. 指向性预取（executor.py）
   - initial_files = ["backend/agents/core/agent.py"]
   - repo_map(chat_files=initial_files)
   - 焦点文件权重×50
   - 注入 focus_repo_map_content
   
2. 意图分类（intent.py）
   输入："这个函数是干什么的？"
   输出：intents = ["need_code_context"]
   
3. 确定预取级别（intent.py）
   输入：intents = ["need_code_context"]
   输出：prefetch_level = "medium"
   
4. 预取文档（multi_agent.py）
   - get_repo_structure() → 目录树
   - repo_map() → 代码地图（中等）
   
5. 主Agent执行
   - 看到 focus_repo_map_content（以打开文件为中心）
   - 看到 repo_map（中等粒度）
   - 理解上下文，解释函数功能
```

---

## 与Cursor的对比

你的系统（daoyoucode）实现了类似Cursor的功能：

| 功能 | Cursor | daoyoucode | 实现位置 |
|------|--------|-----------|---------|
| 意图分类 | ✅ | ✅ | intent.py |
| 动态预取粒度 | ✅ | ✅ | multi_agent.py |
| 指向性（焦点文件） | ✅ | ✅ | executor.py + repo_map |
| 按问检索 | ✅ | ✅ | executor.py + semantic_code_search |
| 智能Agent选择 | ❌ | ✅ | multi_agent.py |
| 辅助Agent协作 | ❌ | ✅ | multi_agent.py |

---

## 关键技术

### 1. PageRank算法（repo_map）

```python
# backend/daoyoucode/agents/tools/repomap_tools.py

def _pagerank(
    graph: Dict[str, Dict[str, float]],
    chat_files: List[str],  # 焦点文件
    mentioned_idents: List[str],  # 提到的标识符
):
    """
    PageRank算法排序
    
    个性化权重：
    - 对话文件（焦点文件）：权重×50
    - 提到的标识符：权重×10
    """
    
    personalization = {}
    for node in nodes:
        weight = 1.0
        
        # 焦点文件权重×50
        if node in chat_files:
            weight *= 50
        
        # 提到的标识符权重×10
        if mentioned_idents:
            # 检查文件中的定义是否包含提到的标识符
            if node in definitions:
                file_defs = definitions[node]
                def_names = {d['name'].lower() for d in file_defs}
                mentioned_lower = {ident.lower() for ident in mentioned_idents}
                
                if def_names.intersection(mentioned_lower):
                    weight *= 10
        
        personalization[node] = weight
    
    # PageRank迭代
    for _ in range(iterations):
        new_scores = {}
        for node in nodes:
            score = (1 - damping) * personalization[node]
            
            # 来自其他节点的分数
            for source, targets in graph.items():
                if node in targets:
                    weight = targets[node]
                    out_weight = sum(targets.values())
                    score += damping * scores[source] * (weight / out_weight)
            
            new_scores[node] = score
        
        scores = new_scores
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### 2. 语义搜索（semantic_code_search）

```python
# 伪代码，实际实现可能在其他地方

async def semantic_code_search(
    query: str,
    top_k: int = 6,
    repo_path: str = "."
):
    """
    语义搜索相关代码块
    
    1. 将代码分块（按函数/类）
    2. 使用embedding模型编码
    3. 计算query与代码块的相似度
    4. 返回top-k最相关的代码块
    """
    
    # 1. 分块
    code_chunks = split_code_into_chunks(repo_path)
    
    # 2. 编码
    query_embedding = embed(query)
    chunk_embeddings = [embed(chunk) for chunk in code_chunks]
    
    # 3. 计算相似度
    similarities = [
        cosine_similarity(query_embedding, chunk_embedding)
        for chunk_embedding in chunk_embeddings
    ]
    
    # 4. 排序并返回top-k
    top_chunks = sorted(
        zip(code_chunks, similarities),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    return format_chunks(top_chunks)
```

---

## 总结

你的系统（daoyoucode）通过以下机制来选择文档：

1. **意图分类** → 理解用户想做什么
2. **动态预取** → 根据意图预取不同粒度的文档
3. **指向性预取** → 根据用户打开的文件预取相关代码
4. **按问检索** → 根据用户问题搜索相关代码
5. **智能Agent选择** → 根据意图选择合适的辅助Agent
6. **工具调用** → Agent动态调用工具获取更多信息

这些机制协同工作，确保LLM能够看到最相关的文档，从而给出准确的答案。

**关键优势**：
- ✅ 节省token（不预取无关文档）
- ✅ 提高准确性（只看相关文档）
- ✅ 提升速度（减少LLM处理时间）
- ✅ 智能化（自动判断需要什么文档）

这就是你的系统如何通过用户意图来确定使用哪些文档的完整机制！
