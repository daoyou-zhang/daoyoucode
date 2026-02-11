"""
Skill执行器
支持完整模式和追问模式，集成限流、熔断、降级
"""

import asyncio
import time
from typing import Dict, Any, Optional
from jinja2 import Template
import logging

from .loader import SkillConfig
from ..base import LLMRequest, LLMResponse
from ..client_manager import get_client_manager
from ..utils import get_rate_limiter, get_circuit_breaker_manager, get_fallback_strategy
from ..exceptions import SkillExecutionError

logger = logging.getLogger(__name__)


class SkillExecutor:
    """
    Skill执行器
    
    核心功能：
    1. 完整模式执行（首次调用）
    2. 追问模式执行（节省tokens）
    3. 集成限流、熔断、降级
    4. 超时控制
    5. 执行监控
    """
    
    def __init__(self):
        self.client_manager = get_client_manager()
        self.rate_limiter = get_rate_limiter()
        self.circuit_breaker = get_circuit_breaker_manager()
        self.fallback_strategy = get_fallback_strategy()
        
        # 统计信息
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_time': 0.0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_skill': {}
        }
        
        logger.info("Skill执行器已初始化")
    
    async def execute(
        self,
        skill: SkillConfig,
        context: Dict[str, Any],
        user_id: Optional[int] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        执行Skill - 完整模式（首次调用）
        
        Args:
            skill: Skill配置
            context: 上下文数据
            user_id: 用户ID（用于限流）
            timeout: 超时时间
        
        Returns:
            执行结果
        """
        start_time = time.time()
        skill_name = skill.name
        
        # 更新统计
        self.stats['total_executions'] += 1
        if skill_name not in self.stats['by_skill']:
            self.stats['by_skill'][skill_name] = {
                'executions': 0,
                'successes': 0,
                'failures': 0,
                'total_time': 0.0,
                'avg_time': 0.0
            }
        
        self.stats['by_skill'][skill_name]['executions'] += 1
        
        try:
            # 1. 验证输入
            self._validate_inputs(skill, context)
            
            # 2. 渲染Prompt
            prompt = self._render_prompt(skill, context)
            
            # 3. 获取LLM配置
            model = skill.llm.get('model', 'qwen-max')
            temperature = skill.llm.get('temperature', 0.7)
            max_tokens = skill.llm.get('max_tokens', 2000)
            
            # 4. 限流
            await self.rate_limiter.acquire(
                user_id=user_id,
                model=model,
                timeout=timeout
            )
            
            # 5. 通过熔断器和降级策略执行
            async def execute_llm(fallback_model: str) -> LLMResponse:
                """执行LLM调用"""
                client = self.client_manager.get_client(fallback_model)
                
                request = LLMRequest(
                    prompt=prompt,
                    model=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # 通过熔断器执行
                return await self.circuit_breaker.call(
                    fallback_model,
                    client.chat,
                    request
                )
            
            # 带超时和降级的执行
            try:
                async with asyncio.timeout(timeout):
                    response, used_model = await self.fallback_strategy.execute_with_fallback(
                        model,
                        execute_llm
                    )
            except asyncio.TimeoutError:
                raise SkillExecutionError(f"Skill执行超时: {timeout}秒")
            
            # 6. 解析输出
            result = self._parse_output(skill, response.content)
            
            # 7. 后处理
            result = await self._post_process(skill, result, context)
            
            # 8. 添加元数据
            result['_metadata'] = {
                'skill': skill_name,
                'model': used_model,
                'tokens_used': response.tokens_used,
                'cost': response.cost,
                'latency': response.latency,
                'mode': 'full'
            }
            
            # 更新统计
            elapsed = time.time() - start_time
            self.stats['successful_executions'] += 1
            self.stats['total_time'] += elapsed
            self.stats['total_tokens'] += response.tokens_used
            self.stats['total_cost'] += response.cost
            
            self.stats['by_skill'][skill_name]['successes'] += 1
            self.stats['by_skill'][skill_name]['total_time'] += elapsed
            self.stats['by_skill'][skill_name]['avg_time'] = (
                self.stats['by_skill'][skill_name]['total_time'] /
                self.stats['by_skill'][skill_name]['executions']
            )
            
            # 记录使用
            self.client_manager.record_usage(response.tokens_used, response.cost)
            
            logger.info(
                f"Skill执行成功: {skill_name}, "
                f"模型={used_model}, "
                f"耗时={elapsed:.2f}s, "
                f"tokens={response.tokens_used}, "
                f"成本=¥{response.cost:.4f}"
            )
            
            return result
        
        except Exception as e:
            # 更新失败统计
            self.stats['failed_executions'] += 1
            self.stats['by_skill'][skill_name]['failures'] += 1
            
            logger.error(f"Skill执行失败: {skill_name}, 错误: {e}", exc_info=True)
            raise SkillExecutionError(f"Skill执行失败: {e}")
    
    async def execute_followup(
        self,
        skill: SkillConfig,
        context: Dict[str, Any],
        history_context: Dict[str, Any],
        user_id: Optional[int] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        执行Skill - 追问模式（节省tokens）
        
        Args:
            skill: Skill配置
            context: 当前上下文
            history_context: 历史上下文
            user_id: 用户ID
            timeout: 超时时间
        
        Returns:
            执行结果
        """
        start_time = time.time()
        
        # 构建轻量级prompt
        user_message = context.get('user_message', '')
        previous_summary = history_context.get('summary', '之前的对话内容')
        
        prompt = f"""你是{skill.description}。

【之前的对话摘要】
{previous_summary}

【用户追问】
{user_message}

请基于之前的对话上下文，简洁回答用户的追问。保持对话的连贯性。"""
        
        # 获取LLM配置（追问用更快的模型）
        model = skill.llm.get('model', 'qwen-max')
        # 可以降级到更便宜的模型
        if model == 'qwen-max':
            model = 'qwen-plus'
        elif model == 'qwen-plus':
            model = 'qwen-turbo'
        
        temperature = max(0.3, skill.llm.get('temperature', 0.7) - 0.3)
        max_tokens = skill.llm.get('max_tokens', 2000) // 2
        
        # 限流
        await self.rate_limiter.acquire(
            user_id=user_id,
            model=model,
            timeout=timeout
        )
        
        # 执行
        async def execute_llm(fallback_model: str) -> LLMResponse:
            client = self.client_manager.get_client(fallback_model)
            request = LLMRequest(
                prompt=prompt,
                model=fallback_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return await self.circuit_breaker.call(
                fallback_model,
                client.chat,
                request
            )
        
        try:
            async with asyncio.timeout(timeout):
                response, used_model = await self.fallback_strategy.execute_with_fallback(
                    model,
                    execute_llm
                )
        except asyncio.TimeoutError:
            raise SkillExecutionError(f"Skill执行超时: {timeout}秒")
        
        # 简化输出
        result = {
            "response": response.content,
            "_metadata": {
                'skill': skill.name,
                'model': used_model,
                'tokens_used': response.tokens_used,
                'cost': response.cost,
                'latency': response.latency,
                'mode': 'followup'
            }
        }
        
        # 更新统计
        elapsed = time.time() - start_time
        self.stats['total_tokens'] += response.tokens_used
        self.stats['total_cost'] += response.cost
        self.client_manager.record_usage(response.tokens_used, response.cost)
        
        logger.info(
            f"Skill追问执行: {skill.name}, "
            f"模型={used_model}, "
            f"耗时={elapsed:.2f}s, "
            f"tokens={response.tokens_used}"
        )
        
        return result
    
    def _validate_inputs(self, skill: SkillConfig, context: Dict[str, Any]):
        """验证输入参数"""
        for input_def in skill.inputs:
            name = input_def['name']
            required = input_def.get('required', False)
            
            if required and name not in context:
                raise ValueError(f"Required input '{name}' not found")
    
    def _render_prompt(self, skill: SkillConfig, context: Dict[str, Any]) -> str:
        """渲染Prompt模板"""
        try:
            template = Template(skill.prompt_template)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Prompt渲染失败: {e}")
            # 降级：直接使用模板
            return skill.prompt_template
    
    def _parse_output(self, skill: SkillConfig, response: str) -> Dict[str, Any]:
        """解析LLM输出"""
        import json
        
        try:
            # 尝试解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始文本
            return {"response": response}
    
    async def _post_process(
        self,
        skill: SkillConfig,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """后处理"""
        for process in skill.post_process:
            if process == 'validate_output':
                result = self._validate_output(skill, result)
            elif process == 'save_to_database':
                # TODO: 实现数据库保存
                pass
        
        return result
    
    def _validate_output(self, skill: SkillConfig, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证输出格式"""
        for output_def in skill.outputs:
            name = output_def['name']
            output_type = output_def['type']
            
            if name not in result:
                continue
            
            # 验证枚举类型
            if output_type == 'enum':
                values = output_def.get('values', [])
                if result[name] not in values:
                    result[name] = values[0]  # 使用默认值
        
        return result
    
    def get_stats(self, skill_name: Optional[str] = None) -> Dict:
        """获取统计信息"""
        if skill_name:
            return self.stats['by_skill'].get(skill_name, {})
        
        return self.stats


def get_skill_executor() -> SkillExecutor:
    """获取Skill执行器单例"""
    if not hasattr(get_skill_executor, '_instance'):
        get_skill_executor._instance = SkillExecutor()
    return get_skill_executor._instance
