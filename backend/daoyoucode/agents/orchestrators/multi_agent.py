"""
多Agent编排器（增强版）

支持多种协作模式的真正多Agent协作
"""

from typing import Dict, Any, Optional, List
import asyncio
import json
from ..core.orchestrator import BaseOrchestrator


class MultiAgentOrchestrator(BaseOrchestrator):
    """
    多Agent编排器（增强版）
    
    支持4种协作模式：
    1. sequential: 顺序执行（每个Agent处理前一个的输出）
    2. parallel: 并行执行（所有Agent同时处理）
    3. debate: 辩论模式（Agent之间讨论）
    4. main_with_helpers: 主Agent + 辅助Agent（默认）
    """
    
    async def execute(
        self,
        skill: 'SkillConfig',
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Skill"""
        if context is None:
            context = {}
        
        self.logger.info(f"多Agent执行Skill: {skill.name}")
        
        # 0. 与 ReAct 一致：是否预取由 intent.should_prefetch_project_understanding 统一判定
        user_input_stripped = (user_input or "").strip()
        if user_input_stripped:
            from ..tools import get_tool_registry
            from ..intent import should_prefetch_project_understanding
            _tool_reg = get_tool_registry()
            need_project_prefetch, intents = await should_prefetch_project_understanding(skill, user_input_stripped, context)
            has_tools = all(_tool_reg.get_tool(n) for n in ("discover_project_docs", "get_repo_structure", "repo_map"))
            self.logger.info("[预取] need_prefetch=%s has_three_tools=%s user_input=%s", need_project_prefetch, has_tools, user_input_stripped[:80] + ("…" if len(user_input_stripped) > 80 else ""))
            if need_project_prefetch and has_tools:
                try:
                    docs_tool = _tool_reg.get_tool("discover_project_docs")
                    struct_tool = _tool_reg.get_tool("get_repo_structure")
                    repo_map_tool = _tool_reg.get_tool("repo_map")
                    d = await docs_tool.execute(repo_path=".", max_doc_length=12000)
                    s = await struct_tool.execute(repo_path=".", max_depth=3)
                    r = await repo_map_tool.execute(repo_path=".")
                    ld = len(getattr(d, "content", None) or "") if d and getattr(d, "content", None) else 0
                    ls = len(getattr(s, "content", None) or "") if s and getattr(s, "content", None) else 0
                    lr = len(getattr(r, "content", None) or "") if r and getattr(r, "content", None) else 0
                    self.logger.info("[预取] 三层结果 doc=%s struct=%s repomap=%s (chars)", ld, ls, lr)
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
                        self.logger.info("已预取了解项目三层结果并注入 context（multi_agent，智能体循环前） block_len=%s", len(context["project_understanding_block"]))
                    else:
                        self.logger.warning("[预取] 三层工具均无有效 content，parts 为空，未注入 block")
                except Exception as e:
                    self.logger.warning("预取了解项目三层失败: %s", e, exc_info=True)
        
        # 1. 应用中间件
        if skill.middleware:
            for middleware_name in skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 2. 只使用已注册的工具名（避免 Skill 配置错误导致不稳定）
        from ..tools import get_tool_registry
        _tool_registry = get_tool_registry()
        skill_tools_filtered = _tool_registry.filter_tool_names(skill.tools if skill.tools else None)
        
        # 3. 获取Agent列表
        agents = self._get_agents_from_skill(skill)
        
        if not agents:
            return {
                'success': False,
                'content': '',
                'error': 'No agents configured'
            }
        
        # 4. 确定协作模式
        mode = getattr(skill, 'collaboration_mode', 'main_with_helpers')
        
        self.logger.info(f"协作模式: {mode}, Agent数量: {len(agents)}")
        
        skill._filtered_tools = skill_tools_filtered
        
        # 5. 根据模式执行（各模式内按 agent_tools 为每个 Agent 选工具，无则用 skill.tools）
        if mode == 'sequential':
            result = await self._execute_sequential(agents, user_input, context, skill)
        elif mode == 'parallel':
            result = await self._execute_parallel(agents, user_input, context, skill)
        elif mode == 'debate':
            result = await self._execute_debate(agents, user_input, context, skill)
        else:
            result = await self._execute_main_with_helpers(agents, user_input, context, skill)
        
        # 5. 添加元数据
        result['metadata'] = result.get('metadata', {})
        result['metadata'].update({
            'skill': skill.name,
            'orchestrator': 'multi_agent',
            'collaboration_mode': mode,
            'agents_count': len(agents),
            'agents_used': [agent.name for agent in agents]
        })
        
        return result
    
    def _get_tools_for_agent(self, skill: 'SkillConfig', agent_name: str):
        """按 Agent 分配工具：若 skill 配置了 agent_tools[agent_name] 则用其，否则用 skill 统一 tools。"""
        from ..tools import get_tool_registry
        registry = get_tool_registry()
        agent_tools = getattr(skill, 'agent_tools', None) or {}
        if agent_name in agent_tools and agent_tools[agent_name]:
            filtered = registry.filter_tool_names(agent_tools[agent_name])
            if filtered:
                return filtered
        return getattr(skill, '_filtered_tools', None) or skill.tools
    
    async def _execute_sequential(
        self,
        agents: List,
        user_input: str,
        context: Dict[str, Any],
        skill: 'SkillConfig'
    ) -> Dict[str, Any]:
        """
        顺序执行模式
        
        每个Agent处理前一个Agent的输出
        """
        self.logger.info("顺序执行模式")
        
        current_input = user_input
        results = []
        
        for i, agent in enumerate(agents):
            self.logger.info(f"执行Agent {i+1}/{len(agents)}: {agent.name}")
            
            result = await agent.execute(
                prompt_source={'use_agent_default': True},
                user_input=current_input,
                context=context,
                llm_config=skill.llm,
                tools=self._get_tools_for_agent(skill, agent.name)
            )
            
            results.append({
                'agent': agent.name,
                'success': result.success,
                'content': result.content,
                'tokens_used': result.tokens_used
            })
            
            # 下一个Agent使用前一个的输出
            if result.success and result.content:
                current_input = result.content
            else:
                # 如果失败，停止执行
                self.logger.warning(f"Agent {agent.name} 执行失败，停止顺序执行")
                break
        
        # 聚合结果
        final_content = results[-1]['content'] if results else ""
        total_tokens = sum(r['tokens_used'] for r in results)
        
        return {
            'success': len(results) > 0 and results[-1]['success'],
            'content': final_content,
            'sequential_results': results,
            'metadata': {
                'total_tokens': total_tokens
            }
        }
    
    async def _execute_parallel(
        self,
        agents: List,
        user_input: str,
        context: Dict[str, Any],
        skill: 'SkillConfig'
    ) -> Dict[str, Any]:
        """
        并行执行模式
        
        所有Agent同时处理相同的输入
        """
        self.logger.info("并行执行模式")
        
        # 并行执行所有Agent（各 Agent 使用 agent_tools 或 skill.tools）
        tasks = [
            agent.execute(
                prompt_source={'use_agent_default': True},
                user_input=user_input,
                context=context,
                llm_config=skill.llm,
                tools=self._get_tools_for_agent(skill, agent.name)
            )
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, (agent, result) in enumerate(zip(agents, results)):
            if isinstance(result, Exception):
                self.logger.error(f"Agent {agent.name} 执行失败: {result}")
                processed_results.append({
                    'agent': agent.name,
                    'success': False,
                    'content': '',
                    'error': str(result)
                })
            else:
                processed_results.append({
                    'agent': agent.name,
                    'success': result.success,
                    'content': result.content,
                    'tokens_used': result.tokens_used
                })
        
        # 聚合结果
        aggregated = await self._aggregate_parallel_results(processed_results)
        
        return {
            'success': any(r['success'] for r in processed_results),
            'content': aggregated,
            'parallel_results': processed_results,
            'metadata': {
                'total_tokens': sum(r.get('tokens_used', 0) for r in processed_results)
            }
        }
    
    async def _execute_debate(
        self,
        agents: List,
        user_input: str,
        context: Dict[str, Any],
        skill: 'SkillConfig',
        rounds: int = 3
    ) -> Dict[str, Any]:
        """
        辩论模式
        
        Agent之间进行多轮讨论（使用共享记忆）
        """
        self.logger.info(f"辩论模式，{rounds}轮")
        
        # 创建共享记忆接口
        session_id = context.get('session_id', 'default')
        agent_names = [agent.name for agent in agents]
        
        from ..memory import get_memory_manager
        memory = get_memory_manager()
        shared_memory = memory.create_shared_memory(session_id, agent_names)
        
        # 添加到context
        context['shared_memory'] = shared_memory
        
        debate_history = []
        
        for round_num in range(rounds):
            self.logger.info(f"辩论第 {round_num + 1}/{rounds} 轮")
            
            round_results = []
            
            for agent in agents:
                # 从共享记忆获取辩论历史
                debate_history = shared_memory.get_shared('debate_history', [])
                
                # 构建辩论上下文
                debate_context = {
                    **context,
                    'round': round_num + 1,
                    'total_rounds': rounds,
                    'debate_history': debate_history
                }
                
                # 构建辩论Prompt
                debate_prompt = self._build_debate_prompt(
                    user_input,
                    agent.name,
                    debate_history,
                    round_num
                )
                
                result = await agent.execute(
                    prompt_source={'inline': debate_prompt},
                    user_input=user_input,
                    context=debate_context,
                    llm_config=skill.llm,
                    tools=self._get_tools_for_agent(skill, agent.name)
                )
                
                opinion = {
                    'agent': agent.name,
                    'opinion': result.content if result.success else ""
                }
                
                round_results.append(opinion)
                
                # 保存到共享记忆
                shared_memory.set_agent_data(
                    agent.name,
                    f'opinion_round_{round_num + 1}',
                    result.content if result.success else ""
                )
            
            # 更新辩论历史到共享记忆
            debate_history.append({
                'round': round_num + 1,
                'opinions': round_results
            })
            shared_memory.set_shared('debate_history', debate_history)
        
        # 综合所有观点
        final_synthesis = await self._synthesize_debate(debate_history, user_input)
        
        return {
            'success': True,
            'content': final_synthesis,
            'debate_history': debate_history,
            'metadata': {
                'rounds': rounds
            }
        }
    
    async def _execute_main_with_helpers(
        self,
        agents: List,
        user_input: str,
        context: Dict[str, Any],
        skill: 'SkillConfig'
    ) -> Dict[str, Any]:
        """
        主Agent + 辅助Agent模式（默认）
        
        第一个Agent是主Agent，其他是辅助Agent
        """
        self.logger.info("主Agent + 辅助Agent模式")
        
        main_agent = agents[0]
        helper_agents = agents[1:] if len(agents) > 1 else []
        
        # 1. 如果有辅助Agent，先并行执行它们
        helper_results = []
        if helper_agents:
            self.logger.info(f"执行 {len(helper_agents)} 个辅助Agent")
            
            helper_tasks = [
                agent.execute(
                    prompt_source={'use_agent_default': True},
                    user_input=user_input,
                    context=context,
                    llm_config=skill.llm,
                    tools=self._get_tools_for_agent(skill, agent.name)
                )
                for agent in helper_agents
            ]
            
            helper_responses = await asyncio.gather(*helper_tasks, return_exceptions=True)
            
            for agent, response in zip(helper_agents, helper_responses):
                if isinstance(response, Exception):
                    self.logger.error(f"辅助Agent {agent.name} 失败: {response}")
                else:
                    helper_results.append({
                        'agent': agent.name,
                        'content': response.content if response.success else ""
                    })
        
        # 2. 执行主Agent（可以看到辅助Agent的结果）
        self.logger.info(f"执行主Agent: {main_agent.name}")
        
        main_context = {
            **context,
            'helper_results': helper_results
        }
        block_len = len(main_context.get("project_understanding_block") or "")
        self.logger.info("[预取] 主Agent 入参 context 含 project_understanding_block=%s (chars)", block_len if block_len else "无")
        
        main_result = await main_agent.execute(
            prompt_source=skill.prompt if skill.prompt else {'use_agent_default': True},
            user_input=user_input,
            context=main_context,
            llm_config=skill.llm,
            tools=self._get_tools_for_agent(skill, main_agent.name)
        )
        
        return {
            'success': main_result.success,
            'content': main_result.content,
            'error': main_result.error,
            'helper_results': helper_results,
            'tools_used': main_result.tools_used,
            'tokens_used': main_result.tokens_used,
            'cost': main_result.cost,
            'metadata': {
                'main_agent': main_agent.name,
                'helper_agents': [a.name for a in helper_agents]
            }
        }
    
    def _build_debate_prompt(
        self,
        user_input: str,
        agent_name: str,
        debate_history: List,
        round_num: int
    ) -> str:
        """构建辩论Prompt"""
        
        prompt_parts = [
            f"你是 {agent_name}，正在参与一个多Agent辩论。",
            f"",
            f"问题: {user_input}",
            f"",
            f"当前是第 {round_num + 1} 轮辩论。"
        ]
        
        # 添加之前的辩论历史
        if debate_history:
            prompt_parts.append("")
            prompt_parts.append("之前的辩论:")
            
            for round_data in debate_history:
                prompt_parts.append(f"\n第 {round_data['round']} 轮:")
                for opinion in round_data['opinions']:
                    prompt_parts.append(f"- {opinion['agent']}: {opinion['opinion'][:200]}...")
        
        prompt_parts.append("")
        prompt_parts.append("请提出你的观点（考虑其他Agent的意见，但保持独立思考）:")
        
        return "\n".join(prompt_parts)
    
    async def _aggregate_parallel_results(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """聚合并行结果"""
        
        sections = []
        
        for result in results:
            if result['success'] and result.get('content'):
                sections.append(f"[{result['agent']}]\n{result['content']}")
        
        if not sections:
            return ""
        
        return "\n\n---\n\n".join(sections)
    
    async def _synthesize_debate(
        self,
        debate_history: List,
        user_input: str
    ) -> str:
        """综合辩论结果"""
        
        # 简化版：提取所有观点
        all_opinions = []
        
        for round_data in debate_history:
            for opinion in round_data['opinions']:
                if opinion.get('opinion'):
                    all_opinions.append(f"{opinion['agent']}: {opinion['opinion']}")
        
        if not all_opinions:
            return "辩论未产生有效结论"
        
        # 组合成最终答案
        synthesis = [
            f"经过 {len(debate_history)} 轮辩论，各Agent的观点如下：",
            "",
            *all_opinions,
            "",
            "综合结论：",
            "（各Agent观点已列出，请根据实际情况综合判断）"
        ]
        
        return "\n".join(synthesis)
    
    def _get_agents_from_skill(self, skill: 'SkillConfig') -> List:
        """从Skill配置获取Agent列表"""
        agents = []
        
        if skill.agents:
            for agent_name in skill.agents:
                agent = self._get_agent(agent_name)
                agents.append(agent)
        elif skill.agent:
            agent = self._get_agent(skill.agent)
            agents.append(agent)
        
        return agents
