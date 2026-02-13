# Tool Result Truncation Solution

## 问题描述

Function Calling中，工具返回的内容可能非常长（例如repo_map返回几千行代码），如果直接传递给LLM会导致：
1. **Token消耗巨大** - 每次迭代都重复传递超长内容
2. **超出上下文窗口** - 可能超过模型的max_tokens限制
3. **成本高昂** - 大量无用的token消耗

## 业界解决方案

### 1. OpenAI的官方限制
根据OpenAI社区讨论，Function Calling的结果有隐式限制：
- **32768字符限制** - 单个function result message会被截断到32768字符
- 这是未公开的限制，但实际存在

### 2. Aider的处理方式
Aider没有特殊的截断逻辑，主要依赖：
- **工具自身限制输出** - 例如repo_map有max_tokens参数
- **行数限制** - 某些工具截断到100行（前50+后50）
- **依赖模型的上下文窗口** - 让模型自己处理

### 3. 其他AI编码工具的方案

#### Codex (GitHub Copilot)
- 硬限制：256行或10KB
- 截断策略：前128行 + 后128行
- 中间部分用"..."标记

#### Claude Code (Anthropic)
- 智能摘要：使用LLM总结长内容
- 分层展示：只传递关键部分
- 按需加载：LLM可以请求更多细节

## 推荐方案

### 方案A：智能截断（推荐）⭐⭐⭐⭐⭐

**优点**：
- 简单高效
- 不需要额外LLM调用
- 保留最重要的信息

**实现**：
```python
def truncate_tool_result(content: str, max_chars: int = 8000) -> str:
    """
    智能截断工具结果
    
    策略：
    1. 如果内容<=max_chars，直接返回
    2. 否则：前40% + 中间摘要 + 后40%
    """
    if len(content) <= max_chars:
        return content
    
    # 计算保留的字符数
    keep_chars = max_chars - 200  # 留200字符给摘要信息
    head_chars = int(keep_chars * 0.4)
    tail_chars = int(keep_chars * 0.4)
    
    head = content[:head_chars]
    tail = content[-tail_chars:]
    
    # 统计被截断的部分
    truncated_chars = len(content) - head_chars - tail_chars
    truncated_lines = content[head_chars:-tail_chars].count('\n')
    
    summary = f"\n\n... [截断了 {truncated_chars} 字符 / {truncated_lines} 行] ...\n\n"
    
    return head + summary + tail
```

### 方案B：分层摘要（高级）⭐⭐⭐⭐

**优点**：
- 保留语义信息
- 更智能的压缩

**缺点**：
- 需要额外LLM调用
- 增加延迟和成本

**实现**：
```python
async def summarize_tool_result(
    content: str,
    max_chars: int = 8000,
    llm_client = None
) -> str:
    """
    使用LLM摘要工具结果
    
    适用场景：
    - 内容非常长（>20000字符）
    - 需要保留语义信息
    - 可以接受额外的LLM调用成本
    """
    if len(content) <= max_chars:
        return content
    
    # 使用弱模型（便宜）进行摘要
    prompt = f"""请将以下内容摘要到{max_chars}字符以内，保留关键信息：

{content[:50000]}  # 只传递前50000字符给摘要模型

要求：
1. 保留所有重要的定义和结构
2. 删除重复和冗余信息
3. 保持代码片段的可读性
"""
    
    summary = await llm_client.chat(prompt, model="qwen-turbo")
    return summary
```

### 方案C：工具级别控制（最佳实践）⭐⭐⭐⭐⭐

**优点**：
- 在源头控制输出
- 每个工具可以自定义策略
- 最高效

**实现**：
```python
class BaseTool:
    """工具基类"""
    
    # 默认输出限制
    MAX_OUTPUT_CHARS = 8000
    MAX_OUTPUT_LINES = 500
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具（子类实现）"""
        raise NotImplementedError
    
    def truncate_output(self, content: str) -> str:
        """截断输出（可被子类覆盖）"""
        # 字符限制
        if len(content) > self.MAX_OUTPUT_CHARS:
            content = self._truncate_by_chars(content, self.MAX_OUTPUT_CHARS)
        
        # 行数限制
        lines = content.splitlines()
        if len(lines) > self.MAX_OUTPUT_LINES:
            content = self._truncate_by_lines(lines, self.MAX_OUTPUT_LINES)
        
        return content
    
    def _truncate_by_chars(self, content: str, max_chars: int) -> str:
        """按字符截断"""
        if len(content) <= max_chars:
            return content
        
        keep = max_chars - 100
        head = int(keep * 0.4)
        tail = int(keep * 0.4)
        
        return (
            content[:head] +
            f"\n\n... [截断 {len(content) - keep} 字符] ...\n\n" +
            content[-tail:]
        )
    
    def _truncate_by_lines(self, lines: List[str], max_lines: int) -> str:
        """按行数截断"""
        if len(lines) <= max_lines:
            return '\n'.join(lines)
        
        keep = max_lines - 2  # 留2行给摘要
        head = keep // 2
        tail = keep - head
        
        result = lines[:head]
        result.append(f"... [截断 {len(lines) - keep} 行] ...")
        result.extend(lines[-tail:])
        
        return '\n'.join(result)


# 具体工具实现
class RepoMapTool(BaseTool):
    """RepoMap工具 - 已经有max_tokens参数"""
    
    # 覆盖默认限制
    MAX_OUTPUT_CHARS = 10000  # RepoMap可以稍微长一点
    
    async def execute(self, repo_path: str, max_tokens: int = 2000, **kwargs):
        # max_tokens已经在工具内部控制输出长度
        # 这是最好的方式
        ...


class ReadFileTool(BaseTool):
    """读取文件工具"""
    
    MAX_OUTPUT_CHARS = 5000  # 单个文件不要太长
    
    async def execute(self, file_path: str, **kwargs):
        content = read_file(file_path)
        
        # 自动截断
        content = self.truncate_output(content)
        
        return ToolResult(success=True, content=content)


class GrepSearchTool(BaseTool):
    """搜索工具"""
    
    MAX_OUTPUT_LINES = 100  # 搜索结果限制行数
    
    async def execute(self, pattern: str, **kwargs):
        results = grep_search(pattern)
        
        # 限制结果数量
        if len(results) > self.MAX_OUTPUT_LINES:
            truncated = results[:self.MAX_OUTPUT_LINES]
            summary = f"\n... [显示前{self.MAX_OUTPUT_LINES}个结果，共{len(results)}个] ...\n"
            return ToolResult(
                success=True,
                content=format_results(truncated) + summary
            )
        
        return ToolResult(success=True, content=format_results(results))
```

