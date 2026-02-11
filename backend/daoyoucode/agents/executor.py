"""
Skill执行器

统一的Skill执行入口，集成Hook系统和失败恢复
"""

from typing import Dict, Any, Optional, Callable
import logging

from .core.skill import get_skill_loader
from .core.orchestrator import get_orchestrator
from .core.hook import get_hook_manager, HookContext
from .core.recovery import RecoveryManager, RecoveryConfig

logger = logging.getLogger(__name__)


async def execute_skill(
    skill_name: str,
    user_input: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    recovery_config: Optional[RecoveryConfig] = None,
    validator: Optional[Callable[[Any], bool]] = None,
    analyzer: Optional[Callable[[Any, Optional[Exception]], str]] = None
) -> Dict[str, Any]:
    """
    执行Skill（集成Hook系统和失败恢复）
    
    Args:
        skill_name: Skill名称
        user_input: 用户输入
        session_id: 会话ID
        context: 额外上下文
        recovery_config: 恢复配置（可选）
        validator: 结果验证函数（可选）
        analyzer: 错误分析函数（可选）
    
    Returns:
        执行结果
    """
    if context is None:
        context = {}
    
    if session_id:
        context['session_id'] = session_id
    
    # 如果启用了恢复机制，使用RecoveryManager
    if recovery_config or validator or analyzer:
        recovery_manager = RecoveryManager(recovery_config or RecoveryConfig())
        return await recovery_manager.execute_with_recovery(
            _execute_skill_internal,
            skill_name=skill_name,
            user_input=user_input,
            context=context,
            validator=validator,
            analyzer=analyzer
        )
    
    # 否则直接执行
    return await _execute_skill_internal(skill_name, user_input, context)


async def _execute_skill_internal(
    skill_name: str,
    user_input: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    内部执行函数（被RecoveryManager调用）
    
    Args:
        skill_name: Skill名称
        user_input: 用户输入
        context: 上下文
    
    Returns:
        执行结果
    """
    session_id = context.get('session_id')
    
    # 创建Hook上下文
    hook_context = HookContext(
        skill_name=skill_name,
        user_input=user_input,
        session_id=session_id,
        metadata=context.copy()
    )
    
    # 获取Hook管理器
    hook_manager = get_hook_manager()
    
    try:
        # 1. 运行before hooks
        hook_context = await hook_manager.run_before_hooks(hook_context)
        
        # 更新context（hooks可能修改了）
        context.update(hook_context.metadata)
        
        # 2. 加载Skill
        skill_loader = get_skill_loader()
        skill = skill_loader.get_skill(skill_name)
        
        if not skill:
            error_result = {
                'success': False,
                'content': '',
                'error': f"Skill '{skill_name}' not found"
            }
            # 运行after hooks（即使失败）
            return await hook_manager.run_after_hooks(hook_context, error_result)
        
        logger.info(f"执行Skill: {skill_name}, 编排器: {skill.orchestrator}")
        
        # 3. 获取编排器
        orchestrator = get_orchestrator(skill.orchestrator)
        
        if not orchestrator:
            error_result = {
                'success': False,
                'content': '',
                'error': f"Orchestrator '{skill.orchestrator}' not found"
            }
            return await hook_manager.run_after_hooks(hook_context, error_result)
        
        # 4. 执行
        result = await orchestrator.execute(skill, user_input, context)
        
        # 5. 运行after hooks
        result = await hook_manager.run_after_hooks(hook_context, result)
        
        return result
    
    except Exception as e:
        logger.error(f"执行Skill失败: {e}", exc_info=True)
        
        # 运行error hooks
        error_result = await hook_manager.run_error_hooks(hook_context, e)
        
        if error_result is not None:
            # Hook处理了错误
            return error_result
        
        # Hook没有处理，返回默认错误
        return {
            'success': False,
            'content': '',
            'error': str(e)
        }


def list_skills() -> list:
    """列出所有可用的Skill"""
    skill_loader = get_skill_loader()
    return skill_loader.list_skills()


def get_skill_info(skill_name: str) -> Optional[Dict[str, Any]]:
    """获取Skill详细信息"""
    skill_loader = get_skill_loader()
    skill = skill_loader.get_skill(skill_name)
    
    if not skill:
        return None
    
    return {
        'name': skill.name,
        'version': skill.version,
        'description': skill.description,
        'orchestrator': skill.orchestrator,
        'agent': skill.agent,
        'agents': skill.agents,
        'middleware': skill.middleware
    }
