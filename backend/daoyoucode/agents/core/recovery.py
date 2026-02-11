"""
失败恢复管理器

借鉴daoyouCodePilot的自动重试和失败分析机制，提供：
- 自动重试（最多N次）
- 结果验证
- 错误分析和修复建议
- 回滚机制
"""

import logging
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


class MaxRetriesExceeded(Exception):
    """超过最大重试次数"""
    
    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error


@dataclass
class RecoveryConfig:
    """恢复配置"""
    max_retries: int = 3
    enable_analysis: bool = True
    enable_rollback: bool = False
    retry_delay: float = 1.0  # 重试延迟（秒）


class RecoveryManager:
    """失败恢复管理器"""
    
    def __init__(self, config: Optional[RecoveryConfig] = None):
        self.config = config or RecoveryConfig()
        self.retry_count = 0
        self.history: List[Dict] = []
    
    async def execute_with_recovery(
        self,
        func: Callable,
        *args,
        validator: Optional[Callable[[Any], bool]] = None,
        analyzer: Optional[Callable[[Any, Optional[Exception]], str]] = None,
        **kwargs
    ) -> Any:
        """
        带恢复机制的执行
        
        Args:
            func: 要执行的函数
            validator: 结果验证函数，返回True表示结果有效
            analyzer: 错误分析函数，返回修复建议
            *args, **kwargs: 传递给func的参数
        
        Returns:
            执行结果
        
        Raises:
            MaxRetriesExceeded: 超过最大重试次数
        """
        last_error = None
        
        while self.retry_count < self.config.max_retries:
            try:
                logger.info(f"执行尝试 {self.retry_count + 1}/{self.config.max_retries}")
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 记录历史
                self.history.append({
                    'attempt': self.retry_count + 1,
                    'success': True,
                    'result': result
                })
                
                # 验证结果
                if validator:
                    is_valid = validator(result)
                    if not is_valid:
                        logger.warning(f"结果验证失败: {result}")
                        
                        # 分析并修复
                        if self.config.enable_analysis and analyzer:
                            fix_instruction = analyzer(result, None)
                            if fix_instruction:
                                logger.info(f"修复建议: {fix_instruction}")
                                # 更新输入
                                if 'user_input' in kwargs:
                                    kwargs['user_input'] = fix_instruction
                                self.retry_count += 1
                                await asyncio.sleep(self.config.retry_delay)
                                continue
                        
                        # 无法修复，返回结果
                        logger.warning("无法生成修复建议，返回当前结果")
                        return result
                
                # 验证通过或无需验证
                logger.info("执行成功")
                return result
            
            except Exception as e:
                last_error = e
                logger.error(f"执行失败 (第{self.retry_count + 1}次): {e}")
                
                # 记录历史
                self.history.append({
                    'attempt': self.retry_count + 1,
                    'success': False,
                    'error': str(e)
                })
                
                # 分析错误
                if self.config.enable_analysis and analyzer:
                    fix_instruction = analyzer(None, e)
                    if fix_instruction:
                        logger.info(f"修复建议: {fix_instruction}")
                        # 更新输入
                        if 'user_input' in kwargs:
                            kwargs['user_input'] = fix_instruction
                        self.retry_count += 1
                        await asyncio.sleep(self.config.retry_delay)
                        continue
                
                # 无法修复，重试
                self.retry_count += 1
                if self.retry_count < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                
                # 重试次数用完
                break
        
        # 重试次数用完
        raise MaxRetriesExceeded(
            f"执行失败，已重试{self.config.max_retries}次",
            last_error=last_error
        )
    
    def reset(self):
        """重置状态"""
        self.retry_count = 0
        self.history.clear()
    
    def get_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.history.copy()


# 常用验证器
def validate_non_empty(result: Any) -> bool:
    """验证结果非空"""
    if isinstance(result, dict):
        return bool(result.get('content') or result.get('response'))
    return bool(result)


def validate_success_flag(result: Any) -> bool:
    """验证success标志"""
    if isinstance(result, dict):
        return result.get('success', False)
    return True


def validate_no_error(result: Any) -> bool:
    """验证无错误"""
    if isinstance(result, dict):
        return 'error' not in result
    return True


# 常用分析器
def simple_analyzer(result: Optional[Any], error: Optional[Exception]) -> str:
    """简单分析器"""
    if error:
        return f"上次执行出错: {error}，请重新尝试"
    
    if result:
        return f"上次结果不符合预期: {result}，请改进"
    
    return ""


async def llm_analyzer(
    result: Optional[Any],
    error: Optional[Exception],
    llm_client = None
) -> str:
    """
    使用LLM分析错误
    
    Args:
        result: 执行结果
        error: 错误信息
        llm_client: LLM客户端
    
    Returns:
        修复建议
    """
    if not llm_client:
        return simple_analyzer(result, error)
    
    # 构建分析Prompt
    if error:
        prompt = f"""分析以下错误并给出修复建议：

错误类型: {type(error).__name__}
错误信息: {str(error)}

请给出具体的修复指令，直接说明如何修复，不要解释。"""
    
    elif result:
        prompt = f"""分析以下执行结果并给出改进建议：

结果: {result}

请给出具体的改进指令，直接说明如何改进，不要解释。"""
    
    else:
        return ""
    
    try:
        # 调用LLM
        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.get('content', '')
    
    except Exception as e:
        logger.error(f"LLM分析失败: {e}")
        return simple_analyzer(result, error)
