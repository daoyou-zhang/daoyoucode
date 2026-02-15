"""
超时处理器

在 executor 层面集成超时恢复策略
"""

import logging
from typing import Dict, Any, Optional
import asyncio

from .timeout_recovery import TimeoutRecoveryStrategy, TimeoutRecoveryConfig, get_user_friendly_timeout_message
from ..llm.exceptions import LLMTimeoutError

logger = logging.getLogger(__name__)


async def execute_with_timeout_handling(
    execute_func,
    skill_name: str,
    user_input: str,
    context: Dict[str, Any],
    enable_recovery: bool = True
) -> Dict[str, Any]:
    """
    带超时处理的执行
    
    Args:
        execute_func: 执行函数（可以是 _execute_skill_internal 或包装后的函数）
        skill_name: Skill 名称
        user_input: 用户输入
        context: 上下文
        enable_recovery: 是否启用超时恢复
    
    Returns:
        执行结果
    """
    if not enable_recovery:
        # 不启用恢复，直接执行
        return await execute_func(skill_name, user_input, context)
    
    # 创建超时恢复策略
    recovery_config = TimeoutRecoveryConfig(
        max_retries=3,
        initial_timeout=60.0,
        timeout_multiplier=1.5,
        max_timeout=180.0,
        retry_delay=2.0,
        enable_prompt_simplification=True,
        enable_fallback_model=False  # 暂时禁用备用模型（需要更多配置）
    )
    
    strategy = TimeoutRecoveryStrategy(recovery_config)
    
    try:
        # 包装执行函数，使其符合 timeout_recovery 的签名
        async def wrapped_execute():
            return await execute_func(skill_name, user_input, context)
        
        # 使用超时恢复策略执行
        result = await strategy.execute_with_timeout_recovery(
            wrapped_execute,
            context=context
        )
        
        return result
    
    except LLMTimeoutError as e:
        # 所有重试都失败，返回友好的错误消息
        error_message = get_user_friendly_timeout_message(strategy.retry_count)
        
        logger.error(f"❌ 超时恢复失败: {error_message}")
        
        return {
            'success': False,
            'content': '',
            'error': error_message,
            'timeout_retries': strategy.retry_count
        }
    
    except Exception as e:
        # 其他错误
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        
        return {
            'success': False,
            'content': '',
            'error': str(e)
        }


def should_enable_timeout_recovery(context: Dict[str, Any]) -> bool:
    """
    判断是否应该启用超时恢复
    
    Args:
        context: 上下文
    
    Returns:
        是否启用
    """
    # 可以根据上下文决定是否启用
    # 例如：某些 skill 可能不需要恢复
    
    # 检查是否明确禁用
    if context.get('disable_timeout_recovery'):
        return False
    
    # 检查是否是测试环境
    if context.get('test_mode'):
        return False
    
    # 默认启用
    return True
