"""
降级策略（Fallback Strategy）
当主模型失败时，自动切换到备用模型
"""

import logging
from typing import Dict, List, Callable, Any, Optional

from ..exceptions import FallbackExhaustedError, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """
    降级策略
    
    定义模型降级链，当主模型失败时自动切换到备用模型
    """
    
    def __init__(self):
        # 模型降级链配置
        self.fallback_chains: Dict[str, List[str]] = {
            # 高端模型降级链
            'gpt-5.2': ['gpt-4o', 'claude-opus-4-5', 'qwen-max'],
            'claude-opus-4-5': ['claude-sonnet-4-5', 'qwen-max'],
            'gemini-3-pro': ['gemini-3-flash', 'qwen-plus'],
            
            # 中端模型降级链
            'qwen-max': ['qwen-plus', 'qwen-turbo'],
            'qwen-plus': ['qwen-turbo', 'deepseek-chat'],
            'deepseek-chat': ['qwen-turbo'],
            
            # 代码专用模型降级链
            'qwen-coder-plus': ['deepseek-coder', 'qwen-plus'],
            'deepseek-coder': ['qwen-coder-plus', 'qwen-plus'],
        }
        
        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'fallback_used': 0,
            'fallback_success': 0,
            'fallback_failed': 0,
            'by_model': {}
        }
        
        logger.info("降级策略已初始化")
    
    def configure_fallback_chain(self, model: str, fallback_models: List[str]):
        """
        配置模型的降级链
        
        Args:
            model: 主模型
            fallback_models: 降级模型列表（按优先级排序）
        """
        self.fallback_chains[model] = fallback_models
        logger.info(f"模型 {model} 降级链: {' -> '.join(fallback_models)}")
    
    def get_fallback_chain(self, model: str) -> List[str]:
        """
        获取模型的降级链
        
        Args:
            model: 模型名称
        
        Returns:
            降级链（包含主模型）
        """
        chain = [model]
        if model in self.fallback_chains:
            chain.extend(self.fallback_chains[model])
        return chain
    
    async def execute_with_fallback(
        self,
        model: str,
        func: Callable,
        *args,
        **kwargs
    ) -> tuple[Any, str]:
        """
        执行函数，失败时自动降级
        
        Args:
            model: 主模型
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            (结果, 实际使用的模型)
        
        Raises:
            FallbackExhaustedError: 所有降级模型都失败
        """
        self.stats['total_attempts'] += 1
        
        # 获取降级链
        fallback_chain = self.get_fallback_chain(model)
        
        last_error = None
        used_fallback = False
        
        for idx, fallback_model in enumerate(fallback_chain):
            try:
                if idx > 0:
                    used_fallback = True
                    self.stats['fallback_used'] += 1
                    logger.warning(
                        f"降级: {model} -> {fallback_model} "
                        f"(第{idx}次降级)"
                    )
                
                # 执行函数（传入当前模型）
                result = await func(fallback_model, *args, **kwargs)
                
                # 成功
                if used_fallback:
                    self.stats['fallback_success'] += 1
                    logger.info(f"降级成功: 使用 {fallback_model}")
                
                # 更新统计
                if model not in self.stats['by_model']:
                    self.stats['by_model'][model] = {
                        'attempts': 0,
                        'fallback_used': 0,
                        'fallback_success': 0
                    }
                
                self.stats['by_model'][model]['attempts'] += 1
                if used_fallback:
                    self.stats['by_model'][model]['fallback_used'] += 1
                    self.stats['by_model'][model]['fallback_success'] += 1
                
                return result, fallback_model
            
            except CircuitBreakerOpenError as e:
                # 熔断器打开，直接跳过
                last_error = e
                logger.warning(f"模型 {fallback_model} 熔断器打开，跳过")
                continue
            
            except Exception as e:
                # 其他错误，记录并继续
                last_error = e
                logger.error(
                    f"模型 {fallback_model} 执行失败: {e}",
                    exc_info=True
                )
                continue
        
        # 所有降级都失败
        self.stats['fallback_failed'] += 1
        
        if model in self.stats['by_model']:
            self.stats['by_model'][model]['fallback_used'] += 1
        
        raise FallbackExhaustedError(
            f"所有降级模型都失败: {' -> '.join(fallback_chain)}\n"
            f"最后错误: {last_error}"
        )
    
    def get_stats(self, model: Optional[str] = None) -> Dict:
        """获取统计信息"""
        if model:
            return self.stats['by_model'].get(model, {})
        
        return {
            'summary': {
                'total_attempts': self.stats['total_attempts'],
                'fallback_used': self.stats['fallback_used'],
                'fallback_success': self.stats['fallback_success'],
                'fallback_failed': self.stats['fallback_failed'],
                'fallback_success_rate': (
                    self.stats['fallback_success'] / self.stats['fallback_used']
                    if self.stats['fallback_used'] > 0 else 0
                )
            },
            'by_model': self.stats['by_model']
        }
    
    def get_fallback_info(self, model: str) -> Dict:
        """获取模型的降级信息"""
        chain = self.get_fallback_chain(model)
        
        return {
            'model': model,
            'has_fallback': len(chain) > 1,
            'fallback_chain': chain,
            'fallback_count': len(chain) - 1
        }


def get_fallback_strategy() -> FallbackStrategy:
    """获取降级策略单例"""
    if not hasattr(get_fallback_strategy, '_instance'):
        get_fallback_strategy._instance = FallbackStrategy()
    return get_fallback_strategy._instance
