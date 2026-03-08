"""
意图分类（在智能体循环前统一做一次，宽泛可复用）

用于：了解项目预取、按问检索预取、后续路由等。
一次 LLM 调用返回多意图标签，避免各场景各自写死触发词或单独调用。

「了解项目」预取判定逻辑（统一入口 should_prefetch_project_understanding）：
  1. skill 配了 project_understanding_use_intent=true → 先调 LLM 意图；命中 understand_project 则预取。
  2. 否则用 skill 的 project_understanding_triggers（chat-assistant 有默认 triggers）做关键词匹配。
  3. 无论 1 还是 2，若未命中都会再走「关键词兜底」：用户输入含任一 PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS 仍预取。
  4. 最终 need_prefetch=True 且三个工具都存在时，编排器里调 discover_project_docs + get_repo_structure + repo_map，拼成 project_understanding_block 注入 context。
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)

# 关键词兜底：意图/触发词未命中时，用户输入含任一词仍视为「想了解项目」（一处维护，react/multi_agent 共用）
# 🆕 使用更灵活的关键词，支持部分匹配
PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS = (
    "架构", "项目架构", "看看项目", "介绍", "项目是干啥",
    "理解", "了解", "当前项目", "介绍一下", "项目介绍",
    "对比", "分析", "优劣势", "优势", "劣势",  # 🆕 添加对比分析相关词
)

# 默认意图定义：供多场景复用，prompt 中说明含义，模型返回命中的标签
DEFAULT_INTENT_DEFINITIONS = {
    "understand_project": "用户想了解/探索当前项目：理解、理解下、当前项目、项目是啥、介绍、架构、结构、概览、整体、看看、了解一下等",
    "need_code_context": "用户问题涉及代码实现、查某功能/某处逻辑、需要看代码上下文",
    "edit_or_write": "用户明确要改代码、写文件、新增或修改实现",
    "run_test": "用户想运行测试、执行测试、测试代码、验证功能：测试、跑测试、运行测试、test、pytest等",
    "general_chat": "一般对话、问候、无关代码的闲聊",
}


async def classify_intents(
    user_input: str,
    llm_config: Optional[Dict[str, Any]] = None,
    intent_definitions: Optional[Dict[str, str]] = None,
    intent_config: Optional[Dict[str, Any]] = None,  # 🔥 新增：完整的意图配置（包含 keywords）
) -> List[str]:
    """
    对用户输入做一次宽泛意图分类，返回命中的意图标签列表。
    在编排器内、智能体循环前调用一次即可，结果可同时驱动预取、路由等。

    Args:
        user_input: 用户输入
        llm_config: Skill 的 llm 配置（model、temperature 等）
        intent_definitions: 意图 id -> 说明文案；None 用 DEFAULT_INTENT_DEFINITIONS
                           🆕 支持从 Skill 的 intents.yaml 传入自定义定义
        intent_config: 🔥 完整的意图配置（包含 keywords），用于关键词兜底

    Returns:
        命中的意图 id 列表，如 ["understand_project", "need_code_context"]；解析失败返回 []。
    """
    if not (user_input and user_input.strip()):
        return []
    
    # 🆕 优先使用传入的意图定义，兜底到默认定义
    defs = intent_definitions if intent_definitions else DEFAULT_INTENT_DEFINITIONS
    
    if not defs:
        logger.warning("没有可用的意图定义，返回空列表")
        return []
    
    # 🆕 构建更清晰的提示，让LLM从列表中选择
    lines = []
    for intent_id, description in defs.items():
        lines.append(f"- `{intent_id}`: {description}")
    
    defs_text = "\n".join(lines)
    
    # 🆕 提取所有有效的意图ID，用于强约束
    valid_intent_ids = list(defs.keys())
    valid_ids_str = ", ".join([f'"{id}"' for id in valid_intent_ids])
    
    prompt = (
        "根据用户输入，从以下意图中选择1个最匹配的（只选1个）：\n\n"
        f"{defs_text}\n\n"
        "只输出JSON：{\"intents\": [\"意图id\"]}\n\n"
        f"用户输入：{user_input.strip()[:600]}"
    )
    
    try:
        from ..llm import get_client_manager
        from ..llm.base import LLMRequest
        cfg = llm_config or {}
        
        # 🔥 使用小模型做意图识别（快速、便宜、准确）
        # 优先级：配置的小模型 > qwen-turbo > 配置的模型
        intent_model = cfg.get("intent_model") or "qwen-turbo"  # qwen-turbo 是小模型，快速便宜
        
        client_manager = get_client_manager()
        client = client_manager.get_client(model=intent_model)
        request = LLMRequest(
            prompt=prompt,
            model=intent_model,
            temperature=0,  # 确定性输出
            max_tokens=50,  # 意图识别只需要很少的 token
        )
        resp = await client.chat(request)
        raw = (resp.content or "").strip()
        
        # 兼容 ```json ... ``` 或直接 {...}
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        start = raw.find("{")
        if start >= 0:
            raw = raw[start:]
        obj = json.loads(raw)
        intents = obj.get("intents") if isinstance(obj, dict) else []
        
        # 🆕 严格验证：只保留在定义中的意图
        valid_intents = []
        for intent in intents:
            if not isinstance(intent, str):
                continue
            
            # 🆕 严格匹配，不做任何修正
            if intent in defs:
                valid_intents.append(intent)
            else:
                logger.warning(f"⚠️ LLM返回了不存在的意图: '{intent}'，已忽略")
        
        if valid_intents:
            logger.info(f"✅ 意图识别成功: {valid_intents} (模型: {intent_model})")
            return valid_intents
        else:
            logger.info(f"ℹ️ LLM未识别到明确意图，尝试关键词兜底...")
            # 🔥 LLM 识别失败，使用关键词兜底
            if intent_config:
                fallback_intents = _keyword_fallback_intent(user_input.strip(), intent_config)
                if fallback_intents:
                    logger.info(f"✅ 关键词兜底成功: {fallback_intents}")
                    return fallback_intents
            
            logger.info(f"ℹ️ 关键词兜底也未匹配，返回空列表")
            return []
        
    except Exception as e:
        logger.warning(f"意图分类失败: {e}，尝试关键词兜底...")
        # 🔥 异常时也尝试关键词兜底
        if intent_config:
            fallback_intents = _keyword_fallback_intent(user_input.strip(), intent_config)
            if fallback_intents:
                logger.info(f"✅ 关键词兜底成功: {fallback_intents}")
                return fallback_intents
        
        logger.warning("关键词兜底也失败，返回空列表")
        return []


def _keyword_fallback_intent(
    user_input: str,
    intent_config: Dict[str, Any]
) -> List[str]:
    """
    关键词兜底：当 LLM 识别失败时，使用关键词匹配
    
    Args:
        user_input: 用户输入
        intent_config: 完整的意图配置（从 intents.yaml 加载）
    
    Returns:
        匹配的意图列表（按优先级排序，最多返回1个）
    """
    if not intent_config or 'intents' not in intent_config:
        return []
    
    user_input_lower = user_input.lower()
    keyword_matches = []
    
    # 遍历所有意图，查找关键词匹配
    for intent_id, intent_data in intent_config['intents'].items():
        keywords = intent_data.get('keywords', [])
        if not keywords:
            continue
        
        # 检查是否有关键词匹配
        if any(kw.lower() in user_input_lower for kw in keywords):
            priority = intent_data.get('priority', 5)
            keyword_matches.append((intent_id, priority))
            logger.debug(f"关键词匹配: {intent_id} (优先级={priority})")
    
    if not keyword_matches:
        return []
    
    # 按优先级降序排序，取优先级最高的
    keyword_matches.sort(key=lambda x: x[1], reverse=True)
    best_match = keyword_matches[0][0]
    
    return [best_match]


async def should_prefetch_project_understanding(
    skill: Any,
    user_input: str,
    context: Dict[str, Any],
) -> Tuple[bool, List[str], str]:
    """
    是否在智能体循环前做「了解项目」预取（文档+目录结构+repo_map → project_understanding_block）。
    编排器（ReAct / MultiAgent）在 execute 开头统一调此函数，逻辑只在此一处维护。

    返回 (need_prefetch, intents, prefetch_level)。
    
    prefetch_level:
    - "full": 完整预取（文档+结构+地图）- 用于"了解项目"
    - "medium": 中等预取（结构+地图）- 用于"需要代码上下文"
    - "light": 轻量预取（只地图）- 用于"编写/修改代码"
    - "none": 不预取 - 用于"简单寒暄"
    """
    user_input_stripped = (user_input or "").strip()
    if not user_input_stripped:
        logger.debug("用户输入为空，跳过预取")
        return False, [], "none"

    use_intent = getattr(skill, "project_understanding_use_intent", False)
    need = False
    intents: List[str] = []
    prefetch_level = "none"

    if use_intent:
        # 🔥 优化：尝试从 skill 获取完整的意图定义
        # 如果失败，使用默认的 5 个意图定义
        intent_defs = None
        workflows_config = getattr(skill, 'workflows', {})
        
        # 只有在有 workflows 配置且有 source 时才尝试加载
        if workflows_config and workflows_config.get('source'):
            try:
                from .workflow_manager import WorkflowManager
                if hasattr(skill, 'skill_path') and skill.skill_path:
                    skill_config = {
                        'skill_dir': str(skill.skill_path),
                        'workflows': workflows_config
                    }
                    wf_manager = WorkflowManager(skill_config)
                    
                    if wf_manager.intent_config:
                        intent_defs = wf_manager.get_intent_definitions()
                        logger.debug(f"从 skill 加载了 {len(intent_defs)} 个意图定义")
            except Exception as e:
                logger.debug(f"无法加载 skill 的意图定义，使用默认定义: {e}")
        
        # 调用意图识别
        intents = await classify_intents(
            user_input_stripped, 
            getattr(skill, "llm", None),
            intent_definitions=intent_defs,  # 可能是 None（使用默认）或完整定义
            intent_config=wf_manager.intent_config if wf_manager else None  # 🔥 传入完整配置用于关键词兜底
        )
        context["detected_intents"] = intents
        logger.info(f"意图识别结果: {intents}")
        
        # 🆕 根据意图确定预取级别
        if "understand_project" in intents:
            need = True
            prefetch_level = "full"
            logger.info("意图: 了解项目 → 完整预取")
        elif "need_code_context" in intents:
            need = True
            prefetch_level = "medium"
            logger.info("意图: 需要代码上下文 → 中等预取")
        elif "edit_or_write" in intents:
            need = True
            prefetch_level = "light"
            logger.info("意图: 编写/修改代码 → 轻量预取")
        elif "general_chat" in intents:
            need = False
            prefetch_level = "none"
            logger.info("意图: 简单寒暄 → 不预取")
        
        # 兜底：关键词匹配（但排除简单寒暄）
        if not need and any(k in user_input_stripped for k in PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS):
            need = True
            prefetch_level = "full"
            logger.info("关键词兜底触发 → 完整预取")
    else:
        triggers = getattr(skill, "project_understanding_triggers", None) or []
        if not triggers and getattr(skill, "name", "") == "chat-assistant":
            triggers = ["了解", "看看项目", "项目怎么样", "项目是啥", "介绍项目", "这是什么项目"]
        need = bool(triggers and any(k in user_input_stripped.lower() for k in triggers))
        
        if need:
            prefetch_level = "full"
            logger.info("触发词匹配 → 完整预取")
        elif any(k in user_input_stripped for k in PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS):
            need = True
            prefetch_level = "full"
            logger.info("关键词兜底触发 → 完整预取")

    return need, intents, prefetch_level
