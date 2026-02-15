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
from .core.task import get_task_manager, TaskStatus

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
    
    # 获取任务管理器
    task_manager = get_task_manager()
    
    # 创建Hook上下文
    hook_context = HookContext(
        skill_name=skill_name,
        user_input=user_input,
        session_id=session_id,
        metadata=context.copy()
    )
    
    # 获取Hook管理器
    hook_manager = get_hook_manager()
    
    # 创建任务（先不知道编排器）
    task = None
    
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
        
        # 4. 创建任务
        # 智能截断描述：保留开头和结尾，中间用...连接
        task_description = self._truncate_description(user_input, max_length=500)
        
        task = task_manager.create_task(
            description=task_description,
            orchestrator=skill.orchestrator,
            agent=skill.agent,
            metadata={
                'skill_name': skill_name,
                'session_id': session_id,
                'input_length': len(user_input)  # 记录原始长度
            }
        )
        
        # 添加任务ID到context
        context['task_id'] = task.id
        
        # 更新任务状态为运行中
        task_manager.update_status(task.id, TaskStatus.RUNNING)
        
        # 5. 执行
        result = await orchestrator.execute(skill, user_input, context)
        
        # 6. 更新任务状态
        if result.get('success'):
            task_manager.update_status(
                task.id,
                TaskStatus.COMPLETED,
                result=result.get('content', '')
            )
        else:
            task_manager.update_status(
                task.id,
                TaskStatus.FAILED,
                error=result.get('error', 'Unknown error')
            )
        
        # 7. 运行after hooks
        result = await hook_manager.run_after_hooks(hook_context, result)
        
        # 添加任务信息到结果
        result['task_id'] = task.id
        
        return result
    
    except Exception as e:
        logger.error(f"执行Skill失败: {e}", exc_info=True)
        
        # 更新任务状态为失败
        if task:
            task_manager.update_status(
                task.id,
                TaskStatus.FAILED,
                error=str(e)
            )
        
        # 运行error hooks
        error_result = await hook_manager.run_error_hooks(hook_context, e)
        
        if error_result is not None:
            # Hook处理了错误
            if task:
                error_result['task_id'] = task.id
            return error_result
        
        # Hook没有处理，返回默认错误
        return {
            'success': False,
            'content': '',
            'error': str(e),
            'task_id': task.id if task else None
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


def get_task_info(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务信息
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务信息字典，如果任务不存在返回None
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        return None
    
    return task.to_dict()


def get_task_tree(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务树（包含所有子任务）
    
    Args:
        task_id: 根任务ID
    
    Returns:
        任务树字典，如果任务不存在返回None
    """
    task_manager = get_task_manager()
    return task_manager.get_task_tree(task_id)


def get_task_stats() -> Dict[str, Any]:
    """
    获取任务统计信息
    
    Returns:
        统计信息字典
    """
    task_manager = get_task_manager()
    return task_manager.get_stats()


def _truncate_description(text: str, max_length: int = 500) -> str:
    """
    智能截断描述文本
    
    策略：
    - 如果文本长度 <= max_length，直接返回
    - 如果文本长度 > max_length，保留开头和结尾，中间用...连接
    
    Args:
        text: 原始文本
        max_length: 最大长度
    
    Returns:
        截断后的文本
    
    Examples:
        >>> _truncate_description("短文本", 500)
        "短文本"
        
        >>> _truncate_description("很长的文本" * 100, 100)
        "很长的文本很长的文本很长的文本很长...的文本很长的文本很长的文本很长的文本"
    """
    if len(text) <= max_length:
        return text
    
    # 计算开头和结尾的长度
    # 开头占60%，结尾占40%，中间3个字符用于...
    separator = "..."
    separator_len = len(separator)
    available_len = max_length - separator_len
    
    head_len = int(available_len * 0.6)
    tail_len = available_len - head_len
    
    # 截断
    head = text[:head_len]
    tail = text[-tail_len:] if tail_len > 0 else ""
    
    return f"{head}{separator}{tail}"
