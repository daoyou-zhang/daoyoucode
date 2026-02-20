"""
结构化委托系统

提供7段式委托提示结构，提升子Agent成功率。
采用结构化委托设计
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DelegationPrompt:
    """
    结构化的委托提示
    
    7段式结构：
    1. TASK: 原子化、具体的目标
    2. EXPECTED OUTCOME: 具体的交付物和成功标准
    3. REQUIRED SKILLS: 需要调用的技能
    4. REQUIRED TOOLS: 明确的工具白名单
    5. MUST DO: 详尽的需求
    6. MUST NOT DO: 禁止的行为
    7. CONTEXT: 文件路径、现有模式、约束
    """
    
    task: str                                    # 1. 任务描述
    expected_outcome: str                        # 2. 预期结果
    required_skills: List[str] = field(default_factory=list)   # 3. 需要的技能
    required_tools: List[str] = field(default_factory=list)    # 4. 需要的工具
    must_do: List[str] = field(default_factory=list)           # 5. 必须做的事
    must_not_do: List[str] = field(default_factory=list)       # 6. 禁止做的事
    context: Dict[str, Any] = field(default_factory=dict)      # 7. 上下文信息
    
    def to_prompt(self) -> str:
        """转换为提示文本"""
        sections = []
        
        # 1. TASK
        sections.append("## TASK")
        sections.append(self.task)
        sections.append("")
        
        # 2. EXPECTED OUTCOME
        sections.append("## EXPECTED OUTCOME")
        sections.append(self.expected_outcome)
        sections.append("")
        
        # 3. REQUIRED SKILLS
        if self.required_skills:
            sections.append("## REQUIRED SKILLS")
            sections.extend(f"- {skill}" for skill in self.required_skills)
            sections.append("")
        
        # 4. REQUIRED TOOLS
        if self.required_tools:
            sections.append("## REQUIRED TOOLS")
            sections.extend(f"- {tool}" for tool in self.required_tools)
            sections.append("")
        
        # 5. MUST DO
        if self.must_do:
            sections.append("## MUST DO")
            sections.extend(f"- {item}" for item in self.must_do)
            sections.append("")
        
        # 6. MUST NOT DO
        if self.must_not_do:
            sections.append("## MUST NOT DO")
            sections.extend(f"- {item}" for item in self.must_not_do)
            sections.append("")
        
        # 7. CONTEXT
        if self.context:
            sections.append("## CONTEXT")
            sections.append(json.dumps(self.context, indent=2, ensure_ascii=False))
            sections.append("")
        
        return "\n".join(sections)
    
    def validate(self) -> bool:
        """验证提示是否完整"""
        if not self.task:
            logger.warning("委托提示缺少TASK")
            return False
        
        if not self.expected_outcome:
            logger.warning("委托提示缺少EXPECTED OUTCOME")
            return False
        
        return True


class DelegationManager:
    """委托管理器"""
    
    def __init__(self):
        self.delegation_history: List[Dict] = []
    
    async def delegate(
        self,
        agent: Any,
        prompt: DelegationPrompt,
        verify: bool = True,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        委托任务给子Agent
        
        Args:
            agent: 子Agent
            prompt: 结构化提示
            verify: 是否验证结果
            max_retries: 最大重试次数
        
        Returns:
            执行结果
        """
        # 1. 验证提示
        if not prompt.validate():
            return {
                'status': 'error',
                'error': '委托提示不完整'
            }
        
        # 2. 生成完整提示
        full_prompt = prompt.to_prompt()
        
        # 3. 记录委托
        delegation_record = {
            'agent': agent.__class__.__name__ if hasattr(agent, '__class__') else str(agent),
            'task': prompt.task,
            'expected_outcome': prompt.expected_outcome,
        }
        
        # 4. 执行委托（带重试）
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"委托任务给 {delegation_record['agent']} (尝试 {attempt + 1}/{max_retries + 1})")
                
                # 执行
                if hasattr(agent, 'execute'):
                    result = await agent.execute(full_prompt)
                else:
                    result = await agent(full_prompt)
                
                # 5. 验证结果（如果启用）
                if verify:
                    verification = self._verify_result(result, prompt.expected_outcome)
                    if not verification['success']:
                        if attempt < max_retries:
                            logger.warning(f"结果验证失败: {verification['reason']}, 重试...")
                            continue
                        else:
                            logger.error(f"结果验证失败: {verification['reason']}, 已达最大重试次数")
                            result['verification_failed'] = True
                            result['verification_reason'] = verification['reason']
                
                # 6. 记录成功
                delegation_record['status'] = 'success'
                delegation_record['attempts'] = attempt + 1
                self.delegation_history.append(delegation_record)
                
                return result
            
            except Exception as e:
                logger.error(f"委托执行失败 (尝试 {attempt + 1}): {e}")
                if attempt >= max_retries:
                    delegation_record['status'] = 'failed'
                    delegation_record['error'] = str(e)
                    delegation_record['attempts'] = attempt + 1
                    self.delegation_history.append(delegation_record)
                    
                    return {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return {
            'status': 'error',
            'error': '未知错误'
        }
    
    def _verify_result(
        self,
        result: Dict[str, Any],
        expected_outcome: str
    ) -> Dict[str, Any]:
        """
        验证结果是否符合预期
        
        Args:
            result: 执行结果
            expected_outcome: 预期结果描述
        
        Returns:
            {
                'success': bool,
                'reason': str
            }
        """
        # 基本验证
        if not result:
            return {
                'success': False,
                'reason': '结果为空'
            }
        
        if result.get('status') == 'error':
            return {
                'success': False,
                'reason': f"执行错误: {result.get('error', '未知错误')}"
            }
        
        # TODO: 可以使用LLM进行更智能的验证
        # 这里简化为检查是否有结果
        if result.get('status') == 'success':
            return {
                'success': True,
                'reason': '执行成功'
            }
        
        return {
            'success': True,
            'reason': '基本验证通过'
        }
    
    def get_delegation_stats(self) -> Dict[str, Any]:
        """获取委托统计"""
        total = len(self.delegation_history)
        if total == 0:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        success = sum(1 for d in self.delegation_history if d.get('status') == 'success')
        failed = total - success
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': success / total if total > 0 else 0.0,
            'avg_attempts': sum(d.get('attempts', 1) for d in self.delegation_history) / total
        }


# 便捷函数
def create_delegation_prompt(
    task: str,
    expected_outcome: str,
    **kwargs
) -> DelegationPrompt:
    """
    创建委托提示
    
    Args:
        task: 任务描述
        expected_outcome: 预期结果
        **kwargs: 其他参数（required_skills, required_tools, must_do, must_not_do, context）
    """
    return DelegationPrompt(
        task=task,
        expected_outcome=expected_outcome,
        required_skills=kwargs.get('required_skills', []),
        required_tools=kwargs.get('required_tools', []),
        must_do=kwargs.get('must_do', []),
        must_not_do=kwargs.get('must_not_do', []),
        context=kwargs.get('context', {})
    )
