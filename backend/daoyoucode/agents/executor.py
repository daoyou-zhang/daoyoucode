"""
Skill执行器

统一的Skill执行入口，集成Hook系统、失败恢复和超时恢复
"""

from typing import Dict, Any, Optional, Callable
import logging

from .core.skill import get_skill_loader
from .core.orchestrator import get_orchestrator
from .core.hook import get_hook_manager, HookContext
from .core.recovery import RecoveryManager, RecoveryConfig
from .core.task import get_task_manager, TaskStatus
from .core.timeout_handler import execute_with_timeout_handling, should_enable_timeout_recovery

logger = logging.getLogger(__name__)


async def execute_skill(
    skill_name: str,
    user_input: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    recovery_config: Optional[RecoveryConfig] = None,
    validator: Optional[Callable[[Any], bool]] = None,
    analyzer: Optional[Callable[[Any, Optional[Exception]], str]] = None,
    enable_timeout_recovery: Optional[bool] = None
) -> Dict[str, Any]:
    """
    执行Skill（集成Hook系统、失败恢复和超时恢复）
    
    Args:
        skill_name: Skill名称
        user_input: 用户输入
        session_id: 会话ID
        context: 额外上下文
        recovery_config: 恢复配置（可选）
        validator: 结果验证函数（可选）
        analyzer: 错误分析函数（可选）
        enable_timeout_recovery: 是否启用超时恢复（None=自动判断）
    
    Returns:
        执行结果
    """
    if context is None:
        context = {}
    
    if session_id:
        context['session_id'] = session_id
    
    # 判断是否启用超时恢复
    if enable_timeout_recovery is None:
        enable_timeout_recovery = should_enable_timeout_recovery(context)
    
    # 如果启用超时恢复，使用 timeout_handler
    if enable_timeout_recovery:
        logger.info("✅ 启用超时恢复机制")
        
        # 如果同时启用了失败恢复，需要嵌套处理
        if recovery_config or validator or analyzer:
            recovery_manager = RecoveryManager(recovery_config or RecoveryConfig())
            
            async def execute_with_recovery():
                return await recovery_manager.execute_with_recovery(
                    _execute_skill_internal,
                    skill_name=skill_name,
                    user_input=user_input,
                    context=context,
                    validator=validator,
                    analyzer=analyzer
                )
            
            return await execute_with_timeout_handling(
                execute_with_recovery,
                skill_name,
                user_input,
                context,
                enable_recovery=True
            )
        else:
            # 只启用超时恢复
            return await execute_with_timeout_handling(
                _execute_skill_internal,
                skill_name,
                user_input,
                context,
                enable_recovery=True
            )
    
    # 不启用超时恢复
    # 如果启用了失败恢复，使用RecoveryManager
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
    
    # 统一设置工具上下文：优先用完整 ToolContext，避免覆盖 CLI 传入的 subtree_only/cwd（见优化建议 3.1）
    
    from pathlib import Path
    from .tools.registry import get_tool_registry
    from .tools.base import ToolContext

    registry = get_tool_registry()
    working_dir = context.get('working_directory') or context.get('repo')
    if working_dir:
        repo_path = Path(working_dir)
        if not repo_path.is_absolute():
            repo_path = repo_path.resolve()
        # 若 context 中有完整信息，统一用 set_context，保持 subtree_only、cwd 贯穿到底
        if any(context.get(k) is not None for k in ('subtree_only', 'cwd')):
            cwd = context.get('cwd')
            tool_context = ToolContext(
                repo_path=repo_path,
                session_id=session_id,
                subtree_only=context.get('subtree_only', False),
                cwd=Path(cwd).resolve() if cwd else None,
            )
            logger.info(f"设置工具上下文: repo_path={repo_path}, subtree_only={tool_context.subtree_only}")
            registry.set_context(tool_context)
        else:
            logger.info(f"设置工具工作目录: {working_dir}")
            registry.set_working_directory(str(repo_path))
    else:
        logger.warning("No working_directory or repo in context!")
    
    # 指向性（Cursor 同级）：若有焦点文件，预取 repo_map(chat_files=initial_files) 并注入 context
    initial_files = context.get("initial_files") or []
    if initial_files and isinstance(initial_files, list) and len(initial_files) > 0:
        try:
            repo_map_tool = registry.get_tool("repo_map")
            if repo_map_tool:
                res = await repo_map_tool.execute(repo_path=".", chat_files=initial_files)
                if res and getattr(res, "content", None):
                    raw = res.content
                    context["focus_repo_map_content"] = (raw[:6000] + "…") if len(raw) > 6000 else raw
                    logger.info(f"指向性: 已预取 repo_map(chat_files={len(initial_files)} 个文件)")
        except Exception as e:
            logger.warning(f"预取 focus repo_map 失败: {e}")
    
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
        task_description = _truncate_description(user_input, max_length=500)
        
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
        
        # 「了解项目」预取已移至 ReAct 编排器内、智能体循环前：一次意图分类 + 预取，见 orchestrators/react.py
        # 按问检索（Cursor 同级）：若 Skill 含 semantic_code_search 且用户有输入，预取相关代码块并注入 context
        skill_tools = getattr(skill, "tools", None) or []
        if "semantic_code_search" in skill_tools and user_input and user_input.strip():
            
            import time
            start_time = time.time()
            
            try:
                sem_tool = registry.get_tool("semantic_code_search")
                if sem_tool:
                    # 正常执行，不设置超时（首次建立索引可能需要较长时间）
                    res = await sem_tool.execute(query=user_input.strip()[:500], top_k=6, repo_path=".")
                    
                    elapsed = time.time() - start_time
                    logger.info(f"语义代码检索完成，耗时: {elapsed:.2f}秒")
                    
                    if res and getattr(res, "content", None) and res.content:
                        context["semantic_code_chunks"] = (res.content[:5000] + "…") if len(res.content) > 5000 else res.content
                        logger.info("按问检索: 已注入 semantic_code_chunks")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(f"按问检索预取失败（耗时{elapsed:.2f}秒）: {e}")
        
        # 5. 执行
        result = await orchestrator.execute(skill, user_input, context)
        
        # 检查是否返回生成器（流式输出）
        import inspect
        if inspect.isasyncgen(result):
            # 流式输出模式，直接返回生成器
            # 注意：任务状态更新、hooks 等将被跳过（流式模式下不适用）
            logger.info("🌊 Executor: 检测到流式输出，直接返回生成器")
            
            # 包装生成器，在最后添加 task_id
            async def wrap_with_task_id():
                async for event in result:
                    yield event
                    # 如果是最终结果，添加 task_id
                    if event.get('type') == 'result' and 'result' in event:
                        event['result'].metadata['task_id'] = task.id
            
            return wrap_with_task_id()
        
        # 6. 更新任务状态（非流式模式）
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
