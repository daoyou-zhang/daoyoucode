# 全项目架构理解优化方案

## 当前问题分析

### 现状

用户问"了解下当前项目"时：
1. LLM调用 `repo_map` (6000 tokens)
2. 得到约100个文件的代码地图
3. 基于代码地图回答

### 问题

1. **只有代码，没有文档**
   - repo_map只包含代码文件（.py, .js等）
   - 遗漏了README.md、ARCHITECTURE.md等重要文档
   - LLM不知道项目的目标、特性、设计理念

2. **信息碎片化**
   - 代码地图是扁平的文件列表
   - 缺少模块间的关系
   - 缺少架构层次

3. **缺少上下文**
   - 不知道项目的技术栈
   - 不知道项目的依赖关系
   - 不知道项目的目录结构含义

---

## 优化方案

### 方案1: 多阶段理解（推荐）⭐

**核心思路**: 分层次、分阶段理解项目

#### 阶段1: 文档层（项目概览）

**目标**: 了解项目是什么、做什么、为什么

**工具**: `discover_project_docs` (新工具)

**功能**:
```python
async def discover_project_docs(repo_path: str) -> ToolResult:
    """
    自动发现并读取项目文档
    
    优先级：
    1. README.md / README.rst
    2. ARCHITECTURE.md / DESIGN.md
    3. CHANGELOG.md / HISTORY.md
    4. docs/index.md
    5. package.json / pyproject.toml (元信息)
    """
    
    docs = []
    
    # 1. README (必读)
    readme = find_readme(repo_path)
    if readme:
        docs.append({
            'type': 'readme',
            'path': readme,
            'content': read_file(readme),
            'summary': extract_summary(readme)  # 提取关键信息
        })
    
    # 2. 架构文档
    arch_doc = find_architecture_doc(repo_path)
    if arch_doc:
        docs.append({
            'type': 'architecture',
            'path': arch_doc,
            'content': read_file(arch_doc)
        })
    
    # 3. 包信息
    package_info = find_package_info(repo_path)
    if package_info:
        docs.append({
            'type': 'package',
            'path': package_info,
            'content': extract_metadata(package_info)  # 只提取关键字段
        })
    
    return format_docs(docs)
```

**输出示例**:
```markdown
# 项目文档

## README.md
项目名称: DaoyouCode
描述: 智能AI代码助手
核心特性:
- 18大核心系统
- 多Agent协作
- 完整记忆系统
...

## 技术栈
- Python 3.8+
- FastAPI
- SQLite
- Tree-sitter
...
```

#### 阶段2: 结构层（目录架构）

**目标**: 了解项目的组织结构

**工具**: `get_repo_structure` (已有，增强)

**增强功能**:
```python
async def get_repo_structure(
    repo_path: str,
    max_depth: int = 3,
    show_files: bool = True,
    annotate: bool = True  # 新参数：添加注释
) -> ToolResult:
    """
    获取目录结构，并添加智能注释
    """
    
    tree = build_tree(repo_path, max_depth, show_files)
    
    if annotate:
        # 根据目录名添加注释
        tree = add_annotations(tree, {
            'backend/': '后端代码',
            'frontend/': '前端代码',
            'docs/': '文档',
            'tests/': '测试',
            'scripts/': '脚本',
            'config/': '配置',
            'agents/': 'Agent系统',
            'tools/': '工具模块',
            'memory/': '记忆系统',
            ...
        })
    
    return tree
```

**输出示例**:
```
daoyoucode/
├── backend/          # 后端代码
│   ├── daoyoucode/   # 核心模块
│   │   ├── agents/   # Agent系统
│   │   │   ├── core/      # 核心组件
│   │   │   ├── tools/     # 工具集
│   │   │   ├── memory/    # 记忆系统
│   │   │   └── orchestrators/  # 编排器
│   │   └── llm/      # LLM客户端
│   └── cli/          # 命令行界面
├── frontend/         # 前端代码
└── docs/            # 文档
```

#### 阶段3: 代码层（核心模块）

