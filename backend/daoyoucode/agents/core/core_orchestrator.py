"""
核心编排器 - 统一执行引擎

整合了所有现有功能：
- 意图识别（LLM + 关键词兜底）
- 工作流管理（动态加载、优先级排序）
- 记忆系统（对话历史、用户画像、任务历史）
- 预取机制（分级预取：full/medium/light/none）
- 工具调用管理（权限控制、缓存）
- Prompt 构建（模板化、动态注入）

设计原则：
1. 保留所有现有核心功能
2. 配置驱动，不写死逻辑
3. 单一职责，清晰分层
4. 易于测试和调试
"""

from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CoreOrchestrator:
    """
    核心编排器
    
    职责：
    - 意图识别
    - 工作流加载
    - 预取管理
    - 工具调用
    - 记忆管理
    - Prompt 构建
    """
    
    def __init__(self, skill_config: 'SkillConfig'):
        """
        初始化核心编排器
        
        Args:
            skill_config: Skill 配置对象
        """
        self.skill = skill_config
        self.logger = logging.getLogger(f"orchestrator.{skill_config.name}")
        
        # 初始化工作流管理器
        self._init_workflow_manager()
        
        # 初始化工具注册表
        from ..tools import get_tool_registry
        self.tool_registry = get_tool_registry()
        
        # 初始化记忆管理器
        from ..memory import get_memory_manager
        self.memory = get_memory_manager()
        
        # 🆕 初始化 Prompt 构建器
        from .prompt_builder import PromptBuilder
        self.prompt_builder = PromptBuilder(skill_config)
        
        # 🆕 缓存基础 prompt（避免重复加载）
        self._base_prompt_cache = None
        
        # 🔥 传递 workflow_manager 到 context（供 Agent 使用）
        self._workflow_manager_initialized = True
        
        self.logger.info(f"核心编排器初始化完成: {skill_config.name}")
    
    def _filter_tools(self) -> Optional[List[str]]:
        """
        过滤工具列表，只保留已注册的工具
        
        🔥 核心功能：避免 Skill 配置错误导致运行时崩溃
        
        Returns:
            过滤后的工具列表，如果没有工具则返回 None
        """
        if not self.skill.tools:
            return None
        
        filtered = self.tool_registry.filter_tool_names(self.skill.tools)
        
        if filtered:
            self.logger.info(f"工具过滤: {len(self.skill.tools)} → {len(filtered)}")
            if len(filtered) < len(self.skill.tools):
                missing = set(self.skill.tools) - set(filtered)
                self.logger.warning(f"以下工具未注册，已忽略: {missing}")
        else:
            self.logger.warning("所有配置的工具都未注册")
        
        return filtered
    
    async def _apply_middleware(
        self,
        middleware_name: str,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用中间件
        
        🔥 核心功能：允许在执行前应用中间件（日志、监控、预处理等）
        
        Args:
            middleware_name: 中间件名称
            user_input: 用户输入
            context: 上下文
        
        Returns:
            处理后的上下文
        """
        try:
            # TODO: 实现中间件加载和执行
            self.logger.debug(f"应用中间件: {middleware_name}")
            return context
        except Exception as e:
            self.logger.warning(f"中间件 {middleware_name} 执行失败: {e}")
            return context
    
    def _init_workflow_manager(self):
        """
        初始化工作流管理器
        
        🔥 保留现有逻辑：
        - 从 intents.yaml 加载配置
        - 支持工作流继承（source）
        - 支持 preferred_intents 过滤
        """
        from .workflow_manager import WorkflowManager
        
        # 构建工作流管理器配置
        workflows_config = getattr(self.skill, 'workflows', {})
        
        # 获取 skill_dir
        skill_dir = getattr(self.skill, 'skill_path', None)
        if not skill_dir:
            # 如果没有 skill_path，尝试从 skill_dir 获取
            skill_dir = getattr(self.skill, 'skill_dir', None)
        
        if skill_dir:
            wf_config = {
                'skill_dir': str(skill_dir),
                'workflows': workflows_config
            }
            
            self.workflow_manager = WorkflowManager(wf_config)
            self.logger.info(
                f"工作流管理器初始化: {len(self.workflow_manager.workflows)} 个工作流"
            )
        else:
            self.workflow_manager = None
            self.logger.warning("未找到 skill_dir，工作流管理器未初始化")
    
    async def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行 Skill
        
        完整流程：
        1. 应用中间件
        2. 意图识别（LLM + 关键词兜底）
        3. 预取判断（分级：full/medium/light/none）
        4. 执行预取（文档+结构+地图）
        5. 传递 workflow_manager 到 context
        6. 工具过滤
        7. 调用 Agent 执行（Agent 负责：记忆加载、工作流加载、Prompt 构建、LLM 调用、记忆保存）
        
        Args:
            user_input: 用户输入
            context: 执行上下文
        
        Returns:
            执行结果字典（或生成器，用于流式输出）
        """
        if context is None:
            context = {}
        
        self.logger.info(f"开始执行: {user_input[:100]}...")
        
        # 🔥 Step 0: 应用中间件
        if self.skill.middleware:
            for middleware_name in self.skill.middleware:
                context = await self._apply_middleware(
                    middleware_name,
                    user_input,
                    context
                )
        
        # 🔥 Step 0.5: 追问判断（在意图识别之前）
        session_id = context.get('session_id', 'default')
        user_id = context.get('user_id', 'default')
        is_followup = False
        followup_confidence = 0.0
        
        if session_id != 'default':
            from ..memory import get_memory_manager
            memory = get_memory_manager()
            is_followup, followup_confidence, reason = await memory.is_followup(
                session_id, user_input
            )
            self.logger.debug(f"追问判断: {is_followup} (置信度: {followup_confidence:.2f}, 原因: {reason})")
            context['is_followup'] = is_followup
            context['followup_confidence'] = followup_confidence
        
        # 🔥 Step 1: 意图识别（可以利用追问信息）
        intents, prefetch_level = await self._recognize_intent(user_input, context)
        context['detected_intents'] = intents  # 传递给 Agent
        
        # 🔥 Step 2: 预取（如果需要）
        if prefetch_level != "none":
            await self._prefetch_project_context(prefetch_level, context)
            # 结果存在 context['project_understanding_block']
        
        # 🔥 Step 3: 传递 workflow_manager（不加载工作流内容，由 Agent 加载）
        if self.workflow_manager:
            context['workflow_manager'] = self.workflow_manager
        
        # 🔥 Step 4: 工具过滤（只使用已注册的工具）
        filtered_tools = self._filter_tools()
        
        # 🔥 Step 5: 调用 Agent 执行
        # Agent 负责：
        # - 加载记忆（对话历史、用户偏好、任务历史）
        # - 加载工作流（根据 detected_intents）
        # - 构建完整 Prompt（注入记忆、工作流、项目理解块）
        # - LLM 调用 + 工具执行
        # - 保存记忆（对话、任务、摘要生成）
        result = await self._execute_with_tools(
            filtered_tools,
            user_input,
            context
        )
        
        # 🔥 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            # 流式输出，直接返回生成器
            return result
        
        # 🔥 Step 6: 添加元数据
        result['metadata'] = result.get('metadata', {})
        result['metadata'].update({
            'skill': self.skill.name,
            'orchestrator': 'core',
            'intents': intents,
            'prefetch_level': prefetch_level
        })
        
        return result
    
    async def _recognize_intent(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> tuple[List[str], str]:
        """
        意图识别
        
        🔥 保留现有逻辑：
        - LLM 驱动的意图分类
        - 关键词兜底机制
        - 预取级别判断
        
        Returns:
            (intents, prefetch_level)
        """
        from .intent import should_prefetch_project_understanding
        
        # 调用现有的意图识别逻辑
        need_prefetch, intents, prefetch_level = await should_prefetch_project_understanding(
            self.skill,
            user_input,
            context
        )
        
        self.logger.info(
            f"意图识别: {intents}, 预取级别: {prefetch_level}"
        )
        
        return intents, prefetch_level
    
    async def _prefetch_project_context(
        self,
        prefetch_level: str,
        context: Dict[str, Any]
    ):
        """
        预取项目上下文
        
        🔥 保留现有逻辑：
        - full: 文档+结构+地图
        - medium: 结构+地图
        - light: 只地图
        
        Args:
            prefetch_level: 预取级别
            context: 上下文（会被修改，添加 project_understanding_block）
        """
        # 检查工具是否可用
        has_tools = all(
            self.tool_registry.get_tool(n)
            for n in ("discover_project_docs", "get_repo_structure", "repo_map")
        )
        
        if not has_tools:
            self.logger.warning("预取工具不可用，跳过预取")
            return
        
        self.logger.info(f"开始预取（{prefetch_level}级别）")
        
        try:
            docs_tool = self.tool_registry.get_tool("discover_project_docs")
            struct_tool = self.tool_registry.get_tool("get_repo_structure")
            repo_map_tool = self.tool_registry.get_tool("repo_map")
            
            parts = []
            
            # 🔥 从 skill 读取预取配置
            _DOC_CHARS = getattr(self.skill, 'project_understanding_doc_chars', 3000)
            _STRUCT_CHARS = getattr(self.skill, 'project_understanding_struct_chars', 4000)
            _REPOMAP_CHARS = getattr(self.skill, 'project_understanding_repomap_chars', 10000)
            
            # 如果配置了总字符数上限，按比例分配
            max_total = getattr(self.skill, 'project_understanding_max_chars', None)
            if max_total and max_total > 0:
                _DOC_CHARS = min(_DOC_CHARS, max(500, int(max_total * 0.50)))
                _STRUCT_CHARS = min(_STRUCT_CHARS, max(300, int(max_total * 0.22)))
                _REPOMAP_CHARS = min(_REPOMAP_CHARS, max(300, int(max_total * 0.28)))
            
            if prefetch_level == "full":
                # 完整预取：结构+地图+文档（按重要性排序）
                # 🔥 显示工具调用进度
                from ..ui import get_tool_display
                display = get_tool_display()
                
                # 1. get_repo_structure（先看整体结构）
                display.show_tool_start("get_repo_structure", {"repo_path": ".", "max_depth": 5})
                import time
                start_time = time.time()
                s = await struct_tool.execute(repo_path=".", max_depth=5)
                display.show_success("get_repo_structure", time.time() - start_time)
                
                # 2. repo_map（核心代码和架构）
                display.show_tool_start("repo_map", {"repo_path": ".", "enable_lsp": True})
                start_time = time.time()
                r = await repo_map_tool.execute(repo_path=".")
                display.show_success("repo_map", time.time() - start_time)
                
                # 3. discover_project_docs（背景信息）
                display.show_tool_start("discover_project_docs", {"repo_path": ".", "max_doc_length": _DOC_CHARS})
                start_time = time.time()
                d = await docs_tool.execute(repo_path=".", max_doc_length=_DOC_CHARS)
                display.show_success("discover_project_docs", time.time() - start_time)
                
                # 🔥 详细日志：记录每个工具返回的字符数
                ls = len(getattr(s, "content", None) or "") if s and getattr(s, "content", None) else 0
                lr = len(getattr(r, "content", None) or "") if r and getattr(r, "content", None) else 0
                ld = len(getattr(d, "content", None) or "") if d and getattr(d, "content", None) else 0
                self.logger.info(f"[预取] full级别 struct={ls} repomap={lr} doc={ld} (chars)")
                
                # 🔥 按新顺序添加：结构 → 地图 → 文档
                if s and getattr(s, "content", None) and s.content:
                    content = s.content[:_STRUCT_CHARS]
                    if len(s.content) > _STRUCT_CHARS:
                        content += "…"
                    parts.append(f"【目录结构】\n{content}")
                
                if r and getattr(r, "content", None) and r.content:
                    content = r.content[:_REPOMAP_CHARS]
                    if len(r.content) > _REPOMAP_CHARS:
                        content += "…"
                    parts.append(f"【代码地图】\n{content}")
                
                if d and getattr(d, "content", None) and d.content:
                    content = d.content[:_DOC_CHARS]
                    if len(d.content) > _DOC_CHARS:
                        content += "…"
                    parts.append(f"【项目文档】\n{content}")
            
            elif prefetch_level == "medium":
                # 中等预取：结构+地图
                # 🔥 显示工具调用进度
                from ..ui import get_tool_display
                display = get_tool_display()
                import time
                
                # 1. get_repo_structure
                display.show_tool_start("get_repo_structure", {"repo_path": ".", "max_depth": 3})
                start_time = time.time()
                s = await struct_tool.execute(repo_path=".", max_depth=3)
                display.show_success("get_repo_structure", time.time() - start_time)
                
                # 2. repo_map
                display.show_tool_start("repo_map", {"repo_path": ".", "enable_lsp": True})
                start_time = time.time()
                r = await repo_map_tool.execute(repo_path=".")
                display.show_success("repo_map", time.time() - start_time)
                
                # 🔥 详细日志
                ls = len(getattr(s, "content", None) or "") if s and getattr(s, "content", None) else 0
                lr = len(getattr(r, "content", None) or "") if r and getattr(r, "content", None) else 0
                self.logger.info(f"[预取] medium级别 struct={ls} repomap={lr} (chars)")
                
                # 🔥 安全属性访问
                if s and getattr(s, "content", None) and s.content:
                    content = s.content[:_STRUCT_CHARS]
                    if len(s.content) > _STRUCT_CHARS:
                        content += "…"
                    parts.append(f"【目录结构】\n{content}")
                
                if r and getattr(r, "content", None) and r.content:
                    content = r.content[:_REPOMAP_CHARS]
                    if len(r.content) > _REPOMAP_CHARS:
                        content += "…"
                    parts.append(f"【代码地图】\n{content}")
            
            elif prefetch_level == "light":
                # 轻量预取：只地图
                # 🔥 显示工具调用进度
                from ..ui import get_tool_display
                display = get_tool_display()
                import time
                
                # repo_map
                display.show_tool_start("repo_map", {"repo_path": ".", "enable_lsp": True})
                start_time = time.time()
                r = await repo_map_tool.execute(repo_path=".")
                display.show_success("repo_map", time.time() - start_time)
                
                # 🔥 详细日志
                lr = len(getattr(r, "content", None) or "") if r and getattr(r, "content", None) else 0
                self.logger.info(f"[预取] light级别 repomap={lr} (chars)")
                
                # 🔥 安全属性访问
                if r and getattr(r, "content", None) and r.content:
                    content = r.content[:_REPOMAP_CHARS]
                    if len(r.content) > _REPOMAP_CHARS:
                        content += "…"
                    parts.append(f"【代码地图】\n{content}")
            
            if parts:
                # 从配置读取 header，如果没有则使用默认值
                header = getattr(self.skill, 'project_understanding_header', None) or (
                    "理解项目时，先看【目录结构】了解整体布局，"
                    "再看【代码地图】掌握核心代码和架构，"
                    "最后看【项目文档】补充背景信息。"
                    "用1-2段话概括项目核心，不要逐条罗列。\n\n"
                )
                context["project_understanding_block"] = header + "\n\n".join(parts)
                self.logger.info(
                    f"预取完成（{prefetch_level}级别）: "
                    f"{len(context['project_understanding_block'])} 字符"
                )
                # 🔥 调试：输出前 200 字符
                self.logger.debug(
                    f"project_understanding_block 预览:\n"
                    f"{context['project_understanding_block'][:200]}..."
                )
            else:
                self.logger.warning("[预取] 工具均无有效 content，parts 为空，未注入 block")
        
        except Exception as e:
            self.logger.warning(f"预取失败: {e}", exc_info=True)
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """
        格式化对话历史
        
        ⚠️ 注意：此方法已废弃，由 Agent 处理
        保留是为了向后兼容，实际不会被调用
        """
        lines = []
        for h in history[-5:]:  # 只保留最近 5 轮
            user_msg = h.get('user', '')
            ai_msg = h.get('ai', '')
            lines.append(f"用户: {user_msg}")
            lines.append(f"AI: {ai_msg}")
        return "\n".join(lines)
    
    async def _load_base_prompt(self, force_reload: bool = False) -> str:
        """
        加载基础 Prompt 模板（不渲染，只加载模板内容）
        
        从 skill.yaml 的 prompt_template 配置中加载基础 prompt 模板文件
        
        Args:
            force_reload: 是否强制重新加载（忽略缓存）
        
        Returns:
            模板内容（未渲染）
        """
        # 🔥 使用缓存，避免重复加载
        if not force_reload and self._base_prompt_cache is not None:
            self.logger.debug("使用缓存的基础 Prompt 模板")
            return self._base_prompt_cache
        
        from pathlib import Path
        
        # 检查是否有 prompt_template 配置
        prompt_template = getattr(self.skill, 'prompt_template', None)
        
        if not prompt_template:
            self.logger.warning("未配置 prompt_template，使用空 prompt")
            self._base_prompt_cache = ""
            return ""
        
        # 获取 skill 目录
        skill_dir = getattr(self.skill, 'skill_dir', None)
        if not skill_dir:
            self.logger.warning("skill_dir 未设置，无法加载 prompt")
            self._base_prompt_cache = ""
            return ""
        
        prompts_dir = Path(skill_dir) / 'prompts'
        
        # 加载 base prompt 模板
        base_file = prompt_template.get('base', 'base_template.md')
        base_path = prompts_dir / base_file
        
        if not base_path.exists():
            self.logger.warning(f"基础 prompt 文件不存在: {base_path}")
            self._base_prompt_cache = ""
            return ""
        
        try:
            with open(base_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 🔥 缓存模板内容（不渲染）
            self._base_prompt_cache = template_content
            
            self.logger.info(f"✅ 加载并缓存基础 Prompt 模板: {base_file} ({len(template_content)} 字符)")
            
            return template_content
            
        except Exception as e:
            self.logger.error(f"加载基础 Prompt 失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self._base_prompt_cache = ""
            return ""
    
    async def _execute_with_tools(
        self,
        filtered_tools: Optional[List[str]],
        user_input: str,
        context: Dict[str, Any]
    ):
        """
        执行（带工具调用）
        
        🔥 职责：调用 Agent 执行
        
        Agent 负责：
        - 加载记忆（对话历史、用户偏好、任务历史）
        - 加载工作流（根据 detected_intents）
        - 构建完整 Prompt（注入记忆、工作流、项目理解块）
        - LLM 调用 + 工具执行
        - 保存记忆（对话、任务、摘要生成）
        
        Args:
            filtered_tools: 过滤后的工具列表
            user_input: 用户输入
            context: 上下文（包含 detected_intents, project_understanding_block, workflow_manager）
        
        Returns:
            执行结果（可能是生成器，用于流式输出）
        """
        from .agent import BaseAgent, AgentConfig
        
        # 🔥 加载基础 Prompt（暂时禁用缓存用于调试）
        system_prompt = await self._load_base_prompt(force_reload=True)
        
        # 创建临时 Agent
        agent_config = AgentConfig(
            name=self.skill.name,
            description=self.skill.description,
            model=self.skill.llm.get('model', 'gpt-4'),
            temperature=self.skill.llm.get('temperature', 0.7),
            system_prompt=system_prompt
        )
        
        agent = BaseAgent(agent_config)
        
        # 🔥 增强 context：添加必要的信息
        enhanced_context = {
            **context,
            'agent_name': self.skill.name,
            'agent_role': 'main',
            'prompt_template_config': getattr(self.skill, 'prompt_template', {}),  # 🔥 传递 prompt_template 配置
            'prompt_builder': self.prompt_builder,  # 🆕 传递 PromptBuilder
        }
        
        # 🔥 workflow_manager 已经在 context 中（Step 3 添加的）
        # 🆕 prompt_builder 也在 context 中
        # Agent 会从 context 获取并使用
        
        # 执行
        result = await agent.execute(
            prompt_source={'use_agent_default': True},  # 🔥 使用 Agent 默认 Prompt
            user_input=user_input,
            context=enhanced_context,
            llm_config=self.skill.llm,
            tools=filtered_tools,
            enable_streaming=context.get('enable_streaming', False)  # 🔥 支持流式输出
        )
        
        # 🔥 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            # 流式输出，直接返回生成器
            return result
        
        # 普通结果，转换为字典
        return {
            'success': result.success,
            'content': result.content,
            'error': result.error,
            'tools_used': result.tools_used,
            'tokens_used': result.tokens_used,
            'cost': result.cost
        }
    
