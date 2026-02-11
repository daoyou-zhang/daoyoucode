"""
ChineseEditor - 中文代码编辑专家

参考daoyouCodePilot的中文优化：
- 深度理解中文表达
- 中文注释优化
- 中文变量名处理
- 中文文档生成

职责：
1. 理解中文编辑需求
2. 执行代码修改
3. 生成中文注释和文档
4. 处理中文相关的编码问题
"""

from typing import Dict, Any, Optional
import logging

from ..core import BaseAgent, AgentConfig, AgentResult

logger = logging.getLogger(__name__)


CHINESE_EDITOR_SYSTEM_PROMPT = """你是ChineseEditor，一个专注于中文代码编辑的AI专家。

## 你的特长

1. **深度理解中文** - 理解中文表达的细微差别和隐含意图
2. **代码编辑** - 精确修改代码，保持代码风格一致
3. **中文注释** - 生成清晰、专业的中文注释
4. **中文文档** - 编写易懂的中文文档

## 编辑原则

1. **最小改动** - 只修改必要的部分，保持其他代码不变
2. **风格一致** - 遵循项目现有的代码风格
3. **注释清晰** - 中文注释要简洁明了，避免冗余
4. **测试友好** - 修改后的代码要易于测试

## 中文优化

1. **理解口语化表达**
   - "加个日志" → 添加logging语句
   - "优化一下" → 改进性能或可读性
   - "修复bug" → 定位并修复问题

2. **处理中文注释**
   - 保持注释简洁
   - 使用专业术语
   - 避免机器翻译腔

3. **中文变量名**
   - 支持拼音变量名（如果项目使用）
   - 建议使用英文但提供中文注释

## 编辑模式

你可以使用以下编辑方式：

1. **整文件重写** - 小文件（<100行）直接重写
2. **块编辑** - 修改特定代码块
3. **diff编辑** - 使用diff格式精确修改

选择最合适的方式，确保修改准确无误。

## 输出格式

你的输出应该包含：
1. 修改说明（中文）
2. 修改后的代码
3. 修改原因和注意事项
"""


class ChineseEditorAgent(BaseAgent):
    """
    中文代码编辑专家
    
    参考daoyouCodePilot的中文优化
    """
    
    def __init__(self):
        config = AgentConfig(
            name="chinese_editor",
            description="中文代码编辑专家，深度理解中文需求",
            model="qwen-coder-plus",  # 使用通义千问代码模型
            temperature=0.1,
            system_prompt=CHINESE_EDITOR_SYSTEM_PROMPT,
            chinese_optimized=True,
            # 可以使用所有编辑工具
            denied_tools=set(),
        )
        super().__init__(config)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        执行编辑任务
        
        Args:
            task: 编辑任务（中文描述）
            context: 上下文（包含文件内容等）
        """
        self.logger.info(f"ChineseEditor开始执行: {task[:50]}...")
        
        try:
            # 构建prompt
            prompt = self._build_editor_prompt(task, context)
            
            # 调用LLM
            response = await self._call_llm(
                prompt=prompt,
                **kwargs
            )
            
            # 解析响应，提取代码修改
            # TODO: 实现代码修改的解析和应用
            
            return AgentResult(
                success=True,
                content=response,
                metadata={
                    'agent': 'chinese_editor',
                    'task': task,
                }
            )
        
        except Exception as e:
            self.logger.error(f"ChineseEditor执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _build_editor_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建编辑器的prompt"""
        parts = [self.config.system_prompt]
        
        # 添加文件内容
        if context and 'file_content' in context:
            file_path = context.get('file_path', '未知文件')
            file_content = context['file_content']
            
            parts.append(f"\n## 当前文件: {file_path}")
            parts.append(f"```python\n{file_content}\n```")
        
        # 添加相关文件
        if context and 'related_files' in context:
            parts.append("\n## 相关文件")
            for file_info in context['related_files']:
                parts.append(f"- {file_info}")
        
        # 添加任务
        parts.append(f"\n## 编辑任务\n{task}")
        
        # 添加指导
        parts.append("\n## 请执行以下步骤")
        parts.append("1. 理解任务需求")
        parts.append("2. 分析当前代码")
        parts.append("3. 确定修改方案")
        parts.append("4. 生成修改后的代码")
        parts.append("5. 说明修改原因")
        
        return "\n".join(parts)


def create_chinese_editor_agent() -> ChineseEditorAgent:
    """创建ChineseEditor Agent实例"""
    return ChineseEditorAgent()
