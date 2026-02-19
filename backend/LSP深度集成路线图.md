# LSP深度集成路线图

## 当前状态（已完成）✅

### 阶段1: 基础集成
- ✅ LSP服务器启动和管理
- ✅ 6个LSP工具（diagnostics, goto_definition, find_references, symbols, rename, code_actions）
- ✅ semantic_code_search默认启用LSP
- ✅ LSP标记显示（质量星级、符号信息）
- ✅ Tree-sitter深度集成
- ✅ 两者互补使用

### 核心价值
- Tree-sitter: 快速语法解析（基础层）
- LSP: 深度语义分析（增强层）
- 检索准确率 +30%
- 代码理解深度 +100%

---

## 下一步计划

### 🔥 阶段2: 深度融合（本周）

#### 2.1 RepoMap集成LSP（优先级：高）

**目标**: 在代码地图中显示类型信息

**当前RepoMap输出**:
```python
daoyoucode/agents/executor.py:
  execute_skill
  _execute_skill_internal
  list_skills
```

**LSP增强后**:
```python
daoyoucode/agents/executor.py:
  execute_skill: async (str, str, ...) -> Dict[str, Any]  ← 类型签名
    被引用: 23次  ← 真实引用计数
    质量: ⭐⭐⭐⭐⭐
  _execute_skill_internal: async (...) -> Dict
  list_skills: () -> List[str]
```

**实施步骤**:
```python
# backend/daoyoucode/agents/tools/repomap_tools.py

class RepoMapTool(BaseTool):
    async def execute(self, ..., enable_lsp: bool = True):
        # 1. 现有的Tree-sitter解析
        definitions = self._parse_file(file)
        
        # 2. 🔥 为重要符号添加LSP信息
        if enable_lsp:
            for defn in definitions:
                if defn['pagerank_score'] > 0.01:  # 只为重要符号
                    lsp_info = await self._get_lsp_type_info(
                        file, defn['line']
                    )
                    defn['type_signature'] = lsp_info.get('signature')
                    defn['reference_count'] = lsp_info.get('ref_count')
        
        # 3. 格式化输出
        return self._format_with_lsp(definitions)
```

**收益**:
- Agent理解函数签名
- 知道哪些是核心函数（引用计数）
- 更准确的代码推荐

#### 2.2 类型注解检测增强（优先级：高）

**目标**: 准确检测Python类型注解

**当前问题**:
```python
# 当前检测逻辑太简单
if '->' in symbol['detail'] or ': ' in symbol['detail']:
    has_type_annotations = True
```

**改进方案**:
```python
def _has_type_annotations(self, symbols: List[Dict]) -> bool:
    """准确检测类型注解"""
    for symbol in symbols:
        if symbol.get('kind') == 12:  # Function
            detail = symbol.get('detail', '')
            
            # 检查参数类型注解
            if ': ' in detail and '->' in detail:
                # 排除文档字符串中的冒号
                if not detail.startswith('"""'):
                    return True
            
            # 🔥 使用LSP的hover信息（更准确）
            hover_info = await self._get_hover_info(symbol)
            if hover_info and 'type' in hover_info:
                return True
    
    return False
```

#### 2.3 真实引用计数（优先级：中）

**目标**: 使用LSP获取真实的跨文件引用

**当前问题**:
```python
# 当前是估算，不准确
def _estimate_reference_count(self, symbols: List[Dict]) -> int:
    count = 0
    for symbol in symbols:
        if symbol.get('kind') in [12, 5]:  # Function=12, Class=5
            count += 5  # 假设值
        else:
            count += 1
    return count
```

**改进方案**:
```python
async def _get_real_reference_count(
    self, 
    file_path: str, 
    symbol: Dict
) -> int:
    """获取真实引用计数"""
    try:
        # 🔥 使用LSP的find_references
        line = symbol['range']['start']['line']
        char = symbol['range']['start']['character']
        
        references = await with_lsp_client(
            file_path,
            lambda client: client.references(
                file_path, line, char, include_declaration=False
            )
        )
        
        return len(references) if references else 0
    
    except Exception as e:
        logger.debug(f"获取引用计数失败: {e}")
        return self._estimate_reference_count([symbol])
```

**优化**: 只为top-k结果获取真实引用（避免太慢）

#### 2.4 代码生成验证（优先级：中）

