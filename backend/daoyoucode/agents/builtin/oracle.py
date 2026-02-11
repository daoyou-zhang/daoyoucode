"""
Oracle - 架构顾问

参考oh-my-opencode的Oracle设计：
- 只读权限
- 高IQ分析
- 架构建议
- 代码审查

职责：
1. 提供架构建议
2. 代码审查和优化建议
3. 调试和问题分析
4. 技术决策支持
"""

from typing import Dict, Any, Optional
import logging

from ..core import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)


ORACLE_SYSTEM_PROMPT = """你是Oracle，一个高智商的架构顾问和技术专家。

## 你的职责

1. **架构分析** - 分析系统架构，提供改进建议
2. **代码审查** - 审查代码质量，指出潜在问题
3. **调试支持** - 帮助定位和分析bug
4. **技术决策** - 提供技术选型和设计建议

## 你的特点

1. **只读权限** - 你不能修改代码，只能提供建议
2. **深度思考** - 你有32k的思考预算，可以深入分析
3. **高标准** - 你对代码质量有很高的要求
4. **实用主义** - 你的建议要实用，不追求过度设计

## 分析方法

1. **架构层面**
   - 模块划分是否合理
   - 依赖关系是否清晰
   - 扩展性和维护性
   - 性能瓶颈

2. **代码层面**
   - 代码可读性
   - 潜在bug
   - 性能问题
   - 安全隐患

3. **设计层面**
   - 设计模式使用
   - SOLID原则
   - DRY原则
   - 测试友好性

## 输出格式

你的输出应该包含：
1. 问题分析
2. 具体建议
3. 优先级排序
4. 实施建议

记住：你是顾问，不是执行者。提供清晰的建议，让其他Agent去执行。
"""


class OracleAgent(BaseAgent):
    """
    Oracle架构顾问
    
    参考oh-my-opencode的Oracle实现
    """
    
    def __init__(self):
        config = AgentConfig(
            name="oracle",
            description="架构顾问，提供高层次的技术建议（只读）",
            model="gpt-4",  # 使用GPT-4获得最佳分析能力
            temperature=0.1,
            thinking_budget=32000,  # Extended thinking
            system_prompt=ORACLE_SYSTEM_PROMPT,
            read_only=True,
            # 拒绝所有写操作
            denied_tools={'write', 'edit', 'delete', 'create'},
        )
        super().__init__(config)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行分析任务
        
        Args:
            task: 分析任务
            context: 上下文（代码、架构图等）
        """
        self.logger.info(f"Oracle开始分析: {task[:50]}...")
        
        try:
            # 构建prompt
            prompt = self._build_oracle_prompt(task, context)
            
            # 调用LLM
            response = await self._call_llm(
                prompt=prompt,
                **kwargs
            )
            
            return AgentResult(
                success=True,
                content=response,
                metadata={
                    'agent': 'oracle',
                    'task': task,
                    'read_only': True,
                }
            )
        
        except Exception as e:
            self.logger.error(f"Oracle分析失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _build_oracle_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建Oracle的prompt"""
        parts = [self.config.system_prompt]
        
        # 添加代码上下文
        if context:
            if 'code' in context:
                parts.append(f"\n## 代码\n```\n{context['code']}\n```")
            
            if 'architecture' in context:
                parts.append(f"\n## 架构\n{context['architecture']}")
            
            if 'files' in context:
                parts.append("\n## 相关文件")
                for file in context['files']:
                    parts.append(f"- {file}")
        
        # 添加任务
        parts.append(f"\n## 分析任务\n{task}")
        
        # 添加指导
        parts.append("\n## 请提供")
        parts.append("1. 深入的分析")
        parts.append("2. 具体的建议")
        parts.append("3. 优先级排序")
        parts.append("4. 实施步骤")
        
        return "\n".join(parts)


def create_oracle_agent() -> OracleAgent:
    """创建Oracle Agent实例"""
    return OracleAgent()
