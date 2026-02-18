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
PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS = (
    "架构", "理解项目", "项目架构", "了解项目", "看看项目", "介绍", "项目是干啥",
    "理解", "理解下", "当前项目", "介绍一下", "项目介绍", "看看当前项目",
)

# 默认意图定义：供多场景复用，prompt 中说明含义，模型返回命中的标签
DEFAULT_INTENT_DEFINITIONS = {
    "understand_project": "用户想了解/探索当前项目：理解、理解下、当前项目、项目是啥、介绍、架构、结构、概览、整体、看看、了解一下等",
    "need_code_context": "用户问题涉及代码实现、查某功能/某处逻辑、需要看代码上下文",
    "edit_or_write": "用户明确要改代码、写文件、新增或修改实现",
    "general_chat": "一般对话、问候、无关代码的闲聊",
}


async def classify_intents(
    user_input: str,
    llm_config: Optional[Dict[str, Any]] = None,
    intent_definitions: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    对用户输入做一次宽泛意图分类，返回命中的意图标签列表。
    在编排器内、智能体循环前调用一次即可，结果可同时驱动预取、路由等。

    Args:
        user_input: 用户输入
        llm_config: Skill 的 llm 配置（model、temperature 等）
        intent_definitions: 意图 id -> 说明文案；None 用 DEFAULT_INTENT_DEFINITIONS

    Returns:
        命中的意图 id 列表，如 ["understand_project", "need_code_context"]；解析失败返回 []。
    """
    if not (user_input and user_input.strip()):
        return []
    defs = intent_definitions or DEFAULT_INTENT_DEFINITIONS
    lines = [f"- {k}: {v}" for k, v in defs.items()]
    defs_text = "\n".join(lines)
    prompt = (
        "你是一个意图分类器。根据用户输入，判断其意图属于下面哪些类型（可多选）。\n"
        "意图定义：\n"
        f"{defs_text}\n\n"
        "只输出一个 JSON 对象，格式：{\"intents\": [\"意图id1\", \"意图id2\"]}。"
        "仅包含明确命中的意图，不要编造。若都不明显则 {\"intents\": []}。\n\n"
        "用户输入：\n" + (user_input.strip()[:600])
    )
    try:
        from .llm import get_client_manager
        from .llm.base import LLMRequest
        cfg = llm_config or {}
        model = cfg.get("model", "qwen-max")
        client_manager = get_client_manager()
        client = client_manager.get_client(model=model)
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=0,
            max_tokens=120,
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
        return [x for x in intents if isinstance(x, str) and x in defs]
    except Exception as e:
        logger.warning("意图分类失败，返回空列表: %s", e)
        return []


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
        return False, [], "none"

    use_intent = getattr(skill, "project_understanding_use_intent", False)
    need = False
    intents: List[str] = []
    prefetch_level = "none"

    if use_intent:
        intents = await classify_intents(user_input_stripped, getattr(skill, "llm", None))
        context["detected_intents"] = intents
        
        # 🆕 根据意图确定预取级别
        if "understand_project" in intents:
            need = True
            prefetch_level = "full"
        elif "need_code_context" in intents:
            need = True
            prefetch_level = "medium"
        elif "edit_or_write" in intents:
            need = True
            prefetch_level = "light"
        elif "general_chat" in intents:
            need = False
            prefetch_level = "none"
        
        # 兜底：关键词匹配
        if not need and any(k in user_input_stripped for k in PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS):
            need = True
            prefetch_level = "full"
    else:
        triggers = getattr(skill, "project_understanding_triggers", None) or []
        if not triggers and getattr(skill, "name", "") == "chat-assistant":
            triggers = ["了解", "看看项目", "项目怎么样", "项目是啥", "介绍项目", "这是什么项目"]
        need = bool(triggers and any(k in user_input_stripped.lower() for k in triggers))
        
        if need:
            prefetch_level = "full"
        elif any(k in user_input_stripped for k in PROJECT_UNDERSTANDING_FALLBACK_KEYWORDS):
            need = True
            prefetch_level = "full"

    return need, intents, prefetch_level
