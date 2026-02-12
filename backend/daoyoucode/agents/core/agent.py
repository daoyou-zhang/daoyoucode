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
        
        # 接入记忆模块（单例，不会重复加载）
        from ..memory import get_memory_manager
        self.memory = get_memory_manager()
    
    async def execute(
        self,
        prompt_source: Dict[str, Any],
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
        max_tool_iterations: int = 5
    ) -> AgentResult:
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
        """
        if context is None:
            context = {}
        
        # 提取session_id和user_id
        session_id = context.get('session_id', 'default')
        user_id = context.get('user_id', session_id)
        
        tools_used = []
        
        try:
            # ========== 1. 获取记忆 ==========
            
            # 1.1 对话历史（LLM层记忆）
            history = self.memory.get_conversation_history(session_id, limit=3)
            if history:
                context['conversation_history'] = history
                self.logger.debug(f"加载了 {len(history)} 轮对话历史")
            
            # 1.2 用户偏好（Agent层记忆）
            prefs = self.memory.get_preferences(user_id)
            if prefs:
                context['user_preferences'] = prefs
                self.logger.debug(f"加载了用户偏好: {list(prefs.keys())}")
            
            # 1.3 任务历史（Agent层记忆）
            task_history = self.memory.get_task_history(user_id, limit=5)
            if task_history:
                context['recent_tasks'] = task_history
                self.logger.debug(f"加载了 {len(task_history)} 个最近任务")
            
            # ========== 2. 加载Prompt ==========
            prompt = await self._load_prompt(prompt_source, context)
            
            # ========== 3. 渲染Prompt ==========
            full_prompt = self._render_prompt(prompt, user_input, context)
            
            # ========== 4. 调用LLM ==========
            if tools:
                response, tools_used = await self._call_llm_with_tools(
                    full_prompt,
                    tools,
                    llm_config,
                    max_tool_iterations
                )
            else:
                response = await self._call_llm(full_prompt, llm_config)
            
            # ========== 5. 保存到记忆 ==========
            
            # 5.1 保存对话（LLM层记忆）
            self.memory.add_conversation(
                session_id,
                user_input,
                response,
                metadata={'agent': self.name}
            )
            
            # 5.2 保存任务（Agent层记忆）
            self.memory.add_task(user_id, {
                'agent': self.name,
                'input': user_input[:200],  # 限制长度
                'result': response[:200],   # 限制长度
                'success': True,
                'tools_used': tools_used
            })
            
            # 5.3 学习用户偏好（Agent层记忆）
            # 例如：如果用户经常问Python问题，记住这个偏好
            if 'python' in user_input.lower():
                self.memory.remember_preference(user_id, 'preferred_language', 'python')
            elif 'javascript' in user_input.lower() or 'js' in user_input.lower():
                self.memory.remember_preference(user_id, 'preferred_language', 'javascript')
            
            return AgentResult(
                success=True,
                content=response,
                metadata={'agent': self.name},
                tools_used=tools_used
            )
        
        except Exception as e:
            self.logger.error(f"执行失败: {e}", exc_info=True)
            
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
                error=str(e),
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
    
    async def _call_llm_with_tools(
        self,
        prompt: str,
        tool_names: List[str],
        llm_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 5
    ) -> tuple[str, List[str]]:
        """
        调用LLM并支持工具调用
        
        Args:
            prompt: 提示词
            tool_names: 可用工具名称列表
            llm_config: LLM配置
            max_iterations: 最大迭代次数
        
        Returns:
            (最终响应, 使用的工具列表)
        """
        from ...tools import get_tool_registry
        import json
        
        tool_registry = get_tool_registry()
        tools_used = []
        
        # 获取工具的Function schemas
        function_schemas = tool_registry.get_function_schemas(tool_names)
        
        if not function_schemas:
            # 没有可用工具，直接调用
            response = await self._call_llm(prompt, llm_config)
            return response, []
        
        # 构建消息历史
        messages = [{"role": "user", "content": prompt}]
        
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
                # 没有工具调用，返回最终响应
                return response.get('content', ''), tools_used
            
            # 解析工具调用
            tool_name = function_call['name']
            tool_args = json.loads(function_call['arguments'])
            
            self.logger.info(f"调用工具: {tool_name}, 参数: {tool_args}")
            tools_used.append(tool_name)
            
            # 执行工具
            try:
                tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
                tool_result_str = str(tool_result)
            except Exception as e:
                tool_result_str = f"Error: {str(e)}"
                self.logger.error(f"工具执行失败: {e}")
            
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
        
        # 构建请求（简化版，实际需要支持messages）
        # 这里暂时用最后一条用户消息
        user_message = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_message = msg['content']
                break
        
        request = LLMRequest(
            prompt=user_message,
            model=model,
            temperature=temperature
        )
        
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
