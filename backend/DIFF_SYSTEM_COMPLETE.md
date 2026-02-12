# Diff系统完成总结

> 基于opencode最先进的9种Replacer策略实现

**完成时间**: 2025-02-12  
**状态**: ✅ 完成  
**测试**: 20个测试场景，全部通过

---

## 一、核心实现

### 1.1 Levenshtein距离算法

```python
def levenshtein(a: str, b: str) -> int:
    """计算两个字符串的编辑距离"""
    # 动态规划实现
    # 用于衡量字符串相似度
```

**用途**: BlockAnchorReplacer中计算中间行相似度

### 1.2 9种Replacer策略

| 策略 | 名称 | 功能 | 来源 |
|------|------|------|------|
| 1 | SimpleReplacer | 精确匹配 | opencode |
| 2 | LineTrimmedReplacer | 忽略行首尾空白 | opencode |
| 3 | BlockAnchorReplacer | 首尾行锚定+Levenshtein相似度 | opencode ⭐ |
| 4 | WhitespaceNormalizedReplacer | 空白归一化 | opencode |
| 5 | IndentationFlexibleReplacer | 缩进灵活匹配 | opencode |
| 6 | EscapeNormalizedReplacer | 转义字符处理 | opencode |
| 7 | TrimmedBoundaryReplacer | 边界trim | opencode |
| 8 | ContextAwareReplacer | 上下文感知 | opencode |
| 9 | MultiOccurrenceReplacer | 多次出现处理 | opencode |

### 1.3 BlockAnchorReplacer（最强大）

**核心算法**:
1. 使用首尾行作为锚点
2. 计算中间行的Levenshtein相似度
3. 单候选阈值0.0（宽松）
4. 多候选阈值0.3（严格）

```python
# 单候选情况
if len(candidates) == 1:
    similarity = calculate_similarity(middle_lines)
    if similarity >= 0.0:  # 宽松阈值
        yield match

# 多候选情况
best_match = max(candidates, key=lambda c: calculate_similarity(c))
if best_match.similarity >= 0.3:  # 严格阈值
    yield best_match
```

**优势**:
- 容忍中间行的微小差异
- 自动选择最佳匹配
- 避免误匹配

---

## 二、核心函数

### 2.1 replace函数

```python
def replace(content: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """使用9种策略进行智能替换"""
    # 按优先级尝试9种策略
    for replacer_class in [
        SimpleReplacer,
        LineTrimmedReplacer,
        BlockAnchorReplacer,
        WhitespaceNormalizedReplacer,
        IndentationFlexibleReplacer,
        EscapeNormalizedReplacer,
        TrimmedBoundaryReplacer,
        ContextAwareReplacer,
        MultiOccurrenceReplacer,
    ]:
        for search in replacer_class.find_matches(content, old_string):
            # 执行替换
            return content.replace(search, new_string)
```

**特性**:
- 自动尝试9种策略
- 找到第一个匹配即返回
- 支持replace_all模式
- 详细的错误提示

### 2.2 SearchReplaceTool

```python
class SearchReplaceTool(BaseTool):
    """SEARCH/REPLACE编辑工具"""
    
    async def execute(self, file_path, search, replace, replace_all=False):
        # 读取文件
        content = path.read_text()
        # 执行替换
        new_content = replace(content, search, replace, replace_all)
        # 写入文件
        path.write_text(new_content)
```

**集成**:
- 已注册到工具注册表
- 支持Function Calling
- 完整的错误处理

---

## 三、测试覆盖

### 3.1 测试场景（20个）

**Levenshtein距离测试**（4个）:
- ✅ 相同字符串
- ✅ 空字符串
- ✅ 单字符差异
- ✅ 多字符差异

**Replacer策略测试**（6个）:
- ✅ SimpleReplacer - 精确匹配
- ✅ LineTrimmedReplacer - 忽略空白
- ✅ BlockAnchorReplacer - 单候选
- ✅ BlockAnchorReplacer - 多候选
- ✅ WhitespaceNormalizedReplacer - 空白归一化
- ✅ IndentationFlexibleReplacer - 缩进灵活

**replace函数测试**（7个）:
- ✅ 简单替换
- ✅ 带空白替换
- ✅ 多行替换
- ✅ 缩进灵活替换
- ✅ 找不到匹配
- ✅ 多个匹配（应该失败）
- ✅ 替换所有

**SearchReplaceTool测试**（3个）:
- ✅ 基本替换
- ✅ 文件不存在
- ✅ 缩进灵活替换

---

## 四、与其他项目对比

### 4.1 opencode vs daoyouCodePilot

| 维度 | opencode | daoyouCodePilot |
|------|----------|-----------------|
| **策略数量** | 9种 | 4种 |
| **相似度算法** | Levenshtein距离 | 简单匹配 |
| **BlockAnchor** | ✅ 首尾行锚定 | ❌ 无 |
| **阈值控制** | ✅ 单/多候选不同阈值 | ❌ 无 |
| **代码质量** | TypeScript + 完整测试 | Python |
| **代码行数** | 1000+ | 500+ |

### 4.2 为什么选择opencode

1. **策略更多** - 9种 vs 4种
2. **算法更先进** - Levenshtein距离
3. **容错更强** - BlockAnchorReplacer
4. **代码更优** - TypeScript类型安全

---

## 五、使用示例

### 5.1 基本使用

```python
from daoyoucode.agents.tools import get_tool_registry

registry = get_tool_registry()
tool = registry.get_tool("search_replace")

result = await tool.execute(
    file_path="test.py",
    search='print("Hello")',
    replace='print("Hi")'
)
```

### 5.2 缩进灵活匹配

```python
# 原文件（有缩进）
"""
    def hello():
        print("Hello")
"""

# 搜索（无缩进）
search = """def hello():
    print("Hello")"""

# 也能匹配！IndentationFlexibleReplacer会处理
```

### 5.3 首尾行锚定

```python
# 原文件
"""
def func1():
    print("A")
    return 1

def func2():
    print("B")
    return 2
"""

# 搜索（只需首尾行精确，中间行可以有差异）
search = """def func1():
    print("A")
    return 1"""

# BlockAnchorReplacer会找到最佳匹配
```

---

## 六、总结

### 6.1 完成情况

- ✅ Levenshtein距离算法
- ✅ 9种Replacer策略
- ✅ replace核心函数
- ✅ SearchReplaceTool工具
- ✅ 20个测试场景全部通过
- ✅ 集成到工具注册表

### 6.2 核心优势

1. **最先进** - 采用opencode的9种策略
2. **最智能** - BlockAnchorReplacer + Levenshtein
3. **最容错** - 多种策略自动尝试
4. **最可靠** - 20个测试全部通过

### 6.3 下一步

**实现RepoMap系统**（采用daoyouCodePilot的PageRank排序），这是第二核心功能。
