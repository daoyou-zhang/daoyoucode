# 智能工具后处理系统设计

## 核心理念

**问题**：LLM自动调用工具时，返回的原始结果往往：
1. 包含大量无关信息
2. 没有针对用户问题进行优化
3. 浪费大量tokens

**解决方案**：在工具执行后，基于用户意图和上下文，智能地处理结果

## 架构设计

```
用户问题 → LLM决策 → 调用工具 → 原始结果 → 智能后处理 → 优化结果 → LLM理解
                                        ↑
                                   用户意图分析
                                   上下文理解
                                   语义相关性
```

## 核心组件

### 1. 工具后处理器（ToolPostProcessor）

```python
class ToolPostProcessor:
    """
    工具后处理器基类
    
    职责：
    - 分析用户意图
    - 提取关键信息
    - 语义过滤
    - 智能摘要
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # 用于语义分析
    
    async def process(
        self,
        tool_name: str,
        tool_result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        处理工具结果
        
        Args:
            tool_name: 工具名称
            tool_result: 原始工具结果
            user_query: 用户问题
            context: 上下文信息
        
        Returns:
            优化后的工具结果
        """
        # 1. 提取用户意图
        intent = self._extract_intent(user_query, context)
        
        # 2. 根据工具类型选择处理策略
        processor = self._get_processor(tool_name)
        
        # 3. 智能处理
        processed_result = await processor.process(
            tool_result,
            intent,
            context
        )
        
        return processed_result
```

### 2. 意图提取器（IntentExtractor）

```python
class IntentExtractor:
    """
    从用户问题中提取意图
    
    意图类型：
    - FIND_DEFINITION: 查找定义
    - UNDERSTAND_STRUCTURE: 理解结构
    - FIND_USAGE: 查找使用
    - DEBUG_ERROR: 调试错误
    - LEARN_API: 学习API
    """
    
    def extract(self, user_query: str, context: Dict) -> Intent:
        """
        提取意图
        
        使用规则+语义的混合方法
        """
        # 规则匹配（快速）
        intent = self._rule_based_match(user_query)
        
        if intent.confidence < 0.7:
            # 语义匹配（准确但慢）
            intent = await self._semantic_match(user_query, context)
        
        return intent
    
    def _rule_based_match(self, query: str) -> Intent:
        """基于规则的快速匹配"""
        query_lower = query.lower()
        
        # 查找定义
        if any(kw in query_lower for kw in ['定义', '是什么', 'what is', 'define']):
            return Intent(type='FIND_DEFINITION', confidence=0.9)
        
        # 理解结构
        if any(kw in query_lower for kw in ['结构', '架构', 'structure', 'architecture']):
            return Intent(type='UNDERSTAND_STRUCTURE', confidence=0.9)
        
        # 查找使用
        if any(kw in query_lower for kw in ['怎么用', '如何使用', 'how to use', 'usage']):
            return Intent(type='FIND_USAGE', confidence=0.9)
        
        # 调试错误
        if any(kw in query_lower for kw in ['错误', '报错', 'error', 'bug', 'fix']):
            return Intent(type='DEBUG_ERROR', confidence=0.9)
        
        return Intent(type='GENERAL', confidence=0.5)
```

### 3. 语义相关性过滤器（SemanticFilter）

