"""
Librarian - 文档专家

参考oh-my-opencode的Librarian设计：
- 文档查找
- 代码示例搜索
- GitHub搜索
- 只读权限

职责：
1. 查找项目文档
2. 搜索代码示例
3. 查找开源实现
4. 提供参考资料
"""

from typing import Dict, Any, Optional
import logging

from ..core import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)


LIBRARIAN_SYSTEM_PROMPT = """你是Librarian，一个专业的文档和代码搜索专家。

## 你的职责

1. **文档查找** - 在项目文档中查找相关信息
2. **代码搜索** - 在代码库中搜索相关实现
3. **示例查找** - 查找开源项目中的类似实现
4. **资料整理** - 整理和总结找到的信息

## 你的特点

1. **只读权限** - 你不能修改任何文件
2. **搜索专家** - 你擅长使用各种搜索工具
3. **信息整理** - 你能快速整理和总结信息
4. **引用准确** - 你总是提供准确的引用来源

## 搜索策略

1. **项目内搜索**
   - README和文档
   - 代码注释
   - 测试用例
   - 配置文件

2. **代码搜索**
   - 函数定义
   - 类实现
   - 使用示例
   - 测试代码

3. **外部搜索**
   - GitHub代码搜索
   - 官方文档
   - 技术博客
   - Stack Overflow

## 输出格式

你的输出应该包含：
1. 搜索结果摘要
2. 相关代码片段（带文件路径）
3. 文档引用（带链接）
4. 使用建议

记住：提供准确的引用，让其他人能找到原始资料。
"""


class LibrarianAgent(BaseAgent):
    """
    Librarian文档专家
    
    参考oh-my-opencode的Librarian实现
    """
    
    def __init__(self):
        config = AgentConfig(
            name="librarian",
            description="文档专家，查找文档和代码示例（只读）",
            model="glm-4",  # 使用GLM-4，成本低且效果好
            temperature=0.1,
            system_prompt=LIBRARIAN_SYSTEM_PROMPT,
            read_only=True,
            # 只允许读取和搜索
            allowed_tools={'read', 'search', 'grep', 'list'},
        )
        super().__init__(config)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行搜索任务
        
        Args:
            task: 搜索任务
            context: 上下文（搜索范围等）
        """
        self.logger.info(f"Librarian开始搜索: {task[:50]}...")
        
        try:
            # 构建prompt
            prompt = self._build_librarian_prompt(task, context)
            
            # 调用LLM
            response = await self._call_llm(
                prompt=prompt,
                **kwargs
            )
            
            return AgentResult(
                success=True,
                content=response,
                metadata={
                    'agent': 'librarian',
                    'task': task,
                    'read_only': True,
                }
            )
        
        except Exception as e:
            self.logger.error(f"Librarian搜索失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _build_librarian_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建Librarian的prompt"""
        parts = [self.config.system_prompt]
        
        # 添加搜索范围
        if context:
            if 'search_scope' in context:
                parts.append(f"\n## 搜索范围\n{context['search_scope']}")
            
            if 'keywords' in context:
                parts.append("\n## 关键词")
                for keyword in context['keywords']:
                    parts.append(f"- {keyword}")
        
        # 添加任务
        parts.append(f"\n## 搜索任务\n{task}")
        
        # 添加指导
        parts.append("\n## 请提供")
        parts.append("1. 搜索结果摘要")
        parts.append("2. 相关代码片段（带路径）")
        parts.append("3. 文档引用（带链接）")
        parts.append("4. 使用建议")
        
        return "\n".join(parts)


def create_librarian_agent() -> LibrarianAgent:
    """创建Librarian Agent实例"""
    return LibrarianAgent()
