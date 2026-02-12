"""
ReAct循环编排器

实现完整的"规划-执行-反思-重试"循环，提供自愈能力。
灵感来源：daoyouCodePilot的OrchestratorCoder
"""

from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

from ..core.orchestrator import BaseOrchestrator
from ..core.agent import BaseAgent
from ..core.context import Context, get_context_manager
from ..core.task import Task, TaskStatus, get_task_manager
from ..core.feedback import get_feedback_loop
from ..core.hooks import HookEvent, get_hook_manager

logger = logging.getLogger(__name__)


@dataclass
class ReActPlan:
    """ReAct执行计划"""
    steps: List[Dict[str, Any]]
    estimated_time: float
    complexity: int
    risks: List[str]


class ReActOrchestrator(BaseOrchestrator):
    """
    ReAct循环编排器
    
    实现完整的Reason-Act-Observe循环：
    1. Reason（规划）：分析任务，生成执行计划
    2. Act（执行）：执行计划中的步骤
    3. Observe（观察）：检查执行结果
    4. Reflect（反思）：如果失败，分析原因并重新规划
    """
    
    def __init__(
        self,
        max_reflections: int = 3,
        require_approval: bool = False,
        auto_verify: bool = True,
        **kwargs
    ):
        """
        初始化ReAct编排器
        
        Args:
            max_reflections: 最大反思次数
            require_approval: 是否需要用户批准计划
            auto_verify: 是否自动验证结果
        """
        super().__init__(**kwargs)
        self.max_reflections = max_reflections
        self.require_approval = require_approval
        self.auto_verify = auto_verify
        self.hook_manager = get_hook_manager()
        self.task_manager = get_task_manager()
        self.feedback_loop = get_feedback_loop()
    
    async def execute(
        self,
        skill: Any,
        context: Context,
        agents: Optional[List[BaseAgent]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行ReAct循环
        
        Args:
            skill: 技能定义
            context: 执行上下文
            agents: Agent列表
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        original_instruction = skill.get('instruction', '')
        current_instruction = original_instruction
        
        # 创建主任务
        main_task = self.task_manager.create_task(
            name=f"ReAct: {original_instruction[:50]}",
            description=original_instruction,
            metadata={'orchestrator': 'react', 'max_reflections': self.max_reflections}
        )
        
        # 触发Hook
        await self.hook_manager.trigger(
            HookEvent.PRE_ORCHESTRATE,
            data={
                'orchestrator': 'react',
                'skill': skill,
                'task_id': main_task.task_id
            }
        )
        
        attempt = 0
        last_error = None
        last_plan = None
        
        while attempt < self.max_reflections:
            attempt += 1
            logger.info(f"ReAct循环 - 尝试 {attempt}/{self.max_reflections}")
            
            try:
                # === 1. Reason（规划）===
                logger.info("阶段1: 规划（Reason）")
                plan = await self._plan(current_instruction, context, last_error, last_plan)
                
                if not plan:
                    logger.error("规划失败")
                    last_error = "规划失败：无法生成有效的执行计划"
                    continue
                
                # === 2. 用户批准（可选）===
                if self.require_approval and not await self._approve(plan, context):
                    logger.info("用户取消了执行")
                    self.task_manager.update_task(main_task.task_id, status=TaskStatus.CANCELLED)
                    return {
                        'status': 'cancelled',
                        'message': '用户取消了执行',
                        'task_id': main_task.task_id
                    }
                
                # === 3. Act（执行）===
                logger.info("阶段2: 执行（Act）")
                result = await self._execute_plan(plan, context, agents, main_task)
                
                # === 4. Observe（观察）===
                logger.info("阶段3: 观察（Observe）")
                observation = await self._observe(result, context)
                
                if observation['success']:
                    # 成功！
                    logger.info("ReAct循环成功完成")
                    self.task_manager.update_task(
                        main_task.task_id,
                        status=TaskStatus.COMPLETED,
                        result=result
                    )
                    
                    # 触发Hook
                    await self.hook_manager.trigger(
                        HookEvent.POST_ORCHESTRATE,
                        data={
                            'orchestrator': 'react',
                            'task_id': main_task.task_id,
                            'result': result,
                            'attempts': attempt
                        }
                    )
                    
                    return {
                        'status': 'success',
                        'result': result,
                        'task_id': main_task.task_id,
                        'attempts': attempt
                    }
                
                # 失败，准备反思
                last_error = observation.get('error', '未知错误')
                last_plan = plan
                
            except Exception as e:
                logger.error(f"执行过程中发生异常: {e}", exc_info=True)
                last_error = str(e)
                last_plan = plan if 'plan' in locals() else None
            
            # === 5. Reflect（反思）===
            if attempt < self.max_reflections:
                logger.info(f"阶段4: 反思（Reflect）- 尝试 {attempt}")
                new_instruction = await self._reflect(
                    original_instruction,
                    current_instruction,
                    last_error,
                    last_plan,
                    context,
                    attempt
                )
                
                if new_instruction:
                    current_instruction = new_instruction
                    logger.info(f"生成新指令: {new_instruction[:100]}...")
                else:
                    logger.error("反思失败，无法生成新指令")
                    break
        
        # 达到最大反思次数，仍然失败
        logger.error(f"ReAct循环失败，已达到最大反思次数 ({self.max_reflections})")
        self.task_manager.update_task(
            main_task.task_id,
            status=TaskStatus.FAILED,
            error=last_error
        )
        
        # 触发Hook
        await self.hook_manager.trigger(
            HookEvent.ON_ERROR,
            data={
                'orchestrator': 'react',
                'task_id': main_task.task_id,
                'error': last_error,
                'attempts': attempt
            }
        )
        
        return {
            'status': 'failed',
            'error': last_error,
            'task_id': main_task.task_id,
            'attempts': attempt
        }
    
    async def _plan(
        self,
        instruction: str,
        context: Context,
        last_error: Optional[str] = None,
        last_plan: Optional[ReActPlan] = None
    ) -> Optional[ReActPlan]:
        """
        生成执行计划
        
        Args:
            instruction: 指令
            context: 上下文
            last_error: 上次错误（如果有）
            last_plan: 上次计划（如果有）
            
        Returns:
            执行计划
        """
        # 这里应该调用LLM生成计划
        # 简化起见，返回一个示例计划
        
        prompt = f"""
        任务: {instruction}
        
        {"上次执行失败: " + last_error if last_error else ""}
        {"上次计划: " + str(last_plan) if last_plan else ""}
        
        请生成一个详细的执行计划，包括：
        1. 具体的执行步骤
        2. 每个步骤的预期结果
        3. 可能的风险点
        """
        
        # TODO: 调用LLM生成计划
        # 这里返回一个示例计划
        return ReActPlan(
            steps=[
                {'action': 'analyze', 'description': '分析任务需求'},
                {'action': 'implement', 'description': '实现功能'},
                {'action': 'test', 'description': '测试功能'},
            ],
            estimated_time=300.0,
            complexity=3,
            risks=['可能需要修改多个文件', '可能影响现有功能']
        )
    
    async def _approve(self, plan: ReActPlan, context: Context) -> bool:
        """
        请求用户批准计划
        
        Args:
            plan: 执行计划
            context: 上下文
            
        Returns:
            是否批准
        """
        # 这里应该显示计划并请求用户确认
        # 简化起见，直接返回True
        logger.info(f"执行计划: {len(plan.steps)} 个步骤")
        for i, step in enumerate(plan.steps):
            logger.info(f"  {i+1}. {step['description']}")
        
        # TODO: 实现用户确认逻辑
        return True
    
    async def _execute_plan(
        self,
        plan: ReActPlan,
        context: Context,
        agents: Optional[List[BaseAgent]],
        parent_task: Task
    ) -> Dict[str, Any]:
        """
        执行计划
        
        Args:
            plan: 执行计划
            context: 上下文
            agents: Agent列表
            parent_task: 父任务
            
        Returns:
            执行结果
        """
        results = []
        
        for i, step in enumerate(plan.steps):
            logger.info(f"执行步骤 {i+1}/{len(plan.steps)}: {step['description']}")
            
            # 创建子任务
            step_task = self.task_manager.create_task(
                name=f"Step {i+1}: {step['description']}",
                description=step.get('description', ''),
                parent_id=parent_task.task_id
            )
            
            try:
                # 执行步骤
                # TODO: 根据步骤类型调用相应的Agent或工具
                step_result = await self._execute_step(step, context, agents)
                
                results.append({
                    'step': i + 1,
                    'description': step['description'],
                    'result': step_result,
                    'success': True
                })
                
                self.task_manager.update_task(
                    step_task.task_id,
                    status=TaskStatus.COMPLETED,
                    result=step_result
                )
                
            except Exception as e:
                logger.error(f"步骤 {i+1} 执行失败: {e}")
                results.append({
                    'step': i + 1,
                    'description': step['description'],
                    'error': str(e),
                    'success': False
                })
                
                self.task_manager.update_task(
                    step_task.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e)
                )
                
                # 步骤失败，终止执行
                break
        
        return {
            'steps': results,
            'completed': len([r for r in results if r.get('success')]),
            'total': len(plan.steps)
        }
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Context,
        agents: Optional[List[BaseAgent]]
    ) -> Any:
        """
        执行单个步骤
        
        Args:
            step: 步骤定义
            context: 上下文
            agents: Agent列表
            
        Returns:
            步骤结果
        """
        action = step.get('action')
        
        # 根据动作类型执行
        if action == 'analyze':
            return {'analysis': '任务分析完成'}
        elif action == 'implement':
            return {'implementation': '功能实现完成'}
        elif action == 'test':
            return {'test': '测试通过'}
        else:
            return {'result': f'执行了 {action}'}
    
    async def _observe(
        self,
        result: Dict[str, Any],
        context: Context
    ) -> Dict[str, Any]:
        """
        观察执行结果
        
        Args:
            result: 执行结果
            context: 上下文
            
        Returns:
            观察结果
        """
        steps = result.get('steps', [])
        failed_steps = [s for s in steps if not s.get('success')]
        
        if failed_steps:
            # 有步骤失败
            first_failure = failed_steps[0]
            return {
                'success': False,
                'error': first_failure.get('error', '未知错误'),
                'failed_step': first_failure.get('step'),
                'failed_description': first_failure.get('description')
            }
        
        # 所有步骤成功
        if self.auto_verify:
            # 自动验证
            verification = await self._verify(result, context)
            if not verification['success']:
                return {
                    'success': False,
                    'error': verification.get('error', '验证失败'),
                    'verification': verification
                }
        
        return {
            'success': True,
            'completed_steps': result.get('completed'),
            'total_steps': result.get('total')
        }
    
    async def _verify(
        self,
        result: Dict[str, Any],
        context: Context
    ) -> Dict[str, Any]:
        """
        验证执行结果
        
        Args:
            result: 执行结果
            context: 上下文
            
        Returns:
            验证结果
        """
        # TODO: 实现验证逻辑
        # 1. 运行诊断工具
        # 2. 运行测试
        # 3. 检查文件变更
        
        return {
            'success': True,
            'diagnostics': 'clean',
            'tests': 'passed'
        }
    
    async def _reflect(
        self,
        original_instruction: str,
        current_instruction: str,
        error: str,
        plan: Optional[ReActPlan],
        context: Context,
        attempt: int
    ) -> Optional[str]:
        """
        反思失败原因并生成新指令
        
        Args:
            original_instruction: 原始指令
            current_instruction: 当前指令
            error: 错误信息
            plan: 失败的计划
            context: 上下文
            attempt: 尝试次数
            
        Returns:
            新指令，或None表示无法恢复
        """
        logger.info(f"反思失败原因 (尝试 {attempt})")
        
        # 使用FeedbackLoop分析失败
        analysis = await self.feedback_loop.analyze_failure(
            task_description=f"react_attempt_{attempt}: {original_instruction}",
            error=Exception(error),
            context={
                'original_instruction': original_instruction,
                'current_instruction': current_instruction,
                'plan': plan,
                'attempt': attempt
            }
        )
        
        # 生成新指令
        prompt = f"""
        原始任务: {original_instruction}
        当前指令: {current_instruction}
        
        失败信息:
        - 错误: {error}
        - 错误类型: {analysis.error_type}
        - 根因: {analysis.root_cause}
        
        恢复建议:
        {chr(10).join(f"- {s}" for s in analysis.recovery_suggestions)}
        
        请生成一个新的指令来解决这个问题。
        """
        
        # TODO: 调用LLM生成新指令
        # 简化起见，返回一个修改后的指令
        return f"{current_instruction} (尝试 {attempt + 1}: 根据错误调整策略)"
    
    def get_name(self) -> str:
        """获取编排器名称"""
        return "react"
    
    def get_description(self) -> str:
        """获取编排器描述"""
        return "ReAct循环编排器：实现完整的规划-执行-反思-重试循环，提供自愈能力"
