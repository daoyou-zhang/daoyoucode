"""
ReAct循环编排器

实现ReAct（Reason-Act-Observe-Reflect）模式的编排器。

架构说明：
-----------
ReAct循环的核心逻辑已在Agent层实现（通过Function Calling机制）：
- Thought（思考）：LLM分析用户问题，决定是否调用工具
- Action（行动）：执行工具获取信息
- Observation（观察）：处理工具返回的结果
- Reflect（反思）：LLM基于结果决定下一步行动

当前编排器的职责：
-----------------
1. 调用Agent执行任务
2. 准备Prompt和上下文
3. 处理执行结果
4. 返回统一格式的响应

这种设计的优势：
--------------
- 简单高效：LLM自动控制循环，无需额外的规划步骤
- 成本低：减少不必要的LLM调用
- 灵活性：LLM可以根据实际情况动态调整策略
- 易于使用：对用户透明，无需配置复杂参数

扩展方向：
---------
如需更复杂的编排逻辑（如显式规划、多轮反思、强错误恢复），
可以创建AdvancedReActOrchestrator，实现：
- 显式的规划阶段（生成详细的执行计划）
- 显式的反思阶段（分析失败原因并调整策略）
- 更强的错误恢复能力（自动重试和策略调整）

参考：
-----
- daoyouCodePilot的OrchestratorCoder
- REACT_IMPLEMENTATION_STATUS.md（详细说明）
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
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行ReAct循环
        
        注意：ReAct循环的核心逻辑已在Agent层实现（通过Function Calling）。
        Agent会自动进行：
        - Thought（思考）：LLM分析问题
        - Action（行动）：调用工具
        - Observation（观察）：获取工具结果
        - Reflect（反思）：LLM决定下一步
        
        当前编排器负责：
        - 调用Agent执行任务
        - 处理结果和错误
        - 返回统一格式的响应
        
        如需更复杂的编排逻辑（如显式规划、多轮反思、错误恢复），
        可以创建AdvancedReActOrchestrator。
        
        Args:
            skill: 技能定义（SkillConfig对象）
            user_input: 用户输入
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = {}
        
        logger.info(f"ReAct编排器执行: {skill.name}")
        
        try:
            # 1. 智能体循环前：是否预取「了解项目」由 intent.should_prefetch_project_understanding 统一判定
            user_input_stripped = (user_input or "").strip()
            if user_input_stripped:
                from ..tools import get_tool_registry
                from ..intent import should_prefetch_project_understanding
                _tool_reg = get_tool_registry()
                need_project_prefetch, _ = await should_prefetch_project_understanding(skill, user_input_stripped, context)
                use_intent = getattr(skill, "project_understanding_use_intent", False)
                if need_project_prefetch and all(_tool_reg.get_tool(n) for n in ("discover_project_docs", "get_repo_structure", "repo_map")):
                    try:
                        docs_tool = _tool_reg.get_tool("discover_project_docs")
                        struct_tool = _tool_reg.get_tool("get_repo_structure")
                        repo_map_tool = _tool_reg.get_tool("repo_map")
                        # 传足 max_doc_length，否则工具内部默认 5000 会截断，导致「文档没给到」
                        d = await docs_tool.execute(repo_path=".", max_doc_length=12000)
                        s = await struct_tool.execute(repo_path=".", max_depth=3)
                        r = await repo_map_tool.execute(repo_path=".")
                        # 预取块上限：默认 8000/3500/4500；skill 配了 project_understanding_max_chars 时按比例缩小
                        _DOC_CHARS, _STRUCT_CHARS, _REPOMAP_CHARS = 8000, 3500, 4500
                        max_total = getattr(skill, "project_understanding_max_chars", None)
                        if max_total is not None and max_total > 0:
                            _DOC_CHARS = min(8000, max(500, int(max_total * 0.50)))
                            _STRUCT_CHARS = min(3500, max(300, int(max_total * 0.22)))
                            _REPOMAP_CHARS = min(4500, max(300, int(max_total * 0.28)))
                        header = getattr(skill, "project_understanding_header", None) or "概括时请以【项目文档】为主说明项目是啥、核心在哪；【目录结构】【代码地图】仅作参考，切勿逐条罗列文件或类名。\n\n"
                        parts = []
                        if d and getattr(d, "content", None) and d.content:
                            parts.append("【项目文档】\n" + ((d.content[:_DOC_CHARS] + "…") if len(d.content) > _DOC_CHARS else d.content))
                        if s and getattr(s, "content", None) and s.content:
                            parts.append("【目录结构】\n" + ((s.content[:_STRUCT_CHARS] + "…") if len(s.content) > _STRUCT_CHARS else s.content))
                        if r and getattr(r, "content", None) and r.content:
                            parts.append("【代码地图】仅作参考\n" + ((r.content[:_REPOMAP_CHARS] + "…") if len(r.content) > _REPOMAP_CHARS else r.content))
                        if parts:
                            context["project_understanding_block"] = header + "\n\n".join(parts)
                            logger.info("已预取了解项目三层结果并注入 context（编排器内、智能体循环前）")
                    except Exception as e:
                        logger.warning("预取了解项目三层失败: %s", e)
                # 复用意图：need_code_context 时预取 semantic_code_chunks（若 context 已含则跳过，避免与 executor 重复）
                if use_intent and "need_code_context" in context.get("detected_intents", []) and "semantic_code_chunks" not in context:
                    skill_tools = getattr(skill, "tools", None) or []
                    if "semantic_code_search" in skill_tools:
                        try:
                            sem_tool = _tool_reg.get_tool("semantic_code_search")
                            if sem_tool:
                                res = await sem_tool.execute(query=user_input_stripped[:500], top_k=6, repo_path=".")
                                if res and getattr(res, "content", None) and res.content:
                                    context["semantic_code_chunks"] = (res.content[:5000] + "…") if len(res.content) > 5000 else res.content
                                    logger.info("按意图预取 semantic_code_chunks")
                        except Exception as e:
                            logger.warning("按意图预取 semantic 失败: %s", e)
            
            # 2. 获取Agent
            from ..core.agent import get_agent_registry
            registry = get_agent_registry()
            agent = registry.get_agent(skill.agent)
            
            if not agent:
                return {
                    'success': False,
                    'content': '',
                    'error': f"Agent '{skill.agent}' not found"
                }
            
            # 3. 准备prompt
            prompt_source = self._prepare_prompt_source(skill)
            
            # 4. 只传入已注册的工具名，避免 Kiro 等生成的配置里有错误工具名导致不稳定
            from ..tools import get_tool_registry
            tool_registry = get_tool_registry()
            tools_to_use = tool_registry.filter_tool_names(skill.tools if skill.tools else None)
            
            # 5. 执行Agent（带工具）
            result = await agent.execute(
                prompt_source=prompt_source,
                user_input=user_input,
                context=context,
                llm_config=skill.llm,
                tools=tools_to_use
            )
            
            # 5. 返回结果
            return {
                'success': result.success,
                'content': result.content,
                'metadata': {
                    **result.metadata,
                    'skill': skill.name,
                    'agent': skill.agent,
                    'orchestrator': 'react',
                    'tools_used': result.tools_used,
                    'tokens_used': result.tokens_used,
                    'cost': result.cost
                },
                'error': result.error,
                'tools_used': result.tools_used,
                'tokens_used': result.tokens_used,
                'cost': result.cost
            }
        
        except Exception as e:
            logger.error(f"ReAct执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'content': '',
                'error': str(e)
            }
    
    def _prepare_prompt_source(self, skill: Any) -> Dict[str, Any]:
        """准备prompt来源配置"""
        if skill.prompt:
            if isinstance(skill.prompt, dict):
                return skill.prompt
            if isinstance(skill.prompt, str):
                return {'file': skill.prompt}
        
        return {'use_agent_default': True}
    
    # ========================================================================
    # 以下方法为AdvancedReActOrchestrator预留
    # 
    # 当前的简化版本不使用这些方法，但保留它们作为参考实现。
    # 这些方法在 test_advanced_features.py 中有完整的单元测试。
    # 
    # 使用场景：
    # - 当需要显式的规划阶段（生成详细的执行计划）
    # - 当需要显式的反思阶段（分析失败原因并调整策略）
    # - 当需要更强的错误恢复能力（自动重试和策略调整）
    # - 当需要用户批准执行计划
    # - 当需要自动验证执行结果
    # 
    # 实现AdvancedReActOrchestrator时，可以：
    # 1. 继承ReActOrchestrator
    # 2. 重写execute()方法，调用这些预留方法
    # 3. 实现完整的Plan-Execute-Observe-Reflect循环
    # 
    # 参考：
    # - REACT_IMPLEMENTATION_STATUS.md - 详细的实现说明
    # - test_advanced_features.py - 方法的单元测试
    # - daoyouCodePilot的OrchestratorCoder - 原始实现参考
    # ========================================================================
    
    async def _plan(
        self,
        instruction: str,
        context: Context,
        last_error: Optional[str] = None,
        last_plan: Optional[ReActPlan] = None
    ) -> Optional[ReActPlan]:
        """
        [预留方法] 生成执行计划
        
        用于AdvancedReActOrchestrator的显式规划阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 分析任务需求
        - 生成详细的执行步骤
        - 估算时间和复杂度
        - 识别潜在风险
        - 支持基于失败的重新规划
        
        Args:
            instruction: 任务指令
            context: 执行上下文
            last_error: 上次执行的错误信息（用于重新规划）
            last_plan: 上次的执行计划（用于调整策略）
            
        Returns:
            ReActPlan: 执行计划，包含步骤、时间、复杂度、风险
            None: 如果无法生成计划
            
        测试：
            test_advanced_features.py::test_react_plan_generation
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
        [预留方法] 请求用户批准计划
        
        用于AdvancedReActOrchestrator的人工审核阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 展示执行计划给用户
        - 等待用户确认或拒绝
        - 支持计划修改建议
        
        Args:
            plan: 待批准的执行计划
            context: 执行上下文
            
        Returns:
            bool: True表示批准，False表示拒绝
            
        注意：
            实际实现需要集成用户交互机制（CLI/Web界面）
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
        [预留方法] 执行计划
        
        用于AdvancedReActOrchestrator的计划执行阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 按顺序执行计划中的步骤
        - 为每个步骤创建子任务
        - 跟踪执行进度
        - 处理步骤失败（中断执行）
        - 记录执行结果
        
        Args:
            plan: 要执行的计划
            context: 执行上下文
            agents: 可用的Agent列表
            parent_task: 父任务（用于创建子任务）
            
        Returns:
            Dict包含：
            - steps: 每个步骤的执行结果
            - completed: 成功完成的步骤数
            - total: 总步骤数
            
        注意：
            步骤失败时会立即中断，不会继续执行后续步骤
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
        [预留方法] 执行单个步骤
        
        用于AdvancedReActOrchestrator的步骤执行。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 根据步骤类型选择执行方式
        - 调用相应的Agent或工具
        - 返回步骤执行结果
        
        Args:
            step: 步骤定义，包含action和description
            context: 执行上下文
            agents: 可用的Agent列表
            
        Returns:
            Any: 步骤执行结果（格式取决于步骤类型）
            
        测试：
            test_advanced_features.py::test_react_step_execution
            
        注意：
            当前实现是示例，实际使用时需要根据action类型
            调用相应的Agent或工具
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
        [预留方法] 观察执行结果
        
        用于AdvancedReActOrchestrator的结果观察阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 检查执行结果是否成功
        - 识别失败的步骤
        - 自动验证结果（如果启用）
        - 生成观察报告
        
        Args:
            result: 执行结果（来自_execute_plan）
            context: 执行上下文
            
        Returns:
            Dict包含：
            - success: 是否成功
            - error: 错误信息（如果失败）
            - failed_step: 失败的步骤编号
            - verification: 验证结果（如果启用auto_verify）
            
        测试：
            test_advanced_features.py::test_react_observation
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
        [预留方法] 验证执行结果
        
        用于AdvancedReActOrchestrator的自动验证阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 运行诊断工具检查代码问题
        - 运行测试验证功能
        - 检查文件变更是否符合预期
        - 生成验证报告
        
        Args:
            result: 执行结果
            context: 执行上下文
            
        Returns:
            Dict包含：
            - success: 验证是否通过
            - diagnostics: 诊断结果
            - tests: 测试结果
            - error: 错误信息（如果验证失败）
            
        注意：
            当前实现是示例，实际使用时需要集成：
            - 代码诊断工具（linter, type checker）
            - 测试框架（pytest, unittest）
            - 文件变更检查
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
        [预留方法] 反思失败原因并生成新指令
        
        用于AdvancedReActOrchestrator的反思阶段。
        当前简化版本不使用此方法，但保留作为参考实现。
        
        功能：
        - 分析失败原因（使用FeedbackLoop）
        - 识别错误类型和根因
        - 生成恢复建议
        - 调整执行策略
        - 生成新的指令用于重试
        
        Args:
            original_instruction: 最初的任务指令
            current_instruction: 当前尝试的指令
            error: 错误信息
            plan: 失败的执行计划
            context: 执行上下文
            attempt: 当前尝试次数（用于限制重试）
            
        Returns:
            str: 新的指令用于重试
            None: 如果无法恢复（达到最大重试次数或无法生成策略）
            
        测试：
            test_advanced_features.py::test_react_reflection
            
        注意：
            - 使用FeedbackLoop进行失败分析
            - 需要LLM生成新的指令
            - 应该限制最大反思次数（max_reflections）
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