**目标**: 了解核心代码的实现

**工具**: `repo_map` (已有)

**使用**: 6000 tokens，显示约100个核心文件

#### 完整流程

```
用户: "了解下当前项目"

LLM思考: 需要全面理解，分3个阶段

阶段1: 读取文档
→ discover_project_docs(repo_path=".")
→ 得到: README + 架构文档 + 技术栈

阶段2: 查看结构
→ get_repo_structure(repo_path=".", annotate=True)
→ 得到: 带注释的目录树

阶段3: 分析代码
→ repo_map(repo_path=".", max_tokens=6000)
→ 得到: 100个核心文件的代码地图

LLM回答: 综合3个阶段的信息，给出完整的项目介绍
```

**优势**:
- ✅ 信息完整（文档+结构+代码）
- ✅ 层次清晰（从宏观到微观）
- ✅ 成本可控（总共约8000 tokens）
- ✅ 易于理解（符合人类认知）

---

### 方案2: 智能摘要（适合大型项目）

**核心思路**: 先生成项目摘要，再按需深入

#### 工具: `generate_project_summary`

```python
async def generate_project_summary(
    repo_path: str,
    llm_client: LLMClient
) -> ToolResult:
    """
    生成项目摘要
    
    步骤：
    1. 读取README
    2. 分析目录结构
    3. 扫描主要文件（入口文件、配置文件）
    4. 使用LLM生成摘要
    """
    
    # 1. 收集信息
    readme = read_readme(repo_path)
    structure = get_structure(repo_path, max_depth=2)
    entry_files = find_entry_files(repo_path)  # main.py, __init__.py等
    config_files = find_config_files(repo_path)  # setup.py, package.json等
    
    # 2. 构建prompt
    prompt = f"""
    请分析以下项目信息，生成一个简洁的项目摘要：
    
    README:
    {readme}
    
    目录结构:
    {structure}
    
    入口文件:
    {entry_files}
    
    配置信息:
    {config_files}
    
    请生成包含以下内容的摘要：
    1. 项目名称和描述
    2. 核心功能（3-5个要点）
    3. 技术栈
    4. 主要模块（5-10个）
    5. 架构特点
    """
    
    # 3. 调用LLM生成摘要
    summary = await llm_client.chat(prompt)
    
    # 4. 缓存摘要（避免重复生成）
    cache_summary(repo_path, summary)
    
    return summary
```

**输出示例**:
```markdown
# DaoyouCode 项目摘要

## 项目描述
智能AI代码助手，提供多Agent协作、完整记忆系统和智能任务路由

## 核心功能
1. 18大核心系统（Agent、Task、Memory等）
2. 7种编排器（Simple、ReAct、Workflow等）
3. 25个工具（repo_map、read_file、grep_search等）
4. 智能记忆系统（短期、长期、用户画像）
5. 流式输出支持

## 技术栈
- Python 3.8+
- FastAPI (Web框架)
- SQLite (缓存和记忆)
- Tree-sitter (代码解析)
- Jinja2 (模板引擎)

## 主要模块
1. agents/core - Agent核心组件
2. agents/orchestrators - 编排器
3. agents/tools - 工具系统
4. agents/memory - 记忆系统
5. agents/llm - LLM客户端
6. cli - 命令行界面

## 架构特点
- 分层架构（Agent → Orchestrator → Tool）
- 插件化设计（Skill系统）
- 缓存优化（SQLite + mtime检测）
- 流式处理（支持实时输出）
```

**优势**:
- ✅ 快速概览（一次调用）
- ✅ 信息浓缩（LLM提炼）
- ✅ 可缓存（避免重复）
- ✅ 适合大型项目

**劣势**:
- ❌ 需要额外的LLM调用
- ❌ 可能遗漏细节
- ❌ 依赖LLM质量

---

### 方案3: 分模块理解（适合模块化项目）

**核心思路**: 按模块分别理解，再汇总

#### 工具: `analyze_module`

