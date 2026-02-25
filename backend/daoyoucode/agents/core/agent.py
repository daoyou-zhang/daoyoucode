"""
Agent基类和注册表

Agent是执行任务的专家
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    description: str
    model: str
    temperature: float = 0.7
    system_prompt: str = ""


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    tools_used: list = field(default_factory=list)
    tokens_used: int = 0
    cost: float = 0.0


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"agent.{self.name}")
        
        # 确保工具注册表已初始化（双保险）
        from ..tools import get_tool_registry
        self._tool_registry = get_tool_registry()
        self.logger.debug(f"工具注册表已就绪: {len(self._tool_registry.list_tools())} 个工具")
        
        # 接入记忆模块（单例，不会重复加载）
        from ..memory import get_memory_manager
        self.memory = get_memory_manager()
        
        # 接入工具后处理器
        from ..tools.postprocessor import get_tool_postprocessor
        self.tool_postprocessor = get_tool_postprocessor()
        self.logger.debug("工具后处理器已就绪")
        
        # 用户画像缓存（按需加载，避免每轮都读取）
        self._user_profile_cache: Dict[str, Dict[str, Any]] = {}
        
        # 用户画像检查时间缓存（避免频繁检查）
        # 格式：{user_id: last_check_timestamp}
        self._profile_check_cache: Dict[str, float] = {}
    
    def get_user_profile(self, user_id: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取用户画像（带缓存）
        
        Args:
            user_id: 用户ID
            force_reload: 是否强制重新加载
        
        Returns:
            用户画像字典，如果不存在返回None
        """
        if force_reload or user_id not in self._user_profile_cache:
            profile = self.memory.long_term_memory.get_user_profile(user_id)
            if profile:
                self._user_profile_cache[user_id] = profile
                self.logger.debug(f"加载用户画像: {user_id}")
        
        return self._user_profile_cache.get(user_id)
    
    async def _check_and_update_profile(self, user_id: str, session_id: str):
        """
        检查并更新用户画像（带时间窗口优化）
        
        优化策略：
        - 1小时内只检查一次，避免频繁的文件I/O和计算
        - 减少90%的不必要检查
        
        Args:
            user_id: 用户ID
            session_id: 当前会话ID
        """
        import time
        
        try:
            # 检查时间窗口（1小时 = 3600秒）
            CHECK_INTERVAL = 3600
            current_time = time.time()
            last_check = self._profile_check_cache.get(user_id)
            
            if last_check and (current_time - last_check) < CHECK_INTERVAL:
                # 1小时内已经检查过，跳过
                self.logger.debug(
                    f"跳过画像检查: user_id={user_id}, "
                    f"距上次检查 {int(current_time - last_check)}秒"
                )
                return
            
            # 更新检查时间
            self._profile_check_cache[user_id] = current_time
            
            # 获取用户的总对话数
            tasks = self.memory.get_task_history(user_id, limit=1000)
            total_conversations = len(tasks)
            
            # 检查是否需要更新
            should_update = self.memory.long_term_memory.should_update_profile(
                user_id, total_conversations
            )
            
            if should_update:
                self.logger.info(f"🔄 触发用户画像更新: user_id={user_id}, conversations={total_conversations}")
                
                # 异步更新（不阻塞当前请求）
                # 这里简化实现，实际应该放到后台任务队列
                await self._update_user_profile_async(user_id)
        
        except Exception as e:
            self.logger.warning(f"检查用户画像更新失败: {e}")
    
    async def _update_user_profile_async(self, user_id: str):
        """
        异步更新用户画像
        
        Args:
            user_id: 用户ID
        """
        try:
            # 收集用户的所有会话
            all_sessions = self.memory.get_user_sessions(user_id)
            
            if not all_sessions:
                self.logger.warning(f"用户 {user_id} 没有会话记录，跳过画像更新")
                return
            
            # 获取LLM客户端
            from ..llm import get_client_manager
            client_manager = get_client_manager()
            llm_client = client_manager.get_client(self.config.model)
            
            # 构建用户画像
            profile = await self.memory.long_term_memory.build_user_profile(
                user_id=user_id,
                all_sessions=all_sessions,
                llm_client=llm_client
            )
            
            # 清除缓存，下次访问时会重新加载
            if user_id in self._user_profile_cache:
                del self._user_profile_cache[user_id]
            
            self.logger.info(
                f"✅ 用户画像已更新: user_id={user_id}, "
                f"sessions={len(all_sessions)}, "
                f"topics={len(profile.get('common_topics', []))}"
            )
        
        except Exception as e:
            self.logger.error(f"更新用户画像失败: {e}", exc_info=True)
    
    async def execute_stream(
        self,
        prompt_source: Dict[str, Any],
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
        max_tool_iterations: int = 15  # 🆕 增加到 15 次
    ):
        """
        流式执行任务（yield每个token）
        
        注意：流式模式不支持工具调用，如果提供了tools参数会自动降级到普通模式
        
        Args:
            prompt_source: Prompt来源
            user_input: 用户输入
            context: 上下文
            llm_config: LLM配置
            tools: 可用工具列表（流式模式下会被忽略）
            max_tool_iterations: 最大工具调用迭代次数（流式模式下无效）
        
        Yields:
            Dict: 流式事件
                - {'type': 'token', 'content': str} - 文本token
                - {'type': 'metadata', 'data': dict} - 元数据（开始/结束）
                - {'type': 'error', 'error': str} - 错误信息
        """
        if context is None:
            context = {}
        
        # 提取session_id和user_id
        session_id = context.get('session_id', 'default')
        user_id = context.get('user_id')
        if not user_id:
            from ..memory import get_current_user_id
            user_id = get_current_user_id()
        context['user_id'] = user_id
        
        # 流式模式不支持工具调用
        if tools:
            self.logger.warning("流式模式不支持工具调用，自动降级到普通模式")
            result = await self.execute(
                prompt_source, user_input, context, llm_config, tools, max_tool_iterations
            )
            yield {'type': 'token', 'content': result.content}
            yield {'type': 'metadata', 'data': {'success': result.success, 'done': True}}
            return
        
        try:
            # 发送开始事件
            yield {'type': 'metadata', 'data': {'status': 'started'}}
            
            # ========== 1. 获取记忆（智能加载）==========
            is_followup = False
            confidence = 0.0
            if session_id != 'default':
                is_followup, confidence, reason = await self.memory.is_followup(
                    session_id, user_input
                )
            
            memory_context = await self.memory.load_context_smart(
                session_id=session_id,
                user_id=user_id,
                user_input=user_input,
                is_followup=is_followup,
                confidence=confidence
            )
            
            history = memory_context.get('history', [])
            if history:
                context['conversation_history'] = history
            
            summary = memory_context.get('summary')
            if summary:
                context['conversation_summary'] = summary
            
            prefs = self.memory.get_preferences(user_id)
            if prefs:
                context['user_preferences'] = prefs
            
            task_history = self.memory.get_task_history(user_id, limit=5)
            if task_history:
                context['recent_tasks'] = task_history
            
            # ========== 2. 加载和渲染Prompt ==========
            prompt = await self._load_prompt(prompt_source, context)
            full_prompt = self._render_prompt(prompt, user_input, context)
            
            # ========== 3. 流式调用LLM ==========
            response_content = ""
            async for token in self._stream_llm(full_prompt, llm_config):
                response_content += token
                yield {'type': 'token', 'content': token}
            
            # ========== 4. 保存到记忆 ==========
            self.memory.add_conversation(
                session_id,
                user_input,
                response_content,
                metadata={'agent': self.name, 'stream': True},
                user_id=user_id
            )
            
            # 检查是否需要生成摘要
            history_after = self.memory.get_conversation_history(session_id)
            current_round = len(history_after)
            
            if self.memory.long_term_memory.should_generate_summary(session_id, current_round):
                try:
                    from ..llm import get_client_manager
                    client_manager = get_client_manager()
                    llm_client = client_manager.get_client(
                        llm_config.get('model') if llm_config else self.config.model
                    )
                    summary = await self.memory.long_term_memory.generate_summary(
                        session_id, history_after, llm_client
                    )
                except Exception as e:
                    self.logger.warning(f"⚠️ 摘要生成失败: {e}")
            
            # 保存任务
            self.memory.add_task(user_id, {
                'agent': self.name,
                'input': user_input[:200],
                'result': response_content[:200],
                'success': True,
                'stream': True
            })
            
            # 检查是否需要更新用户画像
            await self._check_and_update_profile(user_id, session_id)
            
            # 发送完成事件
            yield {'type': 'metadata', 'data': {'status': 'completed', 'done': True}}
        
        except Exception as e:
            self.logger.error(f"流式执行失败: {e}", exc_info=True)
            
            # 失败也记录到任务历史
            self.memory.add_task(user_id, {
                'agent': self.name,
                'input': user_input[:200],
                'error': str(e)[:200],
                'success': False
            })
            
            yield {'type': 'error', 'error': str(e)}
            yield {'type': 'metadata', 'data': {'status': 'failed', 'done': True}}
    
    async def execute(
        self,
        prompt_source: Dict[str, Any],
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
        max_tool_iterations: int = 15,  # 🆕 增加到 15 次
        enable_streaming: bool = False  # 🆕 是否启用流式输出
    ):
        """
        执行任务
        
        Args:
            prompt_source: Prompt来源
                - {'file': 'path/to/prompt.md'}
                - {'inline': 'prompt text'}
                - {'use_agent_default': True}
            user_input: 用户输入
            context: 上下文
            llm_config: LLM配置
            tools: 可用工具列表（工具名称）
            max_tool_iterations: 最大工具调用迭代次数
            enable_streaming: 是否启用流式输出（最终回复阶段）
        
        Returns:
            如果 enable_streaming=True:
                AsyncGenerator[Dict[str, Any], None] - 流式事件
                    - {'type': 'token', 'content': str} - 文本token
                    - {'type': 'result', 'result': AgentResult} - 最终结果
            否则:
                AgentResult - 执行结果
        """
        if context is None:
            context = {}
        
        # 提取session_id和user_id
        session_id = context.get('session_id', 'default')
        
        # 获取user_id（优先级：context > user_manager > session_id）
        user_id = context.get('user_id')
        if not user_id:
            # 从用户管理器获取
            from ..memory import get_current_user_id
            user_id = get_current_user_id()
        
        # 确保user_id在context中（供后续使用）
        context['user_id'] = user_id
        
        tools_used = []
        
        try:
            # ========== 1. 获取记忆（智能加载）==========
            
            # 1.1 判断是否为追问
            is_followup = False
            confidence = 0.0
            if session_id != 'default':
                is_followup, confidence, reason = await self.memory.is_followup(
                    session_id, user_input
                )
                self.logger.debug(f"追问判断: {is_followup} (置信度: {confidence:.2f}, 原因: {reason})")
            
            # 1.2 智能加载对话历史（LLM层记忆）
            memory_context = await self.memory.load_context_smart(
                session_id=session_id,
                user_id=user_id,
                user_input=user_input,
                is_followup=is_followup,
                confidence=confidence
            )
            
            # 提取加载的历史
            history = memory_context.get('history', [])
            if history:
                context['conversation_history'] = history
                self.logger.info(
                    f"📚 智能加载: 策略={memory_context['strategy']}, "
                    f"历史={len(history)}轮, 成本={memory_context['cost']}, "
                    f"筛选={'是' if memory_context.get('filtered') else '否'}"
                )
            
            # 提取摘要（如果有）
            summary = memory_context.get('summary')
            if summary:
                context['conversation_summary'] = summary
                self.logger.info(f"📝 加载摘要: {len(summary)}字符")
            
            # 1.3 用户偏好（Agent层记忆，轻量级）
            prefs = self.memory.get_preferences(user_id)
            if prefs:
                context['user_preferences'] = prefs
                self.logger.debug(f"加载了用户偏好: {list(prefs.keys())}")
            
            # 1.4 任务历史（Agent层记忆，最近5个）
            task_history = self.memory.get_task_history(user_id, limit=5)
            if task_history:
                context['recent_tasks'] = task_history
                self.logger.debug(f"加载了 {len(task_history)} 个最近任务")
            
            # ========== 2. 加载Prompt ==========
            prompt = await self._load_prompt(prompt_source, context)
            
            # ========== 3. 渲染Prompt ==========
            full_prompt = self._render_prompt(prompt, user_input, context)
            
            # 添加工具使用规则（可配置：context['tool_rules'] 覆盖默认，Skill/编排器可传入）
            if tools:
                default_tool_rules = """⚠️ 工具使用规则（必须遵守）：

1. 路径参数使用 '.' 表示当前工作目录
   - ✅ 正确：repo_map(repo_path=".")
   - ❌ 错误：repo_map(repo_path="./your-repo-path")
   - ❌ 错误：repo_map(repo_path="/path/to/repo")

2. 文件路径：相对**项目根**（当前工作目录即项目根）
   - 本仓库后端代码在 backend/daoyoucode/ 下，编排器在 backend/daoyoucode/agents/orchestrators/
   - ✅ 正确：read_file(file_path="backend/daoyoucode/agents/orchestrators/multi_agent.py")
   - ❌ 错误：read_file(file_path="daoyoucode/orchestrators/multi_agent.py")  （会解析到错误路径）

3. 搜索目录使用 '.' 或省略
   - ✅ 正确：text_search(query="example", directory=".")
   - ❌ 错误：text_search(query="example", directory="./src")

4. 细粒度编辑与验证
   - 可用 apply_patch(diff="...") 提交 unified diff，便于审计和回滚。
   - 编辑后建议调用 run_lint 或 run_test 验证，再根据输出修复。

5. 单文件符号（AST 深度）
   - 已知文件时可调用 get_file_symbols(file_path) 获取类/函数/方法及行号。

6. 不要重复调用
   - 同一轮对话中不要用相同参数重复调用同一工具（如多次 repo_map(repo_path=".")）；若已获得该工具结果，请直接基于结果回答。

记住：当前工作目录=项目根；不要用 daoyoucode/ 作为路径前缀，后端代码在 backend/daoyoucode/ 下。

---

"""
                tool_rules = context.get('tool_rules') or default_tool_rules
                full_prompt = (tool_rules if isinstance(tool_rules, str) else default_tool_rules) + full_prompt
            
            # ========== 4. 调用LLM ==========
            if tools:
                # 构建初始消息（包含历史对话）
                initial_messages = []
                # 历史轮数可配置：context['max_history_rounds']，默认 5
                max_history_rounds = context.get('max_history_rounds', 5)
                if history:
                    # 如果历史超过限制，只保留最近的N轮
                    if len(history) > max_history_rounds:
                        truncated_count = len(history) - max_history_rounds
                        history = history[-max_history_rounds:]
                        self.logger.info(
                            f"📉 工具调用历史截断: 保留最近{max_history_rounds}轮, "
                            f"截断{truncated_count}轮 (节省token)"
                        )
                    
                    for h in history:
                        initial_messages.append({
                            "role": "user",
                            "content": h.get('user', '')
                        })
                        initial_messages.append({
                            "role": "assistant",
                            "content": h.get('ai', '')
                        })
                
                # 添加当前用户输入
                initial_messages.append({
                    "role": "user",
                    "content": full_prompt
                })
                
                result = await self._call_llm_with_tools(
                    initial_messages,  # 传递包含历史的消息列表
                    tools,
                    llm_config,
                    max_tool_iterations,
                    context=context,  # 传递 context
                    history=history,   # 传递 history
                    enable_streaming=enable_streaming  # 🆕 传递流式标志
                )
                
                # 检查是否返回生成器（流式输出）
                import inspect
                if inspect.isasyncgen(result):
                    # 流式输出模式
                    self.logger.info("🌊 进入流式输出模式")
                    
                    async def stream_with_memory():
                        response_content = ""
                        final_tools_used = []
                        
                        # 逐个 yield token
                        async for event in result:
                            if event['type'] == 'token':
                                response_content += event['content']
                                yield event
                            elif event['type'] == 'metadata':
                                final_tools_used = event.get('tools_used', [])
                        
                        # 流式输出完成后，保存到记忆
                        self.memory.add_conversation(
                            session_id,
                            user_input,
                            response_content,
                            metadata={'agent': self.name, 'stream': True},
                            user_id=user_id
                        )
                        
                        # 检查是否需要生成摘要
                        history_after = self.memory.get_conversation_history(session_id)
                        current_round = len(history_after)
                        
                        if self.memory.long_term_memory.should_generate_summary(session_id, current_round):
                            try:
                                from ..llm import get_client_manager
                                client_manager = get_client_manager()
                                llm_client = client_manager.get_client(
                                    llm_config.get('model') if llm_config else self.config.model
                                )
                                summary = await self.memory.long_term_memory.generate_summary(
                                    session_id, history_after, llm_client
                                )
                            except Exception as e:
                                self.logger.warning(f"⚠️ 摘要生成失败: {e}")
                        
                        # 保存任务
                        self.memory.add_task(user_id, {
                            'agent': self.name,
                            'input': user_input[:200],
                            'result': response_content[:200],
                            'success': True,
                            'tools_used': final_tools_used,
                            'stream': True
                        })
                        
                        # 检查是否需要更新用户画像
                        await self._check_and_update_profile(user_id, session_id)
                        
                        # 发送最终结果
                        yield {
                            'type': 'result',
                            'result': AgentResult(
                                success=True,
                                content=response_content,
                                metadata={'agent': self.name, 'stream': True},
                                tools_used=final_tools_used
                            )
                        }
                    
                    return stream_with_memory()
                else:
                    # 非流式模式，result 是 tuple
                    response, tools_used = result
            else:
                response = await self._call_llm(full_prompt, llm_config)
                tools_used = []
                tools_used = []
            
            # ========== 5. 保存到记忆 ==========
            
            # 5.1 保存对话（LLM层记忆）
            self.memory.add_conversation(
                session_id,
                user_input,
                response,
                metadata={'agent': self.name},
                user_id=user_id  # 传递user_id以维护映射
            )
            
            # 5.2 检查是否需要生成摘要
            history_after = self.memory.get_conversation_history(session_id)
            current_round = len(history_after)
            
            if self.memory.long_term_memory.should_generate_summary(session_id, current_round):
                self.logger.info(f"🔄 触发摘要生成: session={session_id}, round={current_round}")
                try:
                    # 获取LLM客户端
                    from ..llm import get_client_manager
                    client_manager = get_client_manager()
                    llm_client = client_manager.get_client(
                        llm_config.get('model') if llm_config else self.config.model
                    )
                    
                    # 生成摘要
                    summary = await self.memory.long_term_memory.generate_summary(
                        session_id, history_after, llm_client
                    )
                    self.logger.info(f"✅ 摘要已生成: {len(summary)}字符")
                except Exception as e:
                    self.logger.warning(f"⚠️ 摘要生成失败: {e}")
            
            # 5.3 保存任务（Agent层记忆）
            self.memory.add_task(user_id, {
                'agent': self.name,
                'input': user_input[:200],  # 限制长度
                'result': response[:200],   # 限制长度
                'success': True,
                'tools_used': tools_used
            })
            
            # 5.4 学习用户偏好（Agent层记忆）
            # 例如：如果用户经常问Python问题，记住这个偏好
            if 'python' in user_input.lower():
                self.memory.remember_preference(user_id, 'preferred_language', 'python')
            elif 'javascript' in user_input.lower() or 'js' in user_input.lower():
                self.memory.remember_preference(user_id, 'preferred_language', 'javascript')
            
            # 5.5 检查是否需要更新用户画像
            await self._check_and_update_profile(user_id, session_id)
            
            return AgentResult(
                success=True,
                content=response,
                metadata={'agent': self.name},
                tools_used=tools_used
            )
        
        except Exception as e:
            self.logger.error(f"执行失败: {e}", exc_info=True)
            
            # 检查是否是超时错误
            from ..llm.exceptions import LLMTimeoutError
            if isinstance(e, LLMTimeoutError):
                # 超时错误，提供友好的错误消息
                from .timeout_recovery import get_user_friendly_timeout_message
                error_message = get_user_friendly_timeout_message(3)  # 假设已重试3次
                
                self.logger.warning(f"⚠️ LLM 请求超时: {error_message}")
            else:
                error_message = str(e)
            
            # 失败也记录到任务历史
            self.memory.add_task(user_id, {
                'agent': self.name,
                'input': user_input[:200],
                'error': str(e)[:200],
                'success': False
            })
            
            return AgentResult(
                success=False,
                content="",
                error=error_message,
                tools_used=tools_used
            )
    
    async def _load_prompt(
        self,
        prompt_source: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """加载Prompt"""
        if 'file' in prompt_source:
            return await self._load_prompt_from_file(prompt_source['file'])
        elif 'inline' in prompt_source:
            return prompt_source['inline']
        elif prompt_source.get('use_agent_default'):
            return self.config.system_prompt
        else:
            raise ValueError(f"Invalid prompt source: {prompt_source}")
    
    async def _load_prompt_from_file(self, file_path: str) -> str:
        """从文件加载Prompt"""
        from pathlib import Path
        
        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_prompt(
        self,
        prompt: str,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """渲染Prompt（支持Jinja2模板）"""
        try:
            from jinja2 import Template
            template = Template(prompt)
            return template.render(user_input=user_input, **context)
        except Exception as e:
            self.logger.warning(f"Prompt渲染失败: {e}")
            return prompt.replace('{{user_input}}', user_input)
    
    async def _call_llm(
        self,
        prompt: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """调用LLM"""
        from ..llm import get_client_manager
        
        client_manager = get_client_manager()
        
        # 合并配置
        model = (llm_config or {}).get('model', self.config.model)
        temperature = (llm_config or {}).get('temperature', self.config.temperature)
        
        # 获取客户端
        client = client_manager.get_client(model=model)
        
        # 构建请求
        from ..llm.base import LLMRequest
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=temperature
        )
        
        # 调用
        llm_response = await client.chat(request)
        
        return llm_response.content
    
    async def _stream_llm(
        self,
        prompt: str,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        流式调用LLM
        
        Args:
            prompt: 提示词
            llm_config: LLM配置
        
        Yields:
            str: 每个token
        """
        from ..llm import get_client_manager
        
        client_manager = get_client_manager()
        
        # 合并配置
        model = (llm_config or {}).get('model', self.config.model)
        temperature = (llm_config or {}).get('temperature', self.config.temperature)
        
        # 获取客户端
        client = client_manager.get_client(model=model)
        
        # 构建请求
        from ..llm.base import LLMRequest
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            stream=True
        )
        
        # 流式调用
        async for token in client.stream_chat(request):
            yield token
    
    async def _call_llm_with_tools(
        self,
        initial_messages: List[Dict[str, Any]],  # 改为接受消息列表
        tool_names: List[str],
        llm_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 15,  # 🆕 增加到 15 次
        context: Optional[Dict[str, Any]] = None,  # 添加 context 参数
        history: Optional[List[Dict[str, Any]]] = None,  # 添加 history 参数
        enable_streaming: bool = True  # 🆕 是否启用流式输出
    ):
        """
        调用LLM并支持工具调用（支持流式输出）
        
        Args:
            initial_messages: 初始消息列表（包含历史对话和当前输入）
            tool_names: 可用工具名称列表
            llm_config: LLM配置
            max_iterations: 最大迭代次数
            context: 执行上下文（用于后处理）
            history: 对话历史（用于后处理）
            enable_streaming: 是否启用流式输出（最终回复阶段）
        
        Returns:
            如果 enable_streaming=True 且最终回复无工具调用:
                AsyncGenerator[Dict[str, Any], None] - 流式事件
                    - {'type': 'token', 'content': str} - 文本token
                    - {'type': 'metadata', 'tools_used': List[str]} - 元数据
            否则:
                tuple[str, List[str]] - (最终响应, 使用的工具列表)
        """
        import json
        import time  # 添加 time 导入
        
        # 使用已初始化的工具注册表
        tool_registry = self._tool_registry
        tools_used = []
        
        # 调试：列出所有可用工具
        available_tools = tool_registry.list_tools()
        self.logger.info(f"可用工具数量: {len(available_tools)}")
        self.logger.debug(f"可用工具列表: {', '.join(sorted(available_tools))}")
        
        # 获取工具的Function schemas
        function_schemas = tool_registry.get_function_schemas(tool_names)
        
        if not function_schemas:
            # 没有可用工具，直接调用
            # 从initial_messages中提取最后一条用户消息
            last_user_message = ""
            for msg in reversed(initial_messages):
                if msg['role'] == 'user':
                    last_user_message = msg['content']
                    break
            response = await self._call_llm(last_user_message, llm_config)
            return response, []
        
        # 使用初始消息作为起点
        messages = initial_messages.copy()
        # 同轮去重：相同 (工具名, 参数) 在本轮已执行过则直接复用结果，避免模型重复调用（如连续 5 次 repo_map）
        same_call_cache = {}
        
        # 工具调用循环
        for iteration in range(max_iterations):
            self.logger.info(f"工具调用迭代 {iteration + 1}/{max_iterations}")
            
            # 调用LLM（带工具）
            response = await self._call_llm_with_functions(
                messages,
                function_schemas,
                llm_config
            )
            
            # 检查是否有function_call
            function_call = response.get('metadata', {}).get('function_call')
            
            if not function_call:
                # 没有工具调用，这是最终回复
                # 如果启用流式且是第一轮（没有工具调用过），使用流式输出
                if enable_streaming and iteration == 0:
                    # 第一轮就没有工具调用，直接流式输出
                    self.logger.info("🌊 使用流式输出（无工具调用）")
                    
                    async def stream_generator():
                        # 提取最后一条用户消息作为 prompt
                        last_user_message = ""
                        for msg in reversed(messages):
                            if msg.get('role') == 'user':
                                last_user_message = msg.get('content', '')
                                break
                        
                        # 流式输出
                        async for token in self._stream_llm(last_user_message, llm_config):
                            yield {'type': 'token', 'content': token}
                        
                        # 发送元数据
                        yield {'type': 'metadata', 'tools_used': tools_used}
                    
                    return stream_generator()
                
                elif enable_streaming and iteration > 0:
                    # 有工具调用后的最终回复
                    # 注意：response 已经包含了 LLM 的回复，但是非流式的
                    # 我们需要将这个回复转换为流式输出
                    self.logger.info(f"🌊 转换为流式输出（工具调用后，迭代{iteration+1}次）")
                    
                    async def stream_generator():
                        # 将已有的 response 内容逐字符 yield
                        content = response.get('content', '')
                        
                        # 模拟流式输出（逐词输出）
                        import re
                        # 按词分割（中文按字，英文按词）
                        tokens = []
                        current = ""
                        for char in content:
                            current += char
                            # 中文字符或空格/标点后输出
                            if ord(char) > 127 or char in ' \n.,!?;:，。！？；：':
                                if current:
                                    tokens.append(current)
                                    current = ""
                        if current:
                            tokens.append(current)
                        
                        # 逐个 yield
                        for token in tokens:
                            yield {'type': 'token', 'content': token}
                        
                        # 发送元数据
                        yield {'type': 'metadata', 'tools_used': tools_used}
                    
                    return stream_generator()
                
                else:
                    # 不启用流式，返回完整响应
                    return response.get('content', ''), tools_used
            
            # 解析工具调用
            tool_name = function_call['name']
            
            # 🆕 安全解析 JSON，处理空字符串和格式错误
            try:
                args_str = function_call['arguments'].strip()
                
                # 尝试提取JSON部分（处理LLM添加额外文本的情况）
                if args_str.startswith('{'):
                    # 找到第一个完整的JSON对象
                    brace_count = 0
                    json_end = -1
                    for i, char in enumerate(args_str):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > 0:
                        args_str = args_str[:json_end]
                
                tool_args = json.loads(args_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ JSON 解析失败: {e}")
                self.logger.error(f"原始内容: '{function_call['arguments']}'")
                
                # 尝试修复常见问题
                args_str = function_call['arguments'].strip()
                
                if not args_str or args_str == '':
                    # 空字符串，使用空字典
                    self.logger.warning("⚠️ Function arguments 为空，使用空字典")
                    tool_args = {}
                else:
                    # 无法修复，跳过这次工具调用
                    self.logger.error(f"⚠️ 无法解析 function arguments，跳过工具调用: {tool_name}")
                    
                    # 添加错误消息到对话历史
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": function_call
                    })
                    messages.append({
                        "role": "function",
                        "name": tool_name,
                        "content": f"Error: 无法解析工具参数。请检查参数格式是否正确。"
                    })
                    
                    # 继续下一次迭代
                    continue
            
            # 同轮去重：若本轮回已用相同参数调用过该工具，直接复用上次结果并提示模型基于结果回答
            try:
                args_key = json.dumps(tool_args, sort_keys=True)
            except Exception:
                args_key = str(tool_args)
            cache_key = (tool_name, args_key)
            if cache_key in same_call_cache:
                self.logger.info(f"同轮去重: {tool_name} 与上次参数相同，复用结果，避免重复执行")
                tools_used.append(tool_name)
                from ..ui import get_tool_display
                display = get_tool_display()
                display.show_tool_start(tool_name, tool_args)
                display.show_success(tool_name, 0)  # 显示完成，避免 UI 悬空
                tool_result_str = same_call_cache[cache_key] + "\n\n[系统提示：上文为本轮回调相同参数的结果，请直接基于该结果回答，不要再次调用同一工具。]"
                messages.append({"role": "assistant", "content": None, "function_call": function_call})
                messages.append({"role": "function", "name": tool_name, "content": tool_result_str})
                continue
            
            self.logger.info(f"调用工具: {tool_name}, 参数: {tool_args}")
            tools_used.append(tool_name)
            
            # 使用美观的UI显示
            from ..ui import get_tool_display
            display = get_tool_display()
            
            # 显示工具开始
            display.show_tool_start(tool_name, tool_args)
            
            # 执行工具（带进度显示）
            start_time = time.time()
            try:
                with display.show_progress(tool_name) as progress:
                    task = progress.add_task(f"正在执行 {tool_name}...", total=100)
                    
                    # 模拟进度
                    progress.update(task, advance=30)
                    tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
                    progress.update(task, advance=70)
                
                duration = time.time() - start_time
                display.show_success(tool_name, duration)
                
                # ========== 智能后处理 ==========
                if tool_result.success:
                    # 提取用户问题（从messages中找最后一条用户消息）
                    user_query = ""
                    for msg in reversed(messages):
                        if msg.get('role') == 'user':
                            user_query = msg.get('content', '')
                            break
                    
                    # 后处理
                    if user_query and context:  # 确保 context 存在
                        tool_result = await self.tool_postprocessor.process(
                            tool_name=tool_name,
                            result=tool_result,
                            user_query=user_query,
                            context={
                                'session_id': context.get('session_id') if context else None,
                                'conversation_history': history if history else [],
                            }
                        )
                
                # 提取实际内容
                if tool_result.success:
                    tool_result_str = str(tool_result.content) if tool_result.content else "工具执行成功，但没有返回内容"
                    same_call_cache[cache_key] = tool_result_str
                    # 显示结果预览（可选）
                    # display.show_result_preview(tool_result_str, max_lines=3)
                else:
                    tool_result_str = f"Error: {tool_result.error}"
                    display.show_warning(tool_name, f"工具返回错误: {tool_result.error}")
            except Exception as e:
                duration = time.time() - start_time
                display.show_error(tool_name, e, duration)
                
                tool_result_str = f"Error: {str(e)}"
                self.logger.error(f"工具执行失败: {e}", exc_info=True)
            
            # 添加到消息历史
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": function_call
            })
            messages.append({
                "role": "function",
                "name": tool_name,
                "content": tool_result_str
            })
        
        # 达到最大迭代次数，返回最后的响应
        self.logger.warning(f"达到最大工具调用迭代次数: {max_iterations}")
        
        if enable_streaming:
            # 流式输出最后的响应
            self.logger.info("🌊 使用流式输出（达到最大迭代次数）")
            
            async def stream_generator():
                from ..llm import get_client_manager
                from ..llm.base import LLMRequest
                
                client_manager = get_client_manager()
                model = (llm_config or {}).get('model', self.config.model)
                temperature = (llm_config or {}).get('temperature', self.config.temperature)
                client = client_manager.get_client(model=model)
                
                request = LLMRequest(
                    prompt="",
                    model=model,
                    temperature=temperature,
                    stream=True
                )
                request.messages = messages
                
                async for token in client.stream_chat(request):
                    yield {'type': 'token', 'content': token}
                
                yield {'type': 'metadata', 'tools_used': tools_used}
            
            return stream_generator()
        else:
            final_response = await self._call_llm_with_functions(
                messages,
                [],  # 不再提供工具
                llm_config
            )
            
            return final_response.get('content', ''), tools_used
    
    async def _call_llm_with_functions(
        self,
        messages: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用LLM（支持Function Calling）
        
        Args:
            messages: 消息历史
            functions: Function schemas
            llm_config: LLM配置
        
        Returns:
            响应字典
        """
        from ..llm import get_client_manager
        from ..llm.base import LLMRequest
        
        client_manager = get_client_manager()
        
        # 合并配置
        model = (llm_config or {}).get('model', self.config.model)
        temperature = (llm_config or {}).get('temperature', self.config.temperature)
        
        # 获取客户端
        client = client_manager.get_client(model=model)
        
        # 构建请求 - 传递完整的消息历史
        request = LLMRequest(
            prompt="",  # 当有messages时，prompt可以为空
            model=model,
            temperature=temperature
        )
        
        # 添加完整的消息历史
        request.messages = messages
        
        # 添加functions
        if functions:
            request.functions = functions
        
        # 调用
        response = await client.chat(request)
        
        return {
            'content': response.content,
            'metadata': response.metadata
        }


class AgentRegistry:
    """Agent注册表"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent):
        """注册Agent"""
        self._agents[agent.name] = agent
        logger.info(f"已注册Agent: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取Agent"""
        return self._agents.get(name)
    
    def list_agents(self) -> list:
        """列出所有Agent"""
        return list(self._agents.keys())


# 全局注册表
_agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """获取Agent注册表"""
    return _agent_registry


def register_agent(agent: BaseAgent):
    """注册Agent"""
    _agent_registry.register(agent)