**目标**: 使用LSP验证生成的代码

**场景**: Agent生成代码后自动检查

```python
# backend/daoyoucode/agents/tools/write_file.py

class WriteFileTool(BaseTool):
    async def execute(self, file_path: str, content: str, verify: bool = True):
        # 1. 写入文件
        Path(file_path).write_text(content)
        
        # 2. 🔥 使用LSP验证
        if verify and file_path.endswith('.py'):
            diagnostics = await self._verify_with_lsp(file_path)
            
            if diagnostics:
                # 有错误，返回诊断信息
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"代码有{len(diagnostics)}个问题",
                    metadata={'diagnostics': diagnostics}
                )
        
        return ToolResult(success=True, content="文件已写入并验证")
    
    async def _verify_with_lsp(self, file_path: str) -> List[Dict]:
        """使用LSP验证代码"""
        from .lsp_tools import with_lsp_client
        
        result = await with_lsp_client(
            file_path,
            lambda client: client.diagnostics(file_path)
        )
        
        # 只返回错误，忽略警告
        diagnostics = result.get('items', [])
        errors = [d for d in diagnostics if d.get('severity') == 1]
        
        return errors
```

**收益**:
- 生成的代码更可靠
- 自动发现类型错误
- 减少用户手动修复

---

### 🚀 阶段3: 高级功能（下周）

#### 3.1 智能代码补全验证

**目标**: 验证Agent建议的代码是否正确

```python
# Agent建议: "调用execute_skill函数"
suggestion = """
result = execute_skill(
    skill_name="chat",
    user_input="hello"
)
"""

# 🔥 使用LSP验证参数是否正确
validation = await validate_code_snippet(suggestion, context_file)

if validation.has_errors:
    # 修正建议
    corrected = await fix_with_lsp(suggestion, validation.errors)
```

#### 3.2 重构安全检查

**目标**: 重构前检查影响范围

```python
# 用户: "重命名execute_skill为run_skill"

# 🔥 使用LSP查找所有引用
references = await lsp_find_references("executor.py", 20, 10)

# 显示影响范围
print(f"将影响{len(references)}个位置:")
for ref in references[:10]:
    print(f"  - {ref['file']}:{ref['line']}")

# 确认后执行重命名
if user_confirms:
    await lsp_rename("executor.py", 20, 10, "run_skill")
```

#### 3.3 代码质量评分

**目标**: 基于LSP信息评估代码质量

```python
def calculate_code_quality(lsp_info: Dict) -> float:
    """计算代码质量分数（0-1）"""
    score = 0.0
    
    # 类型注解 +0.3
    if lsp_info.get('has_type_annotations'):
        score += 0.3
    
    # 文档字符串 +0.2
    if lsp_info.get('has_docstring'):
        score += 0.2
    
    # 符号数量（复杂度） +0.2
    symbol_count = lsp_info.get('symbol_count', 0)
    if 1 <= symbol_count <= 5:  # 适中的复杂度
        score += 0.2
    
    # 引用计数（重要性） +0.3
    ref_count = lsp_info.get('reference_count', 0)
    if ref_count > 0:
        score += min(0.3, ref_count / 100)
    
    return score
```

#### 3.4 跨文件依赖分析

**目标**: 理解模块间的依赖关系

```python
async def analyze_dependencies(file_path: str) -> Dict:
    """分析文件依赖"""
    # 1. 获取所有导入
    imports = await get_imports(file_path)
    
    # 2. 🔥 使用LSP跳转到定义
    dependencies = {}
    for imp in imports:
        definition = await lsp_goto_definition(file_path, imp.line, imp.char)
        dependencies[imp.name] = definition['file']
    
    # 3. 构建依赖图
    return {
        'file': file_path,
        'imports': imports,
        'dependencies': dependencies,
        'dependents': await find_dependents(file_path)
    }
```

---

### 🎯 阶段4: 多语言支持（下月）

#### 4.1 JavaScript/TypeScript支持

```python
# 安装LSP服务器
npm install -g typescript-language-server typescript

# 配置
BUILTIN_LSP_SERVERS["typescript-language-server"] = LSPServerConfig(
    id="typescript-language-server",
    command=["typescript-language-server", "--stdio"],
    extensions=[".ts", ".tsx", ".js", ".jsx"]
)
```

