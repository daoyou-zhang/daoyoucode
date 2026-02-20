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
class ToolContext:
    """
    工具上下文
    
    包含工具执行所需的所有环境信息，确保路径处理的一致性。
    参考 daoyouCodePilot 和 aider 的设计。
    
    Attributes:
        repo_path: 仓库根路径（绝对路径）
        session_id: 会话ID
        user_id: 用户ID（可选）
        subtree_only: 是否只扫描当前目录及其子目录（参考 aider）
        cwd: 当前工作目录（用于 subtree_only 过滤）
    """
    repo_path: Path
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    subtree_only: bool = False
    cwd: Optional[Path] = None
    
    def __post_init__(self):
        """确保 repo_path 是绝对路径"""
        if not self.repo_path.is_absolute():
            self.repo_path = self.repo_path.resolve()
        
        # 如果启用 subtree_only 但没有设置 cwd，使用当前目录
        if self.subtree_only and self.cwd is None:
            self.cwd = Path.cwd()
        
        # 确保 cwd 是绝对路径
        if self.cwd and not self.cwd.is_absolute():
            self.cwd = self.cwd.resolve()
    
    def should_include_path(self, path: str) -> bool:
        """
        判断路径是否应该被包含（用于 subtree_only 过滤）
        
        参考 aider 的实现：
        - 如果 subtree_only=False，包含所有路径
        - 如果 subtree_only=True，只包含 cwd 及其子目录下的路径
        
        Args:
            path: 要检查的路径（相对或绝对）
        
        Returns:
            是否应该包含该路径
        """
        if not self.subtree_only:
            return True
        
        if not self.cwd:
            return True
        
        # 转换为绝对路径
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.repo_path / path
        
        try:
            # 检查路径是否在 cwd 下
            path_obj.relative_to(self.cwd)
            return True
        except ValueError:
            # 不在 cwd 下
            return False
    
    def abs_path(self, path: str) -> Path:
        """
        将相对路径转换为绝对路径
        
        Args:
            path: 相对路径或绝对路径
        
        Returns:
            绝对路径
        
        Examples:
            >>> ctx = ToolContext(repo_path=Path("/project"))
            >>> ctx.abs_path("backend/file.py")
            Path("/project/backend/file.py")
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.repo_path / path
    
    def rel_path(self, path: str) -> str:
        """
        将绝对路径转换为相对于 repo_path 的路径
        
        Args:
            path: 绝对路径或相对路径
        
        Returns:
            相对于 repo_path 的路径
        
        Examples:
            >>> ctx = ToolContext(repo_path=Path("/project"))
            >>> ctx.rel_path("/project/backend/file.py")
            "backend/file.py"
            >>> ctx.rel_path("backend/file.py")
            "backend/file.py"
        """
        path_obj = Path(path)
        
        # 如果已经是相对路径，直接返回
        if not path_obj.is_absolute():
            return str(path_obj)
        
        # 转换为相对路径
        try:
            return str(path_obj.relative_to(self.repo_path))
        except ValueError:
            # 不在 repo_path 下，返回原路径
            logger.warning(f"Path {path} is not under repo_path {self.repo_path}")
            return str(path_obj)
    
    def normalize_path(self, path: str) -> str:
        """
        标准化路径：确保返回相对于 repo_path 的路径
        
        这是工具返回路径时应该使用的方法。
        
        Args:
            path: 任意路径
        
        Returns:
            相对于 repo_path 的标准路径
        """
        return self.rel_path(path)


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
        self._working_directory = None  # 工作目录（向后兼容）
        self._context: Optional[ToolContext] = None  # 新的上下文对象
    
    def set_context(self, context: ToolContext):
        """设置工具上下文（新方法）"""
        self._context = context
        # 同时设置 working_directory 以保持向后兼容
        self._working_directory = str(context.repo_path)
        self.logger.debug(f"工具 {self.name} 上下文设置为: repo_path={context.repo_path}")
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录（向后兼容）"""
        self._working_directory = working_dir
        # 如果没有 context，创建一个
        if not self._context:
            self._context = ToolContext(repo_path=Path(working_dir))
        self.logger.debug(f"工具 {self.name} 工作目录设置为: {working_dir}")
    
    @property
    def context(self) -> ToolContext:
        """获取工具上下文"""
        if not self._context:
            # 如果没有设置，使用当前目录
            self._context = ToolContext(repo_path=Path.cwd())
        return self._context
    
    def resolve_path(self, path: str) -> Path:
        """
        解析路径（使用 ToolContext）
        
        自动检测并修正常见的占位符路径错误。
        
        Args:
            path: 相对或绝对路径
        
        Returns:
            绝对路径
        """
        # 🆕 检测其他项目名称（防止 AI 混淆项目）
        other_projects = [
            'daoyouCodePilot',
            'daoyoucodepilot',
            'oh-my-opencode',
            'opencode',
            'aider',
            'cursor'
        ]
        
        path_parts = Path(path).parts
        if path_parts:
            first_part = path_parts[0]
            first_part_lower = first_part.lower()
            
            for project in other_projects:
                if project.lower() == first_part_lower:
                    self.logger.error(
                        f"❌ 路径错误: {path}\n"
                        f"   '{first_part}' 不是当前项目的目录\n"
                        f"   当前项目: {self.context.repo_path.name}\n"
                        f"   提示：使用相对于项目根的路径，如 'backend/file.py'"
                    )
                    raise ValueError(
                        f"路径错误：'{path}' 包含其他项目名称 '{first_part}'。\n"
                        f"当前项目是 '{self.context.repo_path.name}'，"
                        f"请使用相对路径，如 'backend/daoyoucode/agents/core/agent.py'"
                    )
        
        # 🆕 检测占位符路径
        placeholder_patterns = [
            'your-repo-path',
            'your-project',
            'your-repo',
            'path/to/your',
            'path/to/file',
            'example/path',
            'example-path'
        ]
        
        path_lower = path.lower()
        for pattern in placeholder_patterns:
            if pattern in path_lower:
                self.logger.warning(
                    f"⚠️  检测到占位符路径: {path}\n"
                    f"   自动修正为: .\n"
                    f"   提示：请使用 '.' 表示当前工作目录"
                )
                # 自动修正为当前工作目录
                return self.context.repo_path
        
        # 🆕 去掉 ./ 前缀（如果路径不存在）
        if path.startswith('./'):
            clean_path = path[2:]
            full_path = self.context.repo_path / clean_path
            
            # 如果去掉 ./ 后的路径存在，使用它
            if not full_path.exists():
                self.logger.warning(
                    f"⚠️  路径不存在: {path}\n"
                    f"   尝试去掉 ./ 前缀: {clean_path}"
                )
                path = clean_path
        
        return self.context.abs_path(path)
    
    def normalize_path(self, path: str) -> str:
        """
        标准化路径（使用 ToolContext）
        
        Args:
            path: 任意路径
        
        Returns:
            相对于 repo_path 的标准路径
        """
        return self.context.normalize_path(path)
    
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
        self._working_directory = None  # 向后兼容
        self._context: Optional[ToolContext] = None  # 新的上下文对象
    
    def set_context(self, context: ToolContext):
        """设置工具上下文（新方法）"""
        self._context = context
        self._working_directory = str(context.repo_path)  # 向后兼容
        logger.info(f"工具注册表上下文设置为: repo_path={context.repo_path}")
        # 传递给所有已注册的工具
        for tool in self._tools.values():
            tool.set_context(context)
    
    def set_working_directory(self, working_dir: str):
        """设置工作目录（向后兼容）"""
        self._working_directory = working_dir
        # 创建或更新 context
        if not self._context:
            self._context = ToolContext(repo_path=Path(working_dir))
        logger.info(f"工具注册表工作目录设置为: {working_dir}")
        # 传递给所有已注册的工具
        for tool in self._tools.values():
            tool.set_working_directory(working_dir)
    
    @property
    def context(self) -> ToolContext:
        """获取工具上下文"""
        if not self._context:
            # 如果没有设置，使用当前目录
            self._context = ToolContext(repo_path=Path.cwd())
        return self._context
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        # 如果已经设置了上下文，传递给新工具
        if self._context:
            tool.set_context(self._context)
        elif self._working_directory:
            tool.set_working_directory(self._working_directory)
        logger.info(f"已注册工具: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def filter_tool_names(self, tool_names: Optional[List[str]]) -> Optional[List[str]]:
        """
        只保留已注册的工具名，避免 Skill 配置了不存在的工具导致运行时报错。
        若过滤后为空，返回 None（表示不限制工具）。
        """
        if not tool_names:
            return None
        available = set(self._tools.keys())
        filtered = [n for n in tool_names if n in available]
        missing = set(tool_names) - available
        if missing:
            logger.warning(
                "Skill 引用了不存在的工具，已忽略: %s（可用: %s）",
                sorted(missing),
                ", ".join(sorted(available)[:20]) + ("..." if len(available) > 20 else ""),
            )
        return filtered if filtered else None

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