```python
async def analyze_module(
    repo_path: str,
    module_path: str,
    llm_client: LLMClient
) -> ToolResult:
    """
    分析单个模块
    
    步骤：
    1. 读取模块的README（如果有）
    2. 生成模块的repo_map
    3. 识别模块的入口和导出
    4. 使用LLM生成模块摘要
    """
    
    # 1. 模块文档
    module_readme = find_module_readme(module_path)
    
    # 2. 模块代码地图
    module_map = await repo_map(
        repo_path=module_path,
        max_tokens=2000  # 单个模块用2000足够
    )
    
    # 3. 入口和导出
    exports = analyze_exports(module_path)  # __init__.py, __all__等
    
    # 4. 生成摘要
    summary = await llm_client.chat(f"""
    分析以下模块：
    
    模块路径: {module_path}
    
    文档:
    {module_readme}
    
    代码地图:
    {module_map}
    
    导出:
    {exports}
    
    请生成模块摘要（功能、主要类/函数、使用方式）
    """)
    
    return summary
```

#### 完整流程

```
用户: "了解下当前项目"

LLM思考: 识别主要模块

步骤1: 识别模块
→ get_repo_structure(repo_path=".", max_depth=2)
→ 识别出: agents/, cli/, llm/, memory/等

步骤2: 分析每个模块
→ analyze_module("agents/")
→ analyze_module("cli/")
→ analyze_module("llm/")
→ ...

步骤3: 汇总
→ 综合各模块的摘要
→ 生成整体架构图

LLM回答: 基于模块分析的完整项目介绍
```

**优势**:
- ✅ 结构清晰（按模块组织）
- ✅ 可并行（多个模块同时分析）
- ✅ 可缓存（模块级缓存）
- ✅ 适合大型项目

**劣势**:
- ❌ 需要多次LLM调用
- ❌ 可能遗漏模块间关系
- ❌ 成本较高

---

## 推荐方案对比

| 方案 | 成本 | 速度 | 完整性 | 适用场景 |
|------|------|------|--------|---------|
| 方案1: 多阶段 | 中 | 快 | ⭐⭐⭐⭐⭐ | 通用，推荐 |
| 方案2: 智能摘要 | 高 | 中 | ⭐⭐⭐⭐ | 大型项目 |
| 方案3: 分模块 | 高 | 慢 | ⭐⭐⭐⭐⭐ | 模块化项目 |

---

## 推荐实现：方案1（多阶段理解）

### 为什么选择方案1？

1. **成本可控**
   - 文档层: ~1000 tokens
   - 结构层: ~500 tokens
   - 代码层: ~6000 tokens
   - 总计: ~7500 tokens

2. **信息完整**
   - 有文档（项目概览）
   - 有结构（目录架构）
   - 有代码（核心实现）

3. **易于实现**
   - 复用现有工具（repo_map, get_repo_structure）
   - 只需新增 discover_project_docs
   - 不需要额外的LLM调用

4. **符合认知**
   - 从宏观到微观
   - 从文档到代码
   - 层次清晰

### 需要实现的工具

#### 1. discover_project_docs（新工具）

**功能**: 自动发现并读取项目文档

**优先级**:
1. README.md / README.rst / README.txt
2. ARCHITECTURE.md / DESIGN.md / STRUCTURE.md
3. CHANGELOG.md / HISTORY.md / RELEASES.md
4. docs/index.md / docs/README.md
5. package.json / pyproject.toml / setup.py (元信息)

**智能提取**:
- README: 提取项目名、描述、特性、安装、使用
- 架构文档: 提取架构图、模块说明
- 包信息: 提取名称、版本、依赖、脚本

**输出格式**:
```markdown
# 项目文档摘要

## 基本信息
- 名称: DaoyouCode
- 版本: 0.1.0
- 描述: 智能AI代码助手

## 核心特性
1. 18大核心系统
2. 多Agent协作
3. 完整记忆系统
...

## 技术栈
- Python 3.8+
- FastAPI
- SQLite
...

## 架构说明
（来自ARCHITECTURE.md）
...
```