## 实施建议

### 第一阶段：工具级别控制（立即实施）

1. **修改BaseTool基类**
   - 添加MAX_OUTPUT_CHARS和MAX_OUTPUT_LINES常量
   - 添加truncate_output方法
   - 在execute后自动调用截断

2. **更新现有工具**
   - repo_map: 已有max_tokens，保持不变
   - read_file: 添加5000字符限制
   - grep_search: 添加100行限制
   - get_repo_structure: 添加深度和行数限制

### 第二阶段：Agent级别控制（可选）

在Agent的`_call_llm_with_tools`中添加全局截断：

```python
async def _call_llm_with_tools(self, ...):
    # ... 执行工具 ...
    
    tool_result_str = str(tool_result.content)
    
    # 全局截断（双保险）
    MAX_FUNCTION_RESULT_CHARS = 8000
    if len(tool_result_str) > MAX_FUNCTION_RESULT_CHARS:
        tool_result_str = truncate_tool_result(
            tool_result_str,
            MAX_FUNCTION_RESULT_CHARS
        )
        self.logger.warning(
            f"工具结果被截断: {len(str(tool_result.content))} -> {len(tool_result_str)} 字符"
        )
    
    # 添加到消息历史
    messages.append({
        "role": "function",
        "name": tool_name,
        "content": tool_result_str
    })
```

### 第三阶段：智能摘要（高级功能）

对于特定工具（如repo_map），可以实现智能摘要：

```python
class RepoMapTool(BaseTool):
    async def execute(self, repo_path: str, max_tokens: int = 2000, **kwargs):
        # 生成完整地图
        full_map = self._generate_map(...)
        
        # 如果太长，使用LLM摘要
        if len(full_map) > 10000:
            summary = await self._summarize_map(full_map)
            return ToolResult(
                success=True,
                content=summary,
                metadata={'original_length': len(full_map), 'summarized': True}
            )
        
        return ToolResult(success=True, content=full_map)
```

## 配置建议

在`backend/config/tool_config.yaml`中添加全局配置：

```yaml
# 工具输出限制配置
tool_output_limits:
  # 全局默认限制
  default:
    max_chars: 8000
    max_lines: 500
    truncation_strategy: "head_tail"  # head_tail | head_only | summarize
  
  # 特定工具的限制
  tools:
    repo_map:
      max_chars: 10000
      max_lines: 1000
    
    read_file:
      max_chars: 5000
      max_lines: 200
    
    grep_search:
      max_lines: 100
      show_context: 2  # 每个匹配显示前后2行
    
    get_repo_structure:
      max_depth: 3
      max_files: 500

# 智能摘要配置（可选）
summarization:
  enabled: false  # 默认关闭，因为有额外成本
  model: "qwen-turbo"  # 使用便宜的模型
  max_input_chars: 50000  # 传递给摘要模型的最大字符数
  trigger_threshold: 20000  # 超过这个长度才触发摘要
```

## 监控和调试

添加日志记录截断情况：

```python
class BaseTool:
    def truncate_output(self, content: str) -> str:
        original_length = len(content)
        truncated = self._do_truncate(content)
        
        if len(truncated) < original_length:
            self.logger.info(
                f"工具 {self.name} 输出被截断: "
                f"{original_length} -> {len(truncated)} 字符 "
                f"({(1 - len(truncated)/original_length)*100:.1f}% 减少)"
            )
        
        return truncated
```

## 总结

**推荐实施顺序**：

1. ✅ **立即实施**：方案C（工具级别控制）
   - 修改BaseTool基类
   - 更新现有工具
   - 添加配置文件

2. ⏳ **短期实施**：Agent级别全局截断（双保险）
   - 在_call_llm_with_tools中添加截断
   - 添加日志记录

3. 🔮 **长期考虑**：智能摘要（可选）
   - 只对特定工具启用
   - 使用便宜的模型
   - 可配置开关

**预期效果**：
- Token消耗减少50-80%
- 不影响功能正确性
- 提升响应速度
- 降低成本

**注意事项**：
- 截断可能丢失部分信息，但通常不影响LLM理解
- 如果LLM需要更多信息，可以再次调用工具
- 监控截断率，如果过高可能需要调整策略
