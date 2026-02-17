"""
超时恢复策略

专门处理 LLM 请求超时的恢复机制
"""

import logging
from typing import Optional, Dict, Any, Callable
import asyncio
from dataclasses import dataclass

from ..llm.exceptions import LLMTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class TimeoutRecoveryConfig:
    """超时恢复配置"""
    max_retries: int = 3  # 最大重试次数
    initial_timeout: float = 1800.0  # 初始超时时间（秒）- 30分钟，支持多次工具调用和大规模文件操作
    timeout_multiplier: float = 1.2  # 每次重试超时时间倍数（降低倍数，因为基础时间已经很长）
    max_timeout: float = 3600.0  # 最大超时时间（秒）- 1小时
    retry_delay: float = 2.0  # 重试延迟（秒）
    enable_prompt_simplification: bool = True  # 是否启用 prompt 简化
    enable_fallback_model: bool = True  # 是否启用备用模型


class TimeoutRecoveryStrategy:
    """超时恢复策略"""
    
    def __init__(self, config: Optional[TimeoutRecoveryConfig] = None):
        self.config = config or TimeoutRecoveryConfig()
        self.retry_count = 0
        self.current_timeout = self.config.initial_timeout
    
    async def execute_with_timeout_recovery(
        self,
        func: Callable,
        *args,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        带超时恢复的执行
        
        策略：
        1. 第一次：正常执行
        2. 第二次：增加超时时间
        3. 第三次：简化 prompt + 增加超时
        4. 第四次：使用备用模型（如果可用）
        
        Args:
            func: 要执行的函数
            context: 上下文（包含 prompt、model 等）
            *args, **kwargs: 传递给 func 的参数
        
        Returns:
            执行结果
        
        Raises:
            LLMTimeoutError: 所有重试都失败
        """
        last_error = None
        original_prompt = None
        original_model = None
        
        # 保存原始参数
        if context:
            original_prompt = context.get('prompt')
            original_model = context.get('model')
        
        while self.retry_count < self.config.max_retries:
            try:
                attempt = self.retry_count + 1
                logger.info(f"🔄 超时恢复尝试 {attempt}/{self.config.max_retries}")
                
                # 应用恢复策略
                self._apply_recovery_strategy(attempt, context, original_prompt, original_model)
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                logger.info(f"✅ 执行成功（第 {attempt} 次尝试）")
                return result
            
            except LLMTimeoutError as e:
                last_error = e
                self.retry_count += 1
                
                logger.warning(
                    f"⚠️ 超时错误（第 {attempt} 次尝试）: {e}\n"
                    f"   当前超时设置: {self.current_timeout}秒"
                )
                
                if self.retry_count < self.config.max_retries:
                    logger.info(f"⏳ 等待 {self.config.retry_delay} 秒后重试...")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                
                # 重试次数用完
                break
            
            except Exception as e:
                # 非超时错误，直接抛出
                logger.error(f"❌ 非超时错误: {e}")
                raise
        
        # 所有重试都失败
        logger.error(
            f"❌ 超时恢复失败，已重试 {self.config.max_retries} 次\n"
            f"   最后错误: {last_error}"
        )
        
        raise LLMTimeoutError(
            f"请求超时，已重试 {self.config.max_retries} 次仍然失败。"
            f"建议：1) 检查网络连接 2) 简化问题 3) 稍后重试"
        )
    
    def _apply_recovery_strategy(
        self,
        attempt: int,
        context: Optional[Dict[str, Any]],
        original_prompt: Optional[str],
        original_model: Optional[str]
    ):
        """
        应用恢复策略
        
        Args:
            attempt: 当前尝试次数（1-based）
            context: 上下文
            original_prompt: 原始 prompt
            original_model: 原始模型
        """
        if not context:
            return
        
        # 策略1: 增加超时时间（所有重试都应用）
        self.current_timeout = min(
            self.current_timeout * self.config.timeout_multiplier,
            self.config.max_timeout
        )
        context['timeout'] = self.current_timeout
        logger.info(f"📈 增加超时时间到 {self.current_timeout} 秒")
        
        # 策略2: 简化 prompt（第3次及以后）
        if attempt >= 3 and self.config.enable_prompt_simplification and original_prompt:
            simplified_prompt = self._simplify_prompt(original_prompt)
            context['prompt'] = simplified_prompt
            logger.info(f"✂️ 简化 prompt（从 {len(original_prompt)} 字符到 {len(simplified_prompt)} 字符）")
        
        # 策略3: 使用备用模型（第4次）
        if attempt >= 4 and self.config.enable_fallback_model and original_model:
            fallback_model = self._get_fallback_model(original_model)
            if fallback_model:
                context['model'] = fallback_model
                logger.info(f"🔄 切换到备用模型: {fallback_model}")
    
    def _simplify_prompt(self, prompt: str) -> str:
        """
        简化 prompt
        
        策略：
        1. 移除示例（如果有）
        2. 保留核心指令
        3. 移除详细说明
        
        Args:
            prompt: 原始 prompt
        
        Returns:
            简化后的 prompt
        """
        # 简单策略：保留前30%和后30%，移除中间部分
        lines = prompt.split('\n')
        total_lines = len(lines)
        
        if total_lines <= 50:
            # prompt 不长，不需要简化
            return prompt
        
        keep_lines = int(total_lines * 0.3)
        
        simplified_lines = (
            lines[:keep_lines] +
            ["\n[... 为了加快响应，部分详细说明已省略 ...]\n"] +
            lines[-keep_lines:]
        )
        
        return '\n'.join(simplified_lines)
    
    def _get_fallback_model(self, original_model: str) -> Optional[str]:
        """
        获取备用模型
        
        策略：
        - qwen-max → qwen-plus
        - qwen-plus → qwen-turbo
        - gpt-4 → gpt-3.5-turbo
        - deepseek-coder → deepseek-chat
        
        Args:
            original_model: 原始模型
        
        Returns:
            备用模型，如果没有则返回 None
        """
        fallback_map = {
            'qwen-max': 'qwen-plus',
            'qwen-plus': 'qwen-turbo',
            'gpt-4': 'gpt-3.5-turbo',
            'gpt-4-turbo': 'gpt-3.5-turbo',
            'deepseek-coder': 'deepseek-chat',
            'claude-opus': 'claude-sonnet',
        }
        
        return fallback_map.get(original_model)
    
    def reset(self):
        """重置状态"""
        self.retry_count = 0
        self.current_timeout = self.config.initial_timeout


def create_timeout_recovery_wrapper(
    config: Optional[TimeoutRecoveryConfig] = None
) -> Callable:
    """
    创建超时恢复装饰器
    
    Args:
        config: 超时恢复配置
    
    Returns:
        装饰器函数
    
    Example:
        @create_timeout_recovery_wrapper()
        async def call_llm(prompt: str):
            # LLM 调用逻辑
            pass
    """
    strategy = TimeoutRecoveryStrategy(config)
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            return await strategy.execute_with_timeout_recovery(
                func, *args, **kwargs
            )
        return wrapper
    
    return decorator


# 用户友好的错误消息
def get_user_friendly_timeout_message(retry_count: int) -> str:
    """
    获取用户友好的超时错误消息
    
    Args:
        retry_count: 重试次数
    
    Returns:
        用户友好的错误消息
    """
    messages = {
        1: "请求超时了，正在重试...",
        2: "请求仍然超时，增加超时时间后重试...",
        3: "请求持续超时，简化问题后重试...",
    }
    
    if retry_count <= 3:
        return messages.get(retry_count, "请求超时，正在重试...")
    
    return (
        "很抱歉，多次重试后仍然超时。可能的原因：\n"
        "1. 网络连接不稳定\n"
        "2. 问题过于复杂\n"
        "3. LLM 服务繁忙\n\n"
        "建议：\n"
        "- 检查网络连接\n"
        "- 简化问题或分步骤提问\n"
        "- 稍后重试"
    )
