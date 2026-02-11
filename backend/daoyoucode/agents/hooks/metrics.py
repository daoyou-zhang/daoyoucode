"""
性能指标Hook

收集和记录性能指标
"""

from ..core.hook import BaseHook, HookContext
from typing import Dict, Any, Optional
import time


class MetricsHook(BaseHook):
    """性能指标Hook"""
    
    def __init__(self):
        super().__init__("metrics")
        self._start_times: Dict[str, float] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
    
    async def on_before_execute(
        self,
        context: HookContext
    ) -> HookContext:
        """记录开始时间"""
        session_key = f"{context.session_id}_{context.skill_name}"
        self._start_times[session_key] = time.time()
        
        # 在上下文中添加开始时间
        context.metadata['start_time'] = self._start_times[session_key]
        
        return context
    
    async def on_after_execute(
        self,
        context: HookContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算性能指标"""
        session_key = f"{context.session_id}_{context.skill_name}"
        start_time = self._start_times.pop(session_key, None)
        
        if start_time:
            duration = time.time() - start_time
            
            # 添加性能指标到结果
            if 'metrics' not in result:
                result['metrics'] = {}
            
            result['metrics'].update({
                'duration': duration,
                'start_time': start_time,
                'end_time': time.time(),
            })
            
            # 如果有tokens信息，添加成本估算
            if 'tokens_used' in result:
                tokens = result['tokens_used']
                # 简单的成本估算（实际应根据模型定价）
                estimated_cost = self._estimate_cost(tokens)
                result['metrics']['estimated_cost'] = estimated_cost
            
            # 保存指标
            self._metrics[session_key] = result['metrics']
            
            self.logger.info(
                f"性能指标 - Skill: {context.skill_name}, "
                f"耗时: {duration:.2f}s, "
                f"tokens: {result.get('tokens_used', 'N/A')}"
            )
        
        return result
    
    async def on_error(
        self,
        context: HookContext,
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """记录错误指标"""
        session_key = f"{context.session_id}_{context.skill_name}"
        start_time = self._start_times.pop(session_key, None)
        
        if start_time:
            duration = time.time() - start_time
            
            self._metrics[session_key] = {
                'duration': duration,
                'error': str(error),
                'success': False,
            }
        
        return None
    
    def _estimate_cost(self, tokens: Dict[str, int]) -> float:
        """
        估算成本（美元）
        
        简化版本，实际应根据具体模型定价
        """
        # 假设平均价格：输入$0.01/1K tokens，输出$0.03/1K tokens
        input_tokens = tokens.get('input', 0)
        output_tokens = tokens.get('output', 0)
        
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        
        return input_cost + output_cost
    
    def get_metrics(self, session_key: str) -> Optional[Dict[str, Any]]:
        """获取指标"""
        return self._metrics.get(session_key)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标"""
        return self._metrics.copy()
    
    def clear_metrics(self):
        """清空指标"""
        self._metrics.clear()
