"""
工具基类

所有工具的基础抽象
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """工具基类"""
    
    # 默认输出限制（子类可以覆盖）
    MAX_OUTPUT_CHARS = 8000  # 最大字符数
    MAX_OUTPUT_LINES = 500   # 最大行数
    TRUNCATION_STRATEGY = "head_tail"  # head_tail | head_only | none
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"tool.{name}")
        self._working_directory = None  # 工作目录
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录"""
        self._working_directory = working_dir
        self.logger.debug(f"工具 {self.name} 工作目录设置为: {working_dir}")
    
    def resolve_path(self, path: str) -> Path:
        """
        解析路径
        
        Args:
            path: 相对或绝对路径
        
        Returns:
            解析后的绝对路径
        """
        path_obj = Path(path)
        
        # 如果是绝对路径，直接返回
        if path_obj.is_absolute():
            return path_obj
        
        # 如果有工作目录，相对于工作目录
        if self._working_directory:
            resolved = Path(self._working_directory) / path_obj
            self.logger.debug(f"路径解析: {path} -> {resolved}")
            return resolved
        
        # 否则相对于当前目录
        resolved = path_obj.resolve()
        self.logger.debug(f"路径解析（使用当前目录）: {path} -> {resolved}")
        return resolved
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def get_function_schema(self) -> Dict[str, Any]:
        """
        获取Function Calling的schema
        
        子类应该重写此方法以提供详细的参数schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    def truncate_output(self, content: str) -> str:
        """
        智能截断输出内容
        
        Args:
            content: 原始内容
        
        Returns:
            截断后的内容
        """
        if self.TRUNCATION_STRATEGY == "none":
            return content
        
        original_length = len(content)
        
        # 字符限制
        if len(content) > self.MAX_OUTPUT_CHARS:
            content = self._truncate_by_chars(content, self.MAX_OUTPUT_CHARS)
        
        # 行数限制
        lines = content.splitlines()
        if len(lines) > self.MAX_OUTPUT_LINES:
            content = self._truncate_by_lines(lines, self.MAX_OUTPUT_LINES)
        
        # 记录截断情况
        if len(content) < original_length:
            reduction_pct = (1 - len(content) / original_length) * 100
            self.logger.info(
                f"工具 {self.name} 输出被截断: "
                f"{original_length} -> {len(content)} 字符 "
                f"({reduction_pct:.1f}% 减少)"
            )
        
        return content
    
    def _truncate_by_chars(self, content: str, max_chars: int) -> str:
        """
        按字符数截断
        
        策略：保留前40% + 后40%，中间用摘要替代
        """
        if len(content) <= max_chars:
            return content
        
        if self.TRUNCATION_STRATEGY == "head_only":
            # 只保留开头
            return content[:max_chars] + "\n\n... [内容被截断] ..."
        
        # head_tail策略
        keep_chars = max_chars - 200  # 留200字符给摘要信息
        head_chars = int(keep_chars * 0.4)
        tail_chars = int(keep_chars * 0.4)
        
        head = content[:head_chars]
        tail = content[-tail_chars:]
        
        # 统计被截断的部分
        truncated_chars = len(content) - head_chars - tail_chars
        truncated_lines = content[head_chars:-tail_chars].count('\n')
        
        summary = (
            f"\n\n... [截断了 {truncated_chars:,} 字符 / "
            f"{truncated_lines:,} 行] ...\n\n"
        )
        
        return head + summary + tail
    
    def _truncate_by_lines(self, lines: List[str], max_lines: int) -> str:
        """
        按行数截断
        
        策略：保留前50% + 后50%
        """
        if len(lines) <= max_lines:
            return '\n'.join(lines)
        
        if self.TRUNCATION_STRATEGY == "head_only":
            # 只保留开头
            result = lines[:max_lines]
            result.append(f"\n... [截断了 {len(lines) - max_lines:,} 行] ...")
            return '\n'.join(result)
        
        # head_tail策略
        keep_lines = max_lines - 2  # 留2行给摘要
        head_lines = keep_lines // 2
        tail_lines = keep_lines - head_lines
        
        result = lines[:head_lines]
        result.append(f"\n... [截断了 {len(lines) - keep_lines:,} 行] ...\n")
        result.extend(lines[-tail_lines:])
        
        return '\n'.join(result)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._working_directory = None
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录"""
        self._working_directory = working_dir
        logger.info(f"工具注册表工作目录设置为: {working_dir}")
        # 传递给所有已注册的工具
        for tool in self._tools.values():
            tool.set_working_directory(working_dir)
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        # 如果已经设置了工作目录，传递给新工具
        if self._working_directory:
            tool.set_working_directory(self._working_directory)
        logger.info(f"已注册工具: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
    
    def get_function_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取工具的Function Calling schemas
        
        Args:
            tool_names: 工具名称列表，如果为None则返回所有工具
        
        Returns:
            Function schemas列表
        """
        if tool_names is None:
            tool_names = self.list_tools()
        
        schemas = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                schemas.append(tool.get_function_schema())
        
        return schemas
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool not found: {name}"
            )
        
        try:
            result = await tool.execute(**kwargs)
            
            # 自动截断输出（如果内容是字符串）
            if result.success and isinstance(result.content, str):
                original_content = result.content
                truncated_content = tool.truncate_output(original_content)
                
                # 如果发生了截断，更新结果
                if len(truncated_content) < len(original_content):
                    result.content = truncated_content
                    result.metadata['truncated'] = True
                    result.metadata['original_length'] = len(original_content)
                    result.metadata['truncated_length'] = len(truncated_content)
            
            return result
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