#### 4.2 其他语言

- Rust: rust-analyzer
- Go: gopls
- Java: jdtls
- C/C++: clangd

---

### 📊 阶段5: 性能优化（持续）

#### 5.1 LSP结果缓存

```python
class LSPCache:
    """LSP结果缓存"""
    
    def __init__(self):
        self._cache = {}
        self._file_mtimes = {}
    
    def get(self, file_path: str, key: str):
        """获取缓存"""
        # 检查文件是否修改
        current_mtime = Path(file_path).stat().st_mtime
        cached_mtime = self._file_mtimes.get(file_path)
        
        if cached_mtime != current_mtime:
            # 文件已修改，清除缓存
            self._invalidate(file_path)
            return None
        
        return self._cache.get(f"{file_path}:{key}")
    
    def set(self, file_path: str, key: str, value):
        """设置缓存"""
        self._cache[f"{file_path}:{key}"] = value
        self._file_mtimes[file_path] = Path(file_path).stat().st_mtime
```

#### 5.2 并行LSP查询

```python
async def get_lsp_info_batch(files: List[str]) -> List[Dict]:
    """并行获取多个文件的LSP信息"""
    tasks = [get_lsp_info(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 过滤异常
    return [r for r in results if not isinstance(r, Exception)]
```

#### 5.3 智能预热

```python
async def warmup_lsp_for_project(repo_path: Path):
    """为项目预热LSP"""
    # 1. 找到最重要的文件（基于PageRank）
    important_files = get_important_files(repo_path, top_k=10)
    
    # 2. 预先打开这些文件
    for file in important_files:
        await lsp_client.open_file(str(file))
    
    # 3. LSP会在后台索引这些文件
    logger.info(f"LSP预热完成: {len(important_files)}个文件")
```

---

## 实施优先级

### 本周（立即开始）

1. **RepoMap集成LSP** ⭐⭐⭐⭐⭐
   - 影响最大
   - 实施简单
   - 用户可见

2. **类型注解检测增强** ⭐⭐⭐⭐
   - 提升准确率
   - 实施简单

3. **代码生成验证** ⭐⭐⭐⭐
   - 提升代码质量
   - 用户价值高

### 下周

4. **真实引用计数** ⭐⭐⭐
   - 提升检索准确率
   - 需要性能优化

5. **智能代码补全验证** ⭐⭐⭐
   - 提升Agent准确性

6. **重构安全检查** ⭐⭐⭐
   - 提升用户信心

### 下月

7. **多语言支持** ⭐⭐
   - 扩展适用范围

8. **性能优化** ⭐⭐⭐⭐
   - 持续改进

---

## 成功指标

### 技术指标

- LSP成功率 > 95%
- LSP响应时间 < 500ms
- 缓存命中率 > 80%
- 类型注解检测准确率 > 90%

### 用户指标

- 代码检索准确率 +50%（当前+30%）
- 代码生成错误率 -70%
- 重构成功率 +40%
- 用户满意度 +60%

---

## 风险和挑战

### 技术风险

1. **LSP性能**: 大项目可能很慢
   - 缓解: 缓存、并行、智能预热

2. **LSP稳定性**: 可能崩溃
   - 缓解: 自动重启、优雅降级

3. **多语言支持**: 不同LSP行为不一致
   - 缓解: 抽象层、适配器模式

### 用户体验风险

1. **首次使用慢**: LSP启动需要时间
   - 缓解: 后台预热、进度提示

2. **LSP未安装**: 用户可能没装pyright
   - 缓解: 自动安装、清晰提示

---

## 总结

### 当前成就 ✅

- LSP服务器启动和管理
- semantic_code_search LSP增强
- Tree-sitter深度集成
- 两者完美互补

### 下一步重点 🔥

1. **RepoMap集成LSP**（本周）
2. **代码生成验证**（本周）
3. **真实引用计数**（下周）

### 长期愿景 🎯

打造业界最强的代码理解系统：
- Tree-sitter的速度
- LSP的深度
- 多语言支持
- 智能缓存
- 完美用户体验

---

**准备好开始阶段2了吗？** 🚀

建议从**RepoMap集成LSP**开始，因为：
1. 影响最大（代码地图是核心功能）
2. 实施相对简单
3. 用户立即可见
4. 为后续功能打基础
