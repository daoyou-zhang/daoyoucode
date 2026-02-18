# RepoMap公开API使用指南

## 概述

RepoMap现在提供了3个公开API，供其他模块（如codebase_index、智能检索等）使用，避免重复解析代码。

---

## API列表

### 1. get_definitions()

获取代码定义（函数、类、方法等）

**签名**:
```python
def get_definitions(
    self,
    repo_path: str,
    use_cache: bool = True
) -> Dict[str, List[Dict]]
```

**参数**:
- `repo_path`: 仓库路径（使用 "." 表示当前目录）
- `use_cache`: 是否使用缓存（默认True）

**返回**:
```python
{
    "backend/agents/core/agent.py": [
        {
            "type": "class",           # 类型：class, function, method
            "name": "BaseAgent",       # 名称
            "line": 50,                # 起始行（1-based）
            "end_line": 150,           # 结束行（1-based）
            "kind": "def",             # 定义或引用：def, ref
            "parent": None,            # 父级（如类名）
            "scope": "global"          # 作用域：global, class, function
        },
        {
            "type": "method",
            "name": "execute",
            "line": 100,
            "end_line": 145,
            "kind": "def",
            "parent": "BaseAgent",
            "scope": "class"
        }
    ]
}
```

**使用示例**:
```python
from daoyoucode.agents.tools.repomap_tools import RepoMapTool

repomap = RepoMapTool()
definitions = repomap.get_definitions(".")

# 遍历所有文件
for file_path, defs in definitions.items():
    print(f"文件: {file_path}")
    
    # 只处理定义，不处理引用
    for d in defs:
        if d.get("kind") == "def":
            print(f"  {d['type']} {d['name']} (line {d['line']}-{d['end_line']})")
```

**输出示例**:
```
文件: backend/agents/core/agent.py
  class BaseAgent (line 50-150)
  method execute (line 100-145)
  method _load_prompt (line 160-180)
```

---

### 2. get_reference_graph()

获取引用图（文件之间的引用关系）

**签名**:
```python
def get_reference_graph(
    self,
    repo_path: str,
    definitions: Optional[Dict[str, List[Dict]]] = None
) -> Dict[str, Dict[str, float]]
```

**参数**:
- `repo_path`: 仓库路径
- `definitions`: 代码定义（如果为None，会自动调用get_definitions()）

**返回**:
```python
{
    "file_a.py": {
        "file_b.py": 3.0,  # file_a引用file_b 3次
        "file_c.py": 1.0   # file_a引用file_c 1次
    },
    "file_b.py": {
        "file_c.py": 2.0
    }
}
```

**使用示例**:
```python
repomap = RepoMapTool()

# 方法1：自动获取definitions
reference_graph = repomap.get_reference_graph(".")

# 方法2：复用已有的definitions
definitions = repomap.get_definitions(".")
reference_graph = repomap.get_reference_graph(".", definitions)

# 查看某个文件引用了哪些文件
file_path = "backend/agents/core/agent.py"
if file_path in reference_graph:
    print(f"{file_path} 引用了:")
    for target, count in reference_graph[file_path].items():
        print(f"  {target}: {count}次")
```

**输出示例**:
```
backend/agents/core/agent.py 引用了:
  backend/agents/llm/client_manager.py: 3次
  backend/agents/tools/registry.py: 2次
  backend/agents/memory/long_term_memory.py: 1次
```

---

### 3. get_pagerank_scores()

获取PageRank分数（代码重要性排序）

**签名**:
```python
def get_pagerank_scores(
    self,
    repo_path: str,
    reference_graph: Optional[Dict] = None,
    definitions: Optional[Dict] = None,
    chat_files: Optional[List[str]] = None,
    mentioned_idents: Optional[List[str]] = None
) -> Dict[str, float]
```