```python
class SemanticFilter:
    """
    基于语义相关性过滤内容
    
    使用向量相似度或LLM判断
    """
    
    def __init__(self, embedding_model=None, llm_client=None):
        self.embedding_model = embedding_model
        self.llm_client = llm_client
    
    async def filter_by_relevance(
        self,
        items: List[str],
        query: str,
        threshold: float = 0.5,
        max_items: int = 20
    ) -> List[str]:
        """
        过滤出最相关的项
        
        方法1: 使用Embedding（快速）
        方法2: 使用LLM判断（准确）
        """
        if self.embedding_model:
            return await self._filter_by_embedding(items, query, threshold, max_items)
        elif self.llm_client:
            return await self._filter_by_llm(items, query, max_items)
        else:
            # 回退到关键词匹配
            return self._filter_by_keywords(items, query, max_items)
    
    async def _filter_by_embedding(
        self,
        items: List[str],
        query: str,
        threshold: float,
        max_items: int
    ) -> List[str]:
        """使用Embedding计算相似度"""
        # 1. 获取query的embedding
        query_embedding = await self.embedding_model.encode(query)
        
        # 2. 获取所有items的embedding
        item_embeddings = await self.embedding_model.encode_batch(items)
        
        # 3. 计算相似度
        similarities = cosine_similarity(query_embedding, item_embeddings)
        
        # 4. 排序并过滤
        scored_items = list(zip(items, similarities))
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # 5. 返回最相关的
        relevant = [item for item, score in scored_items if score >= threshold]
        return relevant[:max_items]
    
    async def _filter_by_llm(
        self,
        items: List[str],
        query: str,
        max_items: int
    ) -> List[str]:
        """使用LLM判断相关性"""
        # 批量判断（减少API调用）
        prompt = f"""用户问题: {query}

以下是搜索结果，请选出最相关的{max_items}个（返回序号）：

{chr(10).join([f"{i+1}. {item[:100]}" for i, item in enumerate(items)])}

只返回序号，用逗号分隔，例如: 1,3,5,7
"""
        
        response = await self.llm_client.chat(prompt, model="qwen-turbo")
        
        # 解析序号
        try:
            indices = [int(x.strip()) - 1 for x in response.split(',')]
            return [items[i] for i in indices if 0 <= i < len(items)]
        except:
            return items[:max_items]
    
    def _filter_by_keywords(
        self,
        items: List[str],
        query: str,
        max_items: int
    ) -> List[str]:
        """基于关键词的简单过滤"""
        keywords = set(query.lower().split())
        
        scored = []
        for item in items:
            item_lower = item.lower()
            score = sum(1 for kw in keywords if kw in item_lower)
            scored.append((item, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:max_items]]
```

### 4. 具体工具的后处理器

#### A. RepoMap后处理器

```python
class RepoMapPostProcessor:
    """
    RepoMap结果的智能后处理
    
    策略：
    1. 根据用户问题提取关键词
    2. 只保留相关的文件和定义
    3. 添加上下文说明
    """
    
    async def process(
        self,
        result: ToolResult,
        intent: Intent,
        context: Dict
    ) -> ToolResult:
        """处理RepoMap结果"""
        if not result.success:
            return result
        
        content = result.content
        
        # 1. 解析RepoMap
        files = self._parse_repo_map(content)
        
        # 2. 根据意图过滤
        if intent.type == 'FIND_DEFINITION':
            # 只保留定义，去掉引用
            files = self._filter_definitions_only(files)
        
        elif intent.type == 'UNDERSTAND_STRUCTURE':
            # 保留结构信息，简化细节
            files = self._simplify_for_structure(files)
        
        elif intent.type == 'FIND_USAGE':
            # 保留引用关系
            files = self._keep_references(files)
        
        # 3. 语义过滤（保留最相关的文件）
        if len(files) > 20:
            relevant_files = await self.semantic_filter.filter_by_relevance(
                files,
                context.get('user_query', ''),
                max_items=20
            )
            files = relevant_files
        
        # 4. 重新格式化
        optimized_content = self._format_repo_map(files, intent)
        
        # 5. 添加元数据
        result.content = optimized_content
        result.metadata['post_processed'] = True
        result.metadata['original_files'] = len(self._parse_repo_map(content))
        result.metadata['filtered_files'] = len(files)
        
        return result
```

#### B. SearchResult后处理器

```python
class SearchResultPostProcessor:
    """
    搜索结果的智能后处理
    
    策略：
    1. 去重（相似的结果合并）
    2. 语义排序（最相关的在前）
    3. 添加上下文（显示周围代码）
    4. 高亮关键部分
    """
    
    async def process(
        self,
        result: ToolResult,
        intent: Intent,
        context: Dict
    ) -> ToolResult:
        """处理搜索结果"""
        if not result.success:
            return result
        
        # 1. 解析搜索结果
        matches = self._parse_search_results(result.content)
        
        # 2. 去重（基于相似度）
        unique_matches = self._deduplicate(matches)
        
        # 3. 语义排序
        if len(unique_matches) > 10:
            sorted_matches = await self.semantic_filter.filter_by_relevance(
                unique_matches,
                context.get('user_query', ''),
                max_items=10
            )
        else:
            sorted_matches = unique_matches
        
        # 4. 添加上下文
        enriched_matches = self._add_context(sorted_matches, lines_before=2, lines_after=2)
        
        # 5. 高亮关键词
        highlighted = self._highlight_keywords(enriched_matches, context.get('user_query', ''))
        
        # 6. 格式化输出
        optimized_content = self._format_results(highlighted)
        
        result.content = optimized_content
        result.metadata['post_processed'] = True
        result.metadata['original_matches'] = len(matches)
        result.metadata['filtered_matches'] = len(sorted_matches)
        
        return result
```

