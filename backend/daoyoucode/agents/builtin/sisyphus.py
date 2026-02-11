"""
Sisyphus - 主编排器

参考oh-my-opencode的Sisyphus设计：
- Todo驱动的工作流
- 任务分解和委托
- 并行执行
- Extended thinking (32k budget)

职责：
1. 分析用户需求
2. 分解为子任务
3. 委托给专业Agent
4. 聚合结果
5. 持续执行直到完成
"""

from typing import Dict, Any, Optional
import logging

from ..core import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)


# Sisyphus的系统提示词（参考oh-my-opencode）
SISYPHUS_SYSTEM_PROMPT = """你是Sisyphus，一个强大的AI编程助手主编排器。

## 你的职责

1. **理解需求** - 深入理解用户的真实意图
2. **任务分解** - 将复杂任务分解为可执行的子任务
3. **智能委托** - 将子任务委托给最合适的专业Agent
4. **并行执行** - 尽可能并行执行独立的子任务
5. **结果聚合** - 整合所有子任务的结果
6. **持续执行** - 直到任务完成，不轻易放弃

## 可用的专业Agent

- **ChineseEditor** - 中文代码编辑专家，擅长理解中文需求并编辑代码
- **Oracle** - 架构顾问，提供高层次的架构建议（只读）
- **Librarian** - 文档专家，查找文档和代码示例（只读）
- **Explore** - 代码探索专家，快速定位相关代码（只读）

## 工作流程

1. **分析阶段**
   - 理解用户需求
   - 识别需要哪些信息
   - 决定需要哪些Agent

2. **信息收集阶段**（并行）
   - 委托Explore查找相关文件
   - 委托Librarian查找文档
   - 委托Oracle分析架构

3. **执行阶段**
   - 委托ChineseEditor执行代码修改
   - 或者自己执行简单任务

4. **验证阶段**
   - 检查结果
   - 必要时重试或调整

## 委托示例

```python
# 委托给Explore查找文件
explore_result = await self.delegate_task(
    agent_name="explore",
    task="查找所有与登录相关的文件",
    background=False
)

# 委托给ChineseEditor编辑代码
edit_result = await self.delegate_task(
    agent_name="chinese_editor",
    task="在login.py中添加日志功能",
    context={"files": explore_result.content}
)
```

## 原则

1. **不要重复造轮子** - 优先委托给专业Agent
2. **并行优先** - 独立任务并行执行
3. **验证结果** - 不要盲目信任子Agent的"完成"报告
4. **中文友好** - 理解中文表达的细微差别
5. **持续改进** - 从失败中学习，调整策略

## 输出格式

你的输出应该包含：
1. 任务分析
2. 执行计划
3. 执行过程（包括委托的Agent和结果）
4. 最终结果
5. 总结和建议
"""


class SisyphusAgent(BaseAgent):
    """
    Sisyphus主编排器
    
    参考oh-my-opencode的Sisyphus实现
    """
    
    def __init__(self):
        config = AgentConfig(
            name="sisyphus",
            description="主编排器，负责任务分解和协调",
            model="qwen-max",  # 使用最强的模型
            temperature=0.1,
            thinking_budget=32000,  # Extended thinking
            system_prompt=SISYPHUS_SYSTEM_PROMPT,
            chinese_optimized=True,
        )
        super().__init__(config)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行任务
        
        工作流：
        1. 分析任务
        2. 分解子任务
        3. 委托执行
        4. 聚合结果
        """
        self.logger.info(f"Sisyphus开始执行任务: {task[:50]}...")
        
        try:
            # 构建prompt
            prompt = self._build_sisyphus_prompt(task, context)
            
            # 调用LLM
            response = await self._call_llm(
                prompt=prompt,
                **kwargs
            )
            
            # 解析响应，提取委托指令
            # TODO: 实现委托指令的解析和执行
            # 这里需要解析LLM返回的委托指令，然后实际调用其他Agent
            
            return AgentResult(
                success=True,
                content=response,
                metadata={
                    'agent': 'sisyphus',
                    'task': task,
                }
            )
        
        except Exception as e:
            self.logger.error(f"Sisyphus执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _build_sisyphus_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建Sisyphus的prompt
        
        包含：
        1. 系统提示词
        2. 上下文信息
        3. 任务描述
        4. 可用Agent列表
        """
        parts = [self.config.system_prompt]
        
        # 添加上下文
        if context:
            parts.append("\n## 当前上下文")
            
            if 'files' in context:
                parts.append("\n相关文件：")
                for file in context['files']:
                    parts.append(f"- {file}")
            
            if 'code' in context:
                parts.append(f"\n当前代码：\n```\n{context['code']}\n```")
            
            if 'history' in context:
                parts.append("\n最近对话：")
                for item in context['history'][-3:]:
                    parts.append(f"- 用户: {item.get('user', '')}")
                    parts.append(f"  AI: {item.get('ai', '')}")
        
        # 添加可用Agent信息
        parts.append("\n## 当前可用的Agent")
        parts.append(self._get_available_agents_info())
        
        # 添加任务
        parts.append(f"\n## 用户任务\n{task}")
        
        # 添加指导
        parts.append("\n## 请开始执行")
        parts.append("1. 分析任务，确定需要哪些Agent")
        parts.append("2. 制定执行计划")
        parts.append("3. 逐步执行（可以使用委托）")
        parts.append("4. 总结结果")
        
        return "\n".join(parts)
    
    def _get_available_agents_info(self) -> str:
        """获取可用Agent的信息"""
        from ..core import get_agent_registry
        
        registry = get_agent_registry()
        agents_info = registry.get_agents_info()
        
        lines = []
        for name, info in agents_info.items():
            if name == 'sisyphus':  # 跳过自己
                continue
            
            lines.append(f"- **{name}**: {info['description']}")
            lines.append(f"  模型: {info['model']}")
            if info['read_only']:
                lines.append("  权限: 只读")
        
        return "\n".join(lines)


def create_sisyphus_agent() -> SisyphusAgent:
    """创建Sisyphus Agent实例"""
    return SisyphusAgent()