**参数**:
- `repo_path`: 仓库路径
- `reference_graph`: 引用图（如果为None，会自动获取）
- `definitions`: 代码定义（如果为None，会自动获取）
- `chat_files`: 焦点文件（权重×50）
- `mentioned_idents`: 提到的标识符（权重×10）

**返回**:
```python
{
    "file_a.py": 0.85,  # PageRank分数（0-1）
    "file_b.py": 0.65,
    "file_c.py": 0.42
}
```

**使用示例**:
```python
repomap = RepoMapTool()

# 方法1：基础PageRank（无焦点）
pagerank_scores = repomap.get_pagerank_scores(".")

# 方法2：带焦点文件（提升相关文件的分数）
pagerank_scores = repomap.get_pagerank_scores(
    ".",
    chat_files=["backend/agents/core/agent.py"]
)

# 方法3：带提到的标识符（提升包含这些标识符的文件分数）
pagerank_scores = repomap.get_pagerank_scores(
    ".",
    mentioned_idents=["execute", "timeout", "BaseAgent"]
)

# 排序并显示Top 10
sorted_files = sorted(
    pagerank_scores.items(),
    key=lambda x: x[1],
    reverse=True
)

print("Top 10 最重要的文件:")
for i, (file_path, score) in enumerate(sorted_files[:10], 1):
    print(f"{i}. {score:.4f} - {file_path}")
```

**输出示例**:
```
Top 10 最重要的文件:
1. 0.8500 - backend/agents/core/agent.py
2. 0.6500 - backend/agents/llm/client_manager.py
3. 0.4200 - backend/agents/tools/registry.py
4. 0.3800 - backend/agents/memory/long_term_memory.py
5. 0.3500 - backend/agents/core/context.py
```

---

## 完整示例：构建代码索引

```python
from pathlib import Path
from daoyoucode.agents.tools.repomap_tools import RepoMapTool

def build_code_index(repo_path: str):
    """使用RepoMap API构建代码索引"""
    
    repomap = RepoMapTool()
    
    # 1. 获取代码定义
    print("🔍 解析代码结构...")
    definitions = repomap.get_definitions(repo_path)
    print(f"✅ 找到 {len(definitions)} 个文件")
    
    # 2. 获取引用图
    print("🔗 构建引用图...")
    reference_graph = repomap.get_reference_graph(repo_path, definitions)
    print(f"✅ 构建了 {len(reference_graph)} 个节点的引用图")
    
    # 3. 计算PageRank分数
    print("📊 计算PageRank分数...")
    pagerank_scores = repomap.get_pagerank_scores(
        repo_path,
        reference_graph=reference_graph,
        definitions=definitions
    )
    print(f"✅ 计算了 {len(pagerank_scores)} 个文件的分数")
    
    # 4. 构建索引
    chunks = []
    for file_path, defs in definitions.items():
        for d in defs:
            if d.get("kind") != "def":
                continue  # 只要定义，不要引用
            
            # 读取代码文本
            code_text = extract_code_text(
                Path(repo_path) / file_path,
                d["line"],
                d.get("end_line", d["line"] + 50)
            )
            
            # 构建chunk
            chunk = {
                "path": file_path,
                "start": d["line"],
                "end": d.get("end_line"),
                "text": code_text,
                "type": d.get("type"),
                "name": d.get("name"),
                "pagerank_score": pagerank_scores.get(file_path, 0.0)
            }
            
            chunks.append(chunk)
    
    print(f"✅ 构建了 {len(chunks)} 个代码块")
    return chunks


def extract_code_text(file_path: Path, start_line: int, end_line: int) -> str:
    """提取代码文本"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 转为0-based索引
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        # 向上扩展：包含装饰器和注释
        while start_idx > 0:
            prev_line = lines[start_idx - 1].strip()
            if prev_line.startswith('@') or prev_line.startswith('#'):
                start_idx -= 1
            else:
                break
        
        return ''.join(lines[start_idx:end_idx])
    
    except Exception as e:
        return ""


# 使用
if __name__ == "__main__":
    chunks = build_code_index(".")
    print(f"\n示例chunk:")
    print(chunks[0])
```

