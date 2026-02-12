"""
动态Prompt构建器

支持：
- 条件化内容
- 模板渲染
- Prompt优化
- Token计数
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class PromptSection:
    """Prompt段落"""
    name: str
    content: str
    condition: Optional[Callable[[Dict], bool]] = None
    priority: int = 0  # 优先级，数字越大越重要


class DynamicPromptBuilder:
    """动态Prompt构建器"""
    
    def __init__(self):
        self.sections: List[PromptSection] = []
        self.logger = logging.getLogger("prompt_builder")
    
    def add_section(
        self,
        name: str,
        content: str,
        condition: Optional[Callable[[Dict], bool]] = None,
        priority: int = 0
    ):
        """
        添加Prompt段落
        
        Args:
            name: 段落名称
            content: 段落内容（支持Jinja2模板）
            condition: 条件函数，返回True时包含此段落
            priority: 优先级（用于优化时保留重要段落）
        """
        section = PromptSection(
            name=name,
            content=content,
            condition=condition,
            priority=priority
        )
        self.sections.append(section)
        self.logger.debug(f"添加段落: {name} (优先级: {priority})")
    
    def build(
        self,
        context: Dict[str, Any],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        构建最终Prompt
        
        Args:
            context: 上下文数据
            max_tokens: 最大token数（可选）
        
        Returns:
            构建的Prompt
        """
        parts = []
        
        # 1. 筛选段落（根据条件）
        active_sections = []
        for section in self.sections:
            if section.condition:
                try:
                    if not section.condition(context):
                        self.logger.debug(f"跳过段落 {section.name}（条件不满足）")
                        continue
                except Exception as e:
                    self.logger.warning(f"段落 {section.name} 条件评估失败: {e}")
                    continue
            
            active_sections.append(section)
        
        # 2. 渲染段落
        rendered_sections = []
        for section in active_sections:
            try:
                rendered = self._render_template(section.content, context)
                rendered_sections.append({
                    'name': section.name,
                    'content': rendered,
                    'priority': section.priority,
                    'tokens': self._count_tokens(rendered)
                })
            except Exception as e:
                self.logger.error(f"段落 {section.name} 渲染失败: {e}")
        
        # 3. 优化（如果需要）
        if max_tokens:
            rendered_sections = self._optimize_sections(
                rendered_sections,
                max_tokens
            )
        
        # 4. 拼接
        for section in rendered_sections:
            parts.append(section['content'])
        
        final_prompt = "\n\n".join(parts)
        
        self.logger.info(
            f"构建Prompt完成: {len(rendered_sections)} 个段落, "
            f"{self._count_tokens(final_prompt)} tokens"
        )
        
        return final_prompt
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染模板"""
        return Template(template).render(**context)
    
    def _count_tokens(self, text: str) -> int:
        """计算tokens（简化版本）"""
        # 简化计算：1 token ≈ 4 字符（英文）或 1.5 字符（中文）
        # 实际应该使用tiktoken或litellm
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def _optimize_sections(
        self,
        sections: List[Dict],
        max_tokens: int
    ) -> List[Dict]:
        """
        优化段落以适应token限制
        
        策略：
        1. 按优先级排序
        2. 保留高优先级段落
        3. 压缩或移除低优先级段落
        """
        # 计算总tokens
        total_tokens = sum(s['tokens'] for s in sections)
        
        if total_tokens <= max_tokens:
            return sections
        
        self.logger.info(
            f"Prompt过长 ({total_tokens} tokens > {max_tokens}), 开始优化"
        )
        
        # 按优先级排序（降序）
        sorted_sections = sorted(
            sections,
            key=lambda s: s['priority'],
            reverse=True
        )
        
        # 保留段落直到达到限制
        optimized = []
        current_tokens = 0
        
        for section in sorted_sections:
            if current_tokens + section['tokens'] <= max_tokens:
                optimized.append(section)
                current_tokens += section['tokens']
            else:
                self.logger.debug(
                    f"移除段落 {section['name']} (优先级: {section['priority']})"
                )
        
        # 恢复原始顺序
        optimized.sort(key=lambda s: sections.index(s))
        
        self.logger.info(
            f"优化完成: 保留 {len(optimized)}/{len(sections)} 个段落, "
            f"{current_tokens} tokens"
        )
        
        return optimized
    
    def clear(self):
        """清空所有段落"""
        self.sections.clear()


class PromptOptimizer:
    """Prompt优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger("prompt_optimizer")
    
    async def optimize(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: int
    ) -> str:
        """
        优化Prompt长度
        
        策略：
        1. 移除示例
        2. 压缩历史
        3. 摘要化
        """
        current_tokens = self._count_tokens(prompt)
        
        if current_tokens <= max_tokens:
            return prompt
        
        self.logger.info(
            f"Prompt过长 ({current_tokens} > {max_tokens}), 开始优化"
        )
        
        # 1. 移除示例
        prompt = self._remove_examples(prompt)
        current_tokens = self._count_tokens(prompt)
        
        if current_tokens <= max_tokens:
            self.logger.info("优化完成（移除示例）")
            return prompt
        
        # 2. 压缩历史
        if 'conversation_history' in context:
            context['conversation_history'] = self._compress_history(
                context['conversation_history'],
                max_length=5
            )
            # 重新渲染prompt（如果是模板）
            # 这里简化处理
        
        # 3. 截断
        if current_tokens > max_tokens:
            prompt = self._truncate(prompt, max_tokens)
        
        self.logger.info("优化完成")
        return prompt
    
    def _count_tokens(self, text: str) -> int:
        """计算tokens"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def _remove_examples(self, prompt: str) -> str:
        """移除示例"""
        import re
        # 移除 <example>...</example> 标签
        return re.sub(
            r'<example>.*?</example>',
            '',
            prompt,
            flags=re.DOTALL
        )
    
    def _compress_history(
        self,
        history: List[Dict],
        max_length: int
    ) -> List[Dict]:
        """压缩历史"""
        if len(history) <= max_length:
            return history
        
        # 保留最近的N条
        return history[-max_length:]
    
    def _truncate(self, prompt: str, max_tokens: int) -> str:
        """截断prompt"""
        # 简化：按字符截断
        max_chars = max_tokens * 4  # 粗略估计
        
        if len(prompt) <= max_chars:
            return prompt
        
        return prompt[:max_chars] + "\n\n[内容已截断]"


# 预定义的常用条件
def is_followup(context: Dict) -> bool:
    """是否是追问"""
    return context.get('is_followup', False)


def has_history(context: Dict) -> bool:
    """是否有历史"""
    return bool(context.get('conversation_history'))


def has_tools(context: Dict) -> bool:
    """是否有工具"""
    return bool(context.get('tools'))


def has_code_context(context: Dict) -> bool:
    """是否有代码上下文"""
    return bool(context.get('code_context'))


# 预定义的Prompt模板
ROLE_TEMPLATE = """你是{{agent_name}}，专注于{{domain}}。"""

HISTORY_TEMPLATE = """历史对话摘要：
{{summary}}"""

TOOLS_TEMPLATE = """可用工具：
{% for tool in tools %}
- {{tool.name}}: {{tool.description}}
{% endfor %}"""

CODE_CONTEXT_TEMPLATE = """相关代码：
{% for name, code in code_context.items() %}
[{{name}}]
```
{{code}}
```
{% endfor %}"""
