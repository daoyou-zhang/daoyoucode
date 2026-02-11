"""
Explore - 代码探索专家

参考oh-my-opencode的Explore设计：
- 快速代码定位
- 上下文grep
- 文件结构分析
- 只读权限

职责：
1. 快速定位相关代码
2. 分析文件结构
3. 查找函数和类定义
4. 提供代码概览
"""

from typing import Dict, Any, Optional
import logging

from ..core import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)


EXPLORE_SYSTEM_PROMPT = """你是Explore，一个快速代码探索专家。

## 你的职责

1. **快速定位** - 快速找到相关的代码文件
2. **结构分析** - 分析项目和文件结构
3. **代码概览** - 提供代码的高层次概览
4. **依赖分析** - 分析模块间的依赖关系

## 你的特点

1. **速度优先** - 快速响应，不做深入分析
2. **只读权限** - 你不能修改任何文件
3. **上下文感知** - 理解代码的上下文关系
4. **精准定位** - 准确找到相关代码

## 探索策略

1. **文件级别**
   - 项目结构
   - 文件组织
   - 命名规范
   - 模块划分

2. **代码级别**
   - 函数定义
   - 类定义
   - 导入关系
   - 调用关系

3. **搜索技巧**
   - 关键词搜索
   - 正则表达式
   - 文件名匹配
   - 内容grep

## 输出格式

你的输出应该包含：
1. 相关文件列表（按相关性排序）
2. 关键代码位置（文件:行号）
3. 代码结构概览
4. 建议的下一步操作

记住：快速定位，不要过度分析。
"""


class ExploreAgent(BaseAgent):
    """
    Explore代码探索专家
    
    参考oh-my-opencode的Explore实现
    """
    
    def __init__(self):
        config = AgentConfig(
            name="explore",
            description="代码探索专家，快速定位相关代码（只读）",
            model="qwen-turbo",  # 使用快速模型
            temperature=0.1,
            system_prompt=EXPLORE_SYSTEM_PROMPT,
            read_only=True,
            # 只允许读取、搜索和列表
            allowed_tools={'read', 'search', 'grep', 'list', 'tree'},
        )
        super().__init__(config)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行探索任务
        
        Args:
            task: 探索任务
            context: 上下文（项目路径等）
        """
        self.logger.info(f"Explore开始探索: {task[:50]}...")
        
        try:
            # 构建prompt
            prompt = self._build_explore_prompt(task, context)
            
            # 调用LLM
            response = await self._call_llm(
                prompt=prompt,
                **kwargs
            )
            
            return AgentResult(
                success=True,
                content=response,
                metadata={
                    'agent': 'explore',
                    'task': task,
                    'read_only': True,
                }
            )
        
        except Exception as e:
            self.logger.error(f"Explore探索失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _build_explore_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建Explore的prompt"""
        parts = [self.config.system_prompt]
        
        # 添加项目信息
        if context:
            if 'project_path' in context:
                parts.append(f"\n## 项目路径\n{context['project_path']}")
            
            if 'file_tree' in context:
                parts.append(f"\n## 文件结构\n```\n{context['file_tree']}\n```")
            
            if 'focus_area' in context:
                parts.append(f"\n## 关注区域\n{context['focus_area']}")
        
        # 添加任务
        parts.append(f"\n## 探索任务\n{task}")
        
        # 添加指导
        parts.append("\n## 请提供")
        parts.append("1. 相关文件列表（按相关性排序）")
        parts.append("2. 关键代码位置（文件:行号）")
        parts.append("3. 代码结构概览")
        parts.append("4. 建议的下一步")
        
        return "\n".join(parts)


def create_explore_agent() -> ExploreAgent:
    """创建Explore Agent实例"""
    return ExploreAgent()
