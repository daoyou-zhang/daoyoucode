"""
LLM编排器
整合所有组件，提供统一的调用接口
"""

from typing import Dict, Any, Optional, AsyncIterator
import logging

from .skills import get_skill_loader, get_skill_executor
from .context import get_context_manager
from .client_manager import get_client_manager

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    LLM编排器
    
    职责：
    1. 整合所有组件（Skill、上下文、客户端）
    2. 提供统一的调用接口
    3. 自动判断追问，选择执行模式
    4. 管理对话流程
    """
    
    def __init__(self):
        # 初始化组件
        self.skill_loader = get_skill_loader()
        self.skill_executor = get_skill_executor()
        self.context_manager = get_context_manager()
        self.client_manager = get_client_manager()
        
        # 加载所有Skill
        self.skill_loader.load_all_skills()
        
        logger.info(f"LLM编排器已初始化，已加载 {len(self.skill_loader.skills)} 个Skill")
    
    async def execute_skill(
        self,
        skill_name: str,
        user_message: str,
        session_id: str,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        force_full_mode: bool = False
    ) -> Dict[str, Any]:
        """
        执行Skill（自动判断追问）
        
        Args:
            skill_name: Skill名称
            user_message: 用户消息
            session_id: 会话ID
            user_id: 用户ID（用于限流）
            context: 额外上下文
            force_full_mode: 强制使用完整模式
        
        Returns:
            执行结果
        """
        # 1. 获取Skill
        skill = self.skill_loader.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        # 2. 判断是否为追问
        is_followup, confidence, reason = await self.context_manager.is_followup(
            session_id,
            user_message,
            skill_name
        )
        
        logger.info(
            f"追问判断: session={session_id}, "
            f"is_followup={is_followup}, "
            f"confidence={confidence:.2f}, "
            f"reason={reason}"
        )
        
        # 3. 准备上下文
        if context is None:
            context = {}
        
        context['user_message'] = user_message
        
        # 4. 执行Skill
        if is_followup and not force_full_mode:
            # 追问模式：使用轻量级prompt
            history_context = {
                'summary': self.context_manager.get_context_summary(session_id, rounds=3)
            }
            
            result = await self.skill_executor.execute_followup(
                skill,
                context,
                history_context,
                user_id=user_id
            )
        else:
            # 完整模式：使用完整prompt
            result = await self.skill_executor.execute(
                skill,
                context,
                user_id=user_id
            )
        
        # 5. 添加追问判断信息
        result['is_followup'] = is_followup
        result['followup_confidence'] = confidence
        result['followup_reason'] = reason
        
        # 6. 保存到上下文
        await self.context_manager.add_conversation(
            session_id,
            user_message,
            result.get('response', str(result)),
            skill_name=skill_name,
            model=result['_metadata']['model']
        )
        
        return result
    
    async def chat(
        self,
        user_message: str,
        session_id: str,
        model: str = "qwen-turbo",
        user_id: Optional[int] = None,
        temperature: float = 0.8
    ) -> Dict[str, Any]:
        """
        普通对话（不使用Skill）
        
        Args:
            user_message: 用户消息
            session_id: 会话ID
            model: 模型名称
            user_id: 用户ID
            temperature: 温度参数
        
        Returns:
            对话结果
        """
        # 1. 判断是否为追问
        is_followup, confidence, reason = await self.context_manager.is_followup(
            session_id,
            user_message
        )
        
        # 2. 构建prompt
        if is_followup:
            # 包含历史上下文
            prompt = self.context_manager.format_context_for_prompt(
                session_id,
                user_message,
                include_history=True,
                history_limit=3
            )
        else:
            # 不包含历史
            prompt = f"用户: {user_message}\n\n请给出友好、简洁的回复。"
        
        # 3. 调用LLM
        client = self.client_manager.get_client(model)
        
        from .base import LLMRequest
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=1000
        )
        
        response = await client.chat(request)
        
        # 4. 构建结果
        result = {
            'response': response.content,
            'model': model,
            'tokens_used': response.tokens_used,
            'cost': response.cost,
            'latency': response.latency,
            'is_followup': is_followup,
            'followup_confidence': confidence,
            'followup_reason': reason
        }
        
        # 5. 保存到上下文
        await self.context_manager.add_conversation(
            session_id,
            user_message,
            response.content,
            model=model
        )
        
        return result
    
    async def stream_execute_skill(
        self,
        skill_name: str,
        user_message: str,
        session_id: str,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式执行Skill
        
        Args:
            skill_name: Skill名称
            user_message: 用户消息
            session_id: 会话ID
            user_id: 用户ID
            context: 额外上下文
        
        Yields:
            流式响应数据
        """
        try:
            # 1. 获取Skill
            skill = self.skill_loader.get_skill(skill_name)
            if not skill:
                yield {
                    'type': 'error',
                    'content': f"Skill '{skill_name}' not found"
                }
                return
            
            # 2. 判断追问
            is_followup, confidence, reason = await self.context_manager.is_followup(
                session_id,
                user_message,
                skill_name
            )
            
            # 3. 准备上下文
            if context is None:
                context = {}
            
            context['user_message'] = user_message
            
            # 4. 构建prompt
            if is_followup:
                history_summary = self.context_manager.get_context_summary(session_id, rounds=3)
                full_prompt = f"{skill.prompt_template}\n\n【历史对话摘要】\n{history_summary}\n\n【当前问题】\n{user_message}"
            else:
                # 渲染完整prompt
                from jinja2 import Template
                template = Template(skill.prompt_template)
                full_prompt = template.render(**context)
            
            # 5. 流式调用LLM
            model = skill.llm.get('model', 'qwen-max')
            temperature = skill.llm.get('temperature', 0.7)
            
            client = self.client_manager.get_client(model)
            
            full_response = ""
            
            async for chunk in client.stream_chat(
                prompt=full_prompt,
                model=model,
                temperature=temperature
            ):
                if chunk == "[DONE]":
                    break
                
                try:
                    import json
                    data = json.loads(chunk)
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            full_response += content
                            
                            yield {
                                'type': 'token',
                                'content': content,
                                'metadata': {
                                    'skill': skill_name,
                                    'is_followup': is_followup,
                                    'confidence': confidence
                                }
                            }
                except json.JSONDecodeError:
                    continue
            
            # 6. 保存到上下文
            await self.context_manager.add_conversation(
                session_id,
                user_message,
                full_response,
                skill_name=skill_name,
                model=model
            )
            
            # 7. 发送完成信号
            yield {
                'type': 'done',
                'content': full_response,
                'metadata': {
                    'skill': skill_name,
                    'model': model,
                    'is_followup': is_followup,
                    'confidence': confidence,
                    'reason': reason
                }
            }
        
        except Exception as e:
            logger.error(f"流式执行Skill失败: {e}", exc_info=True)
            yield {
                'type': 'error',
                'content': f"执行失败: {str(e)}"
            }
    
    def list_skills(self) -> Dict[str, str]:
        """列出所有可用的Skill"""
        return {
            skill.name: skill.description
            for skill in self.skill_loader.skills.values()
        }
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取Skill详细信息"""
        skill = self.skill_loader.get_skill(skill_name)
        if not skill:
            return None
        
        return {
            'name': skill.name,
            'version': skill.version,
            'description': skill.description,
            'type': skill.skill_type,
            'llm': skill.llm,
            'inputs': skill.inputs,
            'outputs': skill.outputs,
            'triggers': skill.triggers
        }
    
    def search_skills(self, keyword: str) -> list:
        """搜索Skill"""
        results = self.skill_loader.search_skills(keyword)
        return [
            {
                'name': skill.name,
                'description': skill.description,
                'version': skill.version
            }
            for skill in results
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'skills': {
                'total': len(self.skill_loader.skills),
                'loaded': list(self.skill_loader.skills.keys())
            },
            'executor': self.skill_executor.get_stats(),
            'context': self.context_manager.get_stats(),
            'client': self.client_manager.get_stats()
        }
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.context_manager.clear_session(session_id)
        logger.info(f"已清除会话: {session_id}")


def get_orchestrator() -> LLMOrchestrator:
    """获取编排器单例"""
    if not hasattr(get_orchestrator, '_instance'):
        get_orchestrator._instance = LLMOrchestrator()
    return get_orchestrator._instance
