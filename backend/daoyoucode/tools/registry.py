"""
工具注册系统

提供工具的注册、管理和调用
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
import inspect

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None


@dataclass
class Tool:
    """工具基类"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: str = "general"
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """
        转换为OpenAI Function Calling格式
        
        Returns:
            {
                "name": "tool_name",
                "description": "tool description",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            
            if param.enum:
                prop["enum"] = param.enum
            
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def validate_parameters(self, kwargs: Dict[str, Any]) -> bool:
        """验证参数"""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        return True


class FunctionTool(Tool):
    """基于函数的工具"""
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ):
        """
        从函数创建工具
        
        Args:
            func: 函数（可以是同步或异步）
            name: 工具名称（默认使用函数名）
            description: 工具描述（默认使用函数docstring）
            category: 工具分类
        """
        self.func = func
        self.is_async = inspect.iscoroutinefunction(func)
        
        # 自动提取名称和描述
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip()
        
        # 自动提取参数
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            # 跳过self和cls
            if param_name in ('self', 'cls'):
                continue
            
            # 推断类型
            param_type = "string"  # 默认
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
            
            # 判断是否必需
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=required,
                default=default
            ))
        
        super().__init__(
            name=tool_name,
            description=tool_description,
            parameters=parameters,
            category=category
        )
    
    async def execute(self, **kwargs) -> Any:
        """执行函数"""
        self.validate_parameters(kwargs)
        
        if self.is_async:
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name] = tool
        
        # 按分类组织
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)
        
        logger.info(f"已注册工具: {tool.name} (分类: {tool.category})")
    
    def register_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ):
        """注册函数为工具"""
        tool = FunctionTool(func, name, description, category)
        self.register(tool)
        return tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """列出工具"""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """获取指定分类的所有工具"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def get_all_tools(self) -> List[Tool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_function_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取工具的Function Calling格式
        
        Args:
            tool_names: 工具名称列表（None表示所有工具）
        
        Returns:
            Function schemas列表
        """
        if tool_names is None:
            tools = self.get_all_tools()
        else:
            tools = [self._tools[name] for name in tool_names if name in self._tools]
        
        return [tool.to_function_schema() for tool in tools]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        logger.info(f"执行工具: {tool_name}, 参数: {kwargs}")
        
        try:
            result = await tool.execute(**kwargs)
            logger.info(f"工具执行成功: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
            raise


# 全局注册表
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表"""
    return _tool_registry


def register_tool(tool: Tool):
    """注册工具"""
    _tool_registry.register(tool)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general"
):
    """
    工具装饰器
    
    使用方式:
    @tool(category="file")
    async def read_file(path: str) -> str:
        '''读取文件内容'''
        ...
    """
    def decorator(func: Callable):
        _tool_registry.register_function(func, name, description, category)
        return func
    
    return decorator
