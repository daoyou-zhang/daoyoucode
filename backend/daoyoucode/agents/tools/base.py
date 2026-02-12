"""
工具基类

所有工具的基础抽象
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
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
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"tool.{name}")
    
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


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
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
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