#### C. ReadFile后处理器

```python
class ReadFilePostProcessor:
    """
    文件内容的智能后处理
    
    策略：
    1. 提取相关部分（函数、类）
    2. 折叠无关代码
    3. 添加导航信息
    """
    
    async def process(
        self,
        result: ToolResult,
        intent: Intent,
        context: Dict
    ) -> ToolResult:
        """处理文件内容"""
        if not result.success:
            return result
        
        content = result.content
        file_path = result.metadata.get('file_path', '')
        
        # 1. 解析代码结构（使用AST）
        structure = self._parse_code_structure(content, file_path)
        
        # 2. 根据意图提取相关部分
        if intent.type == 'FIND_DEFINITION':
            # 只显示定义，折叠实现
            relevant_parts = self._extract_definitions(structure, context)
        
        elif intent.type == 'UNDERSTAND_STRUCTURE':
            # 显示大纲
            relevant_parts = self._extract_outline(structure)
        
        elif intent.type == 'FIND_USAGE':
            # 显示使用示例
            relevant_parts = self._extract_usage_examples(structure, context)
        
        else:
            # 智能截断（保留最相关的部分）
            relevant_parts = await self._extract_relevant_sections(
                structure,
                context.get('user_query', '')
            )
        
        # 3. 格式化输出
        optimized_content = self._format_code_sections(relevant_parts)
        
        result.content = optimized_content
        result.metadata['post_processed'] = True
        result.metadata['original_lines'] = content.count('\n') + 1
        result.metadata['filtered_lines'] = optimized_content.count('\n') + 1
        
        return result
```

## 实现方案

### 阶段1: 基础后处理（立即实施）⭐⭐⭐⭐⭐

**不需要LLM，使用规则和启发式**

```python
# backend/daoyoucode/agents/tools/postprocessor.py

class BasicToolPostProcessor:
    """基础工具后处理器（不需要LLM）"""
    
    def __init__(self):
        self.processors = {
            'repo_map': BasicRepoMapProcessor(),
            'text_search': BasicSearchProcessor(),
            'read_file': BasicReadFileProcessor(),
            'get_repo_structure': BasicStructureProcessor(),
        }
    
    async def process(
        self,
        tool_name: str,
        result: ToolResult,
        user_query: str,
        context: Dict
    ) -> ToolResult:
        """处理工具结果"""
        processor = self.processors.get(tool_name)
        if not processor:
            return result  # 没有专门的处理器，返回原结果
        
        return await processor.process(result, user_query, context)


class BasicRepoMapProcessor:
    """RepoMap基础处理器"""
    
    async def process(self, result, user_query, context):
        """
        基于关键词的简单过滤
        
        1. 提取用户问题中的关键词
        2. 只保留包含关键词的文件
        3. 限制输出长度
        """
        if not result.success:
            return result
        
        # 提取关键词
        keywords = self._extract_keywords(user_query)
        
        if not keywords:
            return result  # 没有关键词，返回原结果
        
        # 解析RepoMap
        lines = result.content.splitlines()
        filtered_lines = []
        current_file = None
        file_relevant = False
        
        for line in lines:
            if line.startswith('\n') or ':' in line:
                # 文件头
                current_file = line
                file_relevant = any(kw.lower() in line.lower() for kw in keywords)
                if file_relevant:
                    filtered_lines.append(line)
            elif file_relevant:
                # 文件内容
                filtered_lines.append(line)
        
        if filtered_lines:
            result.content = '\n'.join(filtered_lines)
            result.metadata['keyword_filtered'] = True
            result.metadata['keywords'] = keywords
        
        return result
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 移除停用词
        stop_words = {'的', '是', '在', '有', '和', '了', '吗', '呢', '啊',
                      'the', 'is', 'in', 'at', 'of', 'and', 'a', 'an'}
        
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:5]  # 最多5个关键词
```

