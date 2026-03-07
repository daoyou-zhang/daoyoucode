"""
单Agent编排器（增强版）

直接执行单个Agent，支持：
- 自动重试机制
- 结果验证
- 成本追踪
- 执行时间统计
- 项目信息预取（ReAct模式）

说明：
- ReAct循环（Reason-Act-Observe-Reflect）已在Agent层通过Function Calling实现
- 编排器负责调用Agent、预取信息、重试和结果验证
- 原ReActOrchestrator已合并到此编排器
"""

from typing import Dict, Any, Optional
import time
import asyncio
from ..core.orchestrator import BaseOrchestrator


class SimpleOrchestrator(BaseOrchestrator):
    """
    单Agent编排器（增强版）
    
    功能：
    - 自动重试机制
    - 结果验证
    - 成本追踪
    - 执行时间统计
    - 项目信息预取（可选）
    
    ReAct循环说明：
    - Thought（思考）：LLM分析问题
    - Action（行动）：调用工具
    - Observation（观察）：获取工具结果
    - Reflect（反思）：LLM决定下一步
    以上循环已在Agent层通过Function Calling自动实现
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill（带重试）"""
        if context is None:
            context = {}
        
        # 获取配置的重试次数（优先使用Skill配置）
        max_retries = getattr(skill, 'max_retries', self.max_retries)
        retry_delay = getattr(skill, 'retry_delay', self.retry_delay)
        
        self.logger.info(f"执行Skill: {skill.name}, Agent: {skill.agent}, 最大重试: {max_retries}")
        
        start_time = time.time()
        last_error = None
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                # 执行一次
                result = await self._execute_once(skill, user_input, context)
                
                # 验证结果
                if self._validate_result(result):
                    # 成功，添加元数据
                    duration = time.time() - start_time
                    result['metadata']['duration'] = duration
                    result['metadata']['retries'] = attempt
                    
                    self.logger.info(f"执行成功，耗时: {duration:.2f}s, 重试次数: {attempt}")
                    return result
                
                # 结果无效，记录并重试
                self.logger.warning(f"结果验证失败，重试 {attempt + 1}/{max_retries}")
                last_error = "结果验证失败"
                
                # 等待后重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
            
            except Exception as e:
                last_error = e
                self.logger.error(f"执行失败 {attempt + 1}/{max_retries}: {e}")
                
                # 等待后重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        # 所有重试都失败
        duration = time.time() - start_time
        
        return {
            'success': False,
            'content': '',
            'error': f'执行失败（已重试{max_retries}次）: {last_error}',
            'metadata': {
                'skill': skill.name,
                'agent': skill.agent,
                'orchestrator': 'simple',
                'duration': duration,
                'retries': max_retries,
                'failed': True
            },
            'tools_used': [],
            'tokens_used': 0,
            'cost': 0.0
        }
    
    async def _execute_once(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行一次（不重试）"""
        
        # 🆕 0. 项目信息预取（如果需要）
        await self._prefetch_project_info(skill, user_input, context)
        
        # 1. 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                self.logger.debug(f"应用中间件: {middleware_name}")
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 2. 获取Agent
        agent = self._get_agent(skill.agent)
        
        # 3. 准备prompt来源
        prompt_source = self._prepare_prompt_source(skill)
        
        # 4. 只传入已注册的工具名
        from ..tools import get_tool_registry
        tools_to_use = get_tool_registry().filter_tool_names(skill.tools if skill.tools else None)
        
        # 5. 执行Agent
        result = await agent.execute(
            prompt_source=prompt_source,
            user_input=user_input,
            context=context,
            llm_config=skill.llm,
            tools=tools_to_use,
            enable_streaming=context.get('enable_streaming', False)  # 🆕 传递流式标志
        )
        
        # 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            # 流式输出模式，直接返回生成器
            return result
        
        # 6. 返回结果（非流式模式）
        return {
            'success': result.success,
            'content': result.content,
            'metadata': {
                **result.metadata,
                'skill': skill.name,
                'agent': skill.agent,
                'orchestrator': 'simple',
                'tools_used': result.tools_used,
                'tokens_used': result.tokens_used,
                'cost': result.cost
            },
            'error': result.error,
            'tools_used': result.tools_used,
            'tokens_used': result.tokens_used,
            'cost': result.cost
        }
    
    async def _prefetch_project_info(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Dict[str, Any]
    ) -> None:
        """
        预取项目信息（可选）
        
        根据意图判断是否需要预取项目文档、目录结构、代码地图
        """
        user_input_stripped = (user_input or "").strip()
        if not user_input_stripped:
            return
        
        try:
            from ..tools import get_tool_registry
            from ..core.intent import should_prefetch_project_understanding
            
            _tool_reg = get_tool_registry()
            need_project_prefetch, detected_intents, prefetch_level = await should_prefetch_project_understanding(
                skill, user_input_stripped, context
            )
            
            self.logger.info(f"[预取判定] 需要预取: {need_project_prefetch}, 级别: {prefetch_level}, 意图: {detected_intents}")
            
            # 检查工具是否可用
            has_tools = all(_tool_reg.get_tool(n) for n in ("discover_project_docs", "get_repo_structure", "repo_map"))
            
            if need_project_prefetch and has_tools and prefetch_level != "none":
                self.logger.info(f"[预取执行] 开始预取项目理解（级别: {prefetch_level}）")
                
                docs_tool = _tool_reg.get_tool("discover_project_docs")
                struct_tool = _tool_reg.get_tool("get_repo_structure")
                repo_map_tool = _tool_reg.get_tool("repo_map")
                
                parts = []
                header = getattr(skill, "project_understanding_header", None) or \
                    "理解项目时，重点关注【代码地图】（核心代码和架构），【目录结构】帮助定位，【项目文档】提供背景。用1-2段话概括项目核心，不要逐条罗列。\n\n"
                
                # 根据级别决定调用哪些工具
                if prefetch_level == "full":
                    # 完整预取：文档+结构+地图
                    self.logger.info("[预取执行] 调用 discover_project_docs")
                    d = await docs_tool.execute(repo_path=".", max_doc_length=12000)
                    if d and getattr(d, "content", None) and d.content:
                        _DOC_CHARS = 8000
                        parts.append("【项目文档】\n" + ((d.content[:_DOC_CHARS] + "…") if len(d.content) > _DOC_CHARS else d.content))
                        self.logger.info(f"[预取执行] discover_project_docs 完成，内容长度: {len(d.content)}")
                
                if prefetch_level in ("full", "medium"):
                    # 中等预取：结构+地图
                    self.logger.info("[预取执行] 调用 get_repo_structure")
                    s = await struct_tool.execute(repo_path=".", max_depth=3)
                    if s and getattr(s, "content", None) and s.content:
                        _STRUCT_CHARS = 3500
                        parts.append("【目录结构】\n" + ((s.content[:_STRUCT_CHARS] + "…") if len(s.content) > _STRUCT_CHARS else s.content))
                        self.logger.info(f"[预取执行] get_repo_structure 完成，内容长度: {len(s.content)}")
                
                # 所有级别都调用 repo_map
                self.logger.info("[预取执行] 调用 repo_map")
                r = await repo_map_tool.execute(repo_path=".")
                if r and getattr(r, "content", None) and r.content:
                    _REPOMAP_CHARS = 4500
                    parts.append("【代码地图】仅作参考\n" + ((r.content[:_REPOMAP_CHARS] + "…") if len(r.content) > _REPOMAP_CHARS else r.content))
                    self.logger.info(f"[预取执行] repo_map 完成，内容长度: {len(r.content)}")
                
                if parts:
                    context["project_understanding_block"] = header + "\n\n".join(parts)
                    self.logger.info(f"[预取完成] 已注入 project_understanding_block，总长度: {len(context['project_understanding_block'])}")
                else:
                    self.logger.warning("[预取完成] 没有获取到任何内容")
        
        except Exception as e:
            self.logger.warning(f"[预取失败] {e}", exc_info=True)
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        验证结果是否有效
        
        验证规则：
        1. success标志为True
        2. content不为空
        3. 没有error
        """
        if not result.get('success'):
            self.logger.debug("验证失败: success=False")
            return False
        
        if not result.get('content'):
            self.logger.debug("验证失败: content为空")
            return False
        
        if result.get('error'):
            self.logger.debug(f"验证失败: 有错误 - {result['error']}")
            return False
        
        return True
    
    def _prepare_prompt_source(self, skill: 'SkillConfig') -> Dict[str, Any]:
        """准备prompt来源配置"""
        if skill.prompt:
            if isinstance(skill.prompt, dict):
                return skill.prompt
            if isinstance(skill.prompt, str):
                return {'file': skill.prompt}
        
        return {'use_agent_default': True}