**输出**:
```
🔍 解析代码结构...
✅ 找到 214 个文件
🔗 构建引用图...
✅ 构建了 187 个节点的引用图
📊 计算PageRank分数...
✅ 计算了 194 个文件的分数
✅ 构建了 1849 个代码块

示例chunk:
{
    'path': 'backend/agents/core/agent.py',
    'start': 50,
    'end': 150,
    'text': 'class BaseAgent:\n    """基础Agent类"""\n    ...',
    'type': 'class',
    'name': 'BaseAgent',
    'pagerank_score': 0.85
}
```

---

## 性能优化建议

### 1. 复用结果

```python
# ❌ 不好：重复调用
definitions = repomap.get_definitions(".")
reference_graph = repomap.get_reference_graph(".")  # 会再次调用get_definitions
pagerank_scores = repomap.get_pagerank_scores(".")  # 会再次调用get_definitions和get_reference_graph

# ✅ 好：复用结果
definitions = repomap.get_definitions(".")
reference_graph = repomap.get_reference_graph(".", definitions)
pagerank_scores = repomap.get_pagerank_scores(".", reference_graph, definitions)
```

---

### 2. 使用缓存

```python
# 第一次调用：解析并缓存
definitions = repomap.get_definitions(".", use_cache=True)  # 慢

# 第二次调用：从缓存读取
definitions = repomap.get_definitions(".", use_cache=True)  # 快
```

---

### 3. 只处理定义

```python
# 定义和引用都会返回，但通常只需要定义
for file_path, defs in definitions.items():
    for d in defs:
        if d.get("kind") == "def":  # 只处理定义
            # ...
```

---

## 常见问题

### Q1: end_line为什么是None？

A: 只有定义（kind="def"）才有end_line，引用（kind="ref"）没有end_line。

```python
for d in defs:
    if d.get("kind") == "def":
        print(f"{d['name']}: {d['line']}-{d['end_line']}")  # ✅ 有end_line
    else:
        print(f"{d['name']}: {d['line']}")  # ❌ 没有end_line
```

---

### Q2: 如何过滤特定类型的定义？

A: 使用type字段过滤。

```python
# 只要类定义
classes = [d for d in defs if d.get("type") == "class" and d.get("kind") == "def"]

# 只要函数定义
functions = [d for d in defs if d.get("type") == "function" and d.get("kind") == "def"]

# 只要方法定义
methods = [d for d in defs if d.get("type") == "method" and d.get("kind") == "def"]
```

---

### Q3: PageRank分数的范围是多少？

A: 通常在0-1之间，但没有严格的上限。分数越高，文件越重要。

```python
# 归一化到0-1
scores = repomap.get_pagerank_scores(".")
max_score = max(scores.values())
normalized_scores = {k: v / max_score for k, v in scores.items()}
```

---

### Q4: 如何提升特定文件的分数？

A: 使用chat_files参数（权重×50）或mentioned_idents参数（权重×10）。

```python
# 提升特定文件的分数
scores = repomap.get_pagerank_scores(
    ".",
    chat_files=["backend/agents/core/agent.py"]
)

# 提升包含特定标识符的文件分数
scores = repomap.get_pagerank_scores(
    ".",
    mentioned_idents=["execute", "BaseAgent"]
)
```

---

## 总结

RepoMap公开API提供了：

1. ✅ 精确的代码定义（基于tree-sitter）
2. ✅ 完整的引用关系（文件级别）
3. ✅ 智能的重要性排序（PageRank）
4. ✅ 高效的缓存机制（避免重复解析）
5. ✅ 清晰的接口设计（易于使用）

**适用场景**:
- 代码索引构建
- 智能检索
- 代码分析
- 依赖关系可视化
- 代码质量评估

**下一步**:
- 在实际项目中使用这些API
- 根据反馈优化API设计
- 扩展更多功能（如增量更新）