#### 2. get_repo_structure（增强现有工具）

**新增功能**: 智能注释

**实现**:
```python
# 预定义的目录注释
DIRECTORY_ANNOTATIONS = {
    'backend': '后端代码',
    'frontend': '前端代码',
    'src': '源代码',
    'lib': '库文件',
    'tests': '测试',
    'docs': '文档',
    'scripts': '脚本',
    'config': '配置',
    'agents': 'Agent系统',
    'tools': '工具模块',
    'memory': '记忆系统',
    'orchestrators': '编排器',
    'llm': 'LLM客户端',
    'cli': '命令行界面',
    'api': 'API接口',
    'models': '数据模型',
    'utils': '工具函数',
    'core': '核心组件',
    ...
}

# 根据目录名匹配注释
def annotate_directory(dir_name: str) -> str:
    for pattern, annotation in DIRECTORY_ANNOTATIONS.items():
        if pattern in dir_name.lower():
            return f"{dir_name}/  # {annotation}"
    return f"{dir_name}/"
```

#### 3. repo_map（已有，无需修改）

**使用**: 
- max_tokens=6000（无chat_files时自动扩大）
- 显示约100个核心文件

### 提示词更新

```markdown
## 项目理解最佳实践

当用户问"了解项目"、"项目架构"、"项目是做什么的"时，使用3阶段理解：

### 阶段1: 文档层（必须）
调用 discover_project_docs(repo_path=".")
- 了解项目概览、特性、技术栈
- 约1000 tokens

### 阶段2: 结构层（推荐）
调用 get_repo_structure(repo_path=".", annotate=True)
- 了解目录组织、模块划分
- 约500 tokens

### 阶段3: 代码层（可选）
调用 repo_map(repo_path=".", max_tokens=6000)
- 了解核心代码实现
- 约6000 tokens

### 回答策略
综合3个阶段的信息：
1. 项目概述（来自文档）
2. 架构说明（来自结构+代码）
3. 核心模块（来自代码地图）
4. 技术特点（综合分析）
```

---

## 其他优化建议

### 1. 缓存项目摘要

```python
# 第一次理解项目时，生成并缓存摘要
cache_key = f"project_summary:{repo_path}:{mtime}"
if cache_exists(cache_key):
    return get_cache(cache_key)

# 生成摘要
summary = generate_summary(docs, structure, code_map)

# 缓存（24小时）
set_cache(cache_key, summary, ttl=86400)
```

### 2. 增量更新

```python
# 检测项目变化
if project_changed_since_last_summary():
    # 只更新变化的部分
    update_summary_incrementally()
else:
    # 使用缓存
    return cached_summary
```

### 3. 可视化架构图

```python
# 生成Mermaid图
def generate_architecture_diagram(modules):
    """
    生成架构图（Mermaid格式）
    """
    diagram = "graph TD\n"
    
    for module in modules:
        diagram += f"  {module.name}[{module.description}]\n"
        for dep in module.dependencies:
            diagram += f"  {module.name} --> {dep}\n"
    
    return diagram
```

### 4. 交互式探索

```python
# 用户可以深入某个模块
用户: "详细说说agents模块"

LLM: 调用 analyze_module("agents/")
→ 生成agents模块的详细分析
```

---

## 总结

### 推荐方案：多阶段理解

**阶段1**: discover_project_docs（文档层）
**阶段2**: get_repo_structure（结构层）
**阶段3**: repo_map（代码层）

### 优势

- ✅ 信息完整（文档+结构+代码）
- ✅ 成本可控（~7500 tokens）
- ✅ 易于实现（复用现有工具）
- ✅ 符合认知（从宏观到微观）

### 需要实现

1. **新工具**: discover_project_docs
2. **增强**: get_repo_structure 添加注释
3. **更新**: 提示词添加3阶段流程

### 预期效果

用户问"了解下当前项目"时：
- 得到完整的项目介绍（概述+架构+代码）
- 理解项目的目标、特性、实现
- 知道如何深入某个模块