### 阶段2: 语义后处理（中期）⭐⭐⭐⭐

**使用Embedding模型**

```python
class SemanticToolPostProcessor(BasicToolPostProcessor):
    """语义工具后处理器（使用Embedding）"""
    
    def __init__(self, embedding_model):
        super().__init__()
        self.embedding_model = embedding_model
        
        # 升级处理器
        self.processors = {
            'repo_map': SemanticRepoMapProcessor(embedding_model),
            'text_search': SemanticSearchProcessor(embedding_model),
            'read_file': SemanticReadFileProcessor(embedding_model),
        }
```

### 阶段3: LLM后处理（高级）⭐⭐⭐

**使用弱模型进行智能摘要**

```python
class LLMToolPostProcessor(SemanticToolPostProcessor):
    """LLM工具后处理器（使用弱模型）"""
    
    def __init__(self, embedding_model, llm_client):
        super().__init__(embedding_model)
        self.llm_client = llm_client
        
        # 升级处理器
        self.processors = {
            'repo_map': LLMRepoMapProcessor(embedding_model, llm_client),
            'text_search': LLMSearchProcessor(embedding_model, llm_client),
            'read_file': LLMReadFileProcessor(embedding_model, llm_client),
        }
```

## 集成到Agent

```python
# backend/daoyoucode/agents/core/agent.py

class BaseAgent:
    def __init__(self, config: AgentConfig):
        # ... 现有代码 ...
        
        # 初始化后处理器
        self.tool_postprocessor = BasicToolPostProcessor()
    
    async def _call_llm_with_tools(self, ...):
        # ... 执行工具 ...
        
        tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
        
        # ========== 智能后处理 ==========
        if tool_result.success:
            # 提取用户问题（从messages中）
            user_query = self._extract_user_query(messages)
            
            # 后处理
            tool_result = await self.tool_postprocessor.process(
                tool_name=tool_name,
                result=tool_result,
                user_query=user_query,
                context={
                    'session_id': context.get('session_id'),
                    'conversation_history': history,
                    'mentioned_files': context.get('files', []),
                }
            )
        
        # 转换为字符串
        tool_result_str = str(tool_result.content)
        
        # ... 添加到消息历史 ...
```

## 配置

```yaml
# backend/config/tool_postprocessing.yaml

# 工具后处理配置
tool_postprocessing:
  enabled: true
  
  # 处理器类型
  processor_type: "basic"  # basic | semantic | llm
  
  # 基础处理器配置
  basic:
    keyword_extraction: true
    max_keywords: 5
    relevance_threshold: 0.3
  
  # 语义处理器配置
  semantic:
    embedding_model: "text-embedding-3-small"
    similarity_threshold: 0.5
    max_items: 20
  
  # LLM处理器配置
  llm:
    model: "qwen-turbo"  # 使用便宜的模型
    max_summary_length: 2000
    enable_for_tools:
      - repo_map
      - text_search
  
  # 每个工具的配置
  tools:
    repo_map:
      enable_postprocessing: true
      filter_by_keywords: true
      max_files: 20
    
    text_search:
      enable_postprocessing: true
      deduplicate: true
      add_context_lines: 2
      max_results: 10
    
    read_file:
      enable_postprocessing: true
      extract_relevant_sections: true
      max_lines: 200
```

## 预期效果

**Token节省**：
- 基础后处理：30-50%
- 语义后处理：50-70%
- LLM后处理：70-85%

**准确性提升**：
- 更相关的信息
- 更少的噪音
- 更快的理解

**成本**：
- 基础：0成本（纯规则）
- 语义：Embedding成本（很低）
- LLM：弱模型成本（可接受）

## 总结

这套方案的核心优势：

1. **渐进式实施** - 从简单到复杂，逐步优化
2. **可配置** - 每个工具可以独立配置
3. **智能化** - 基于用户意图，而不是盲目截断
4. **成本可控** - 优先使用规则和Embedding，LLM作为可选项
5. **效果显著** - 大幅减少token消耗，提升相关性

你觉得这个方案怎么样？我们可以先实现阶段1（基础后处理），它不需要额外的依赖，纯规则就能带来30-50%的token节省。
