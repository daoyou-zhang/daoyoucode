"""
工作流管理器

根据意图动态加载工作流 Prompt，实现任务特定的指导
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import yaml

logger = logging.getLogger(__name__)


class WorkflowManager:
    """工作流管理器 - 根据意图加载对应的工作流 Prompt"""
    
    def __init__(self, skill_config: Dict[str, Any]):
        """
        初始化工作流管理器
        
        Args:
            skill_config: Skill 配置（包含 skill_dir 和可选的 workflows.source）
        """
        self.skill_config = skill_config
        
        # 获取 skill_dir，如果没有则使用当前目录
        skill_dir = skill_config.get('skill_dir')
        if skill_dir:
            self.skill_dir = Path(skill_dir)
        else:
            # 如果没有 skill_dir，尝试从当前工作目录查找
            self.skill_dir = Path.cwd()
            logger.debug(f"未指定 skill_dir，使用当前目录: {self.skill_dir}")
        
        # 🆕 检查是否从其他 Skill 加载工作流（继承机制）
        workflows_config = skill_config.get('workflows', {})
        workflow_source = workflows_config.get('source')
        
        if workflow_source and workflow_source != 'self':
            # 从其他 Skill 加载工作流
            source_skill_dir = self._get_source_skill_dir(workflow_source)
            if source_skill_dir:
                self.workflow_dir = source_skill_dir
                logger.info(f"🔗 继承工作流: 从 {workflow_source} 加载")
            else:
                # 找不到源 Skill，使用自己的
                self.workflow_dir = self.skill_dir
                logger.warning(f"⚠️ 未找到源 Skill {workflow_source}，使用自己的工作流")
        else:
            # 使用自己的工作流
            self.workflow_dir = self.skill_dir
        
        # 🆕 从 intents.yaml 加载配置
        # intent_config: 完整的意图配置（未过滤）
        # 包含所有意图的定义、描述、关键词、工作流配置等
        self.intent_config = self._load_intent_config()
        
        # 提取工作流映射（向后兼容）
        # workflows: 意图ID到工作流配置的映射 {intent_id: {prompt_file, keywords, priority}}
        # 作用：根据意图快速找到对应的工作流文件
        # 注意：这不是权限控制，而是意图到工作流的索引
        self.workflows = self._extract_workflows()
        
        # 🆕 过滤工作流（如果配置了 preferred_intents）
        # preferred_intents: 辅助 agent 只能使用的意图列表（白名单）
        # 例如：programmer 只能使用 write_code, debug_code 等编程相关的工作流
        # 这是一种能力限制机制，确保每个 agent 专注于自己的职责
        preferred_intents = workflows_config.get('preferred_intents', [])
        if preferred_intents:
            self.workflows = self._filter_workflows(self.workflows, preferred_intents)
            logger.info(f"🎯 过滤工作流: 只保留 {preferred_intents}")
        
        logger.info(f"工作流管理器初始化: {len(self.workflows)} 个工作流")
        if self.workflows:
            logger.debug(f"可用工作流: {list(self.workflows.keys())}")
    
    def _get_source_skill_dir(self, source_skill_name: str) -> Optional[Path]:
        """
        获取源 Skill 的目录
        
        Args:
            source_skill_name: 源 Skill 名称（如 "sisyphus-orchestrator"）
        
        Returns:
            源 Skill 目录路径，如果找不到返回 None
        """
        # 从当前 Skill 目录向上查找 skills 目录
        current = self.skill_dir
        skills_root = None
        
        # 向上查找最多 5 层
        for _ in range(5):
            if current.name == 'skills':
                skills_root = current
                break
            parent = current.parent
            if parent == current:  # 到达根目录
                break
            current = parent
        
        if not skills_root:
            logger.warning(f"未找到 skills 根目录，从 {self.skill_dir} 开始查找")
            return None
        
        # 构建源 Skill 路径
        source_skill_dir = skills_root / source_skill_name
        
        if not source_skill_dir.exists():
            logger.warning(f"源 Skill 目录不存在: {source_skill_dir}")
            return None
        
        return source_skill_dir
    
    def _load_intent_config(self) -> Dict[str, Any]:
        """
        从 intents.yaml 加载意图配置
        
        Returns:
            意图配置字典，如果文件不存在返回空字典
        """
        intents_file = self.workflow_dir / 'intents.yaml'
        
        if not intents_file.exists():
            # 静默失败：对于没有工作流的 Agent（如内置 Agent），这是正常的
            logger.debug(f"意图配置文件不存在: {intents_file}（这对于内置 Agent 是正常的）")
            return {}
        
        try:
            with open(intents_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'intents' not in config:
                logger.warning(f"意图配置文件格式错误: {intents_file}")
                return {}
            
            logger.info(f"✅ 加载意图配置: {len(config['intents'])} 个意图")
            return config
        
        except Exception as e:
            logger.error(f"加载意图配置失败: {e}")
            return {}
    
    def _extract_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        从意图配置中提取工作流映射
        
        Returns:
            工作流映射字典 {intent_id: workflow_config}
        """
        workflows = {}
        
        if not self.intent_config:
            return workflows
        
        intents = self.intent_config.get('intents', {})
        
        for intent_id, intent_data in intents.items():
            workflow = intent_data.get('workflow')
            
            # 跳过没有工作流的意图
            if not workflow or workflow is None:
                continue
            
            # 检查是否启用
            if not workflow.get('enabled', True):
                logger.debug(f"工作流已禁用: {intent_id}")
                continue
            
            # 添加到工作流映射
            workflows[intent_id] = {
                'prompt_file': workflow.get('prompt_file'),
                'keywords': intent_data.get('keywords', []),
                'priority': intent_data.get('priority', 5)
            }
        
        return workflows
    
    def get_intent_definitions(self) -> Dict[str, str]:
        """
        获取意图定义（用于 LLM 分类）
        
        🔥 重要：如果配置了 preferred_intents，只返回这些意图的定义
        这样可以避免 LLM 识别出不支持的意图
        
        Returns:
            意图定义字典 {intent_id: description}
        """
        if not self.intent_config:
            return {}
        
        intents = self.intent_config.get('intents', {})
        definitions = {}
        
        # 🔥 如果有 preferred_intents 过滤，只返回这些意图的定义
        # 这样 LLM 就不会识别出不支持的意图
        allowed_intents = set(self.workflows.keys()) if self.workflows else set(intents.keys())
        
        for intent_id, intent_data in intents.items():
            # 🔥 只返回允许的意图
            if intent_id not in allowed_intents:
                continue
            
            description = intent_data.get('description', '')
            if description:
                definitions[intent_id] = description
        
        return definitions
    
    def get_workflow_prompt(
        self,
        intents: List[str],
        user_input: str = ""
    ) -> Optional[str]:
        """
        根据意图列表获取对应的工作流 Prompt
        
        Args:
            intents: 意图列表，如 ["delete_file", "search_code"]
            user_input: 用户输入（用于关键词兜底）
        
        Returns:
            工作流 Prompt 内容，如果没有匹配则返回 None
        """
        if not intents and not user_input:
            return None
        
        # 1. 优先使用意图匹配（按优先级排序）
        if intents:
            # 收集所有匹配的工作流及其优先级
            matched_workflows = []
            
            for intent in intents:
                workflow_config = self.workflows.get(intent)
                
                if workflow_config:
                    priority = workflow_config.get('priority', 5)
                    matched_workflows.append((intent, workflow_config, priority))
            
            # 按优先级降序排序（优先级高的在前）
            if matched_workflows:
                matched_workflows.sort(key=lambda x: x[2], reverse=True)
                
                # 取优先级最高的工作流
                intent, workflow_config, priority = matched_workflows[0]
                prompt_file = workflow_config.get('prompt_file')
                
                if prompt_file:
                    content = self._load_prompt_file(prompt_file)
                    if content:
                        if len(matched_workflows) > 1:
                            other_intents = [x[0] for x in matched_workflows[1:]]
                            logger.info(
                                f"✅ 多意图冲突，选择优先级最高的: {intent} (优先级={priority})，"
                                f"忽略: {other_intents}"
                            )
                        else:
                            logger.info(f"✅ 加载工作流: {intent} -> {prompt_file}")
                        return content
        
        # 没有匹配的工作流
        logger.debug(f"未找到匹配的工作流: intents={intents}")
        return None
    
    def _filter_workflows(
        self,
        workflows: Dict[str, Dict[str, Any]],
        preferred_intents: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        过滤工作流，只保留 preferred_intents 中的意图
        
        Args:
            workflows: 原始工作流映射
            preferred_intents: 优先意图列表
        
        Returns:
            过滤后的工作流映射
        """
        filtered = {}
        for intent_id in preferred_intents:
            if intent_id in workflows:
                filtered[intent_id] = workflows[intent_id]
        
        return filtered
    
    def _load_prompt_file(self, prompt_file: str) -> Optional[str]:
        """
        加载工作流 Prompt 文件
        
        Args:
            prompt_file: Prompt 文件相对路径（相对于 workflow_dir）
        
        Returns:
            文件内容，如果文件不存在则返回 None
        """
        try:
            file_path = self.workflow_dir / prompt_file
            
            if not file_path.exists():
                logger.warning(f"工作流文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"成功加载工作流文件: {file_path} ({len(content)} 字符)")
            return content
        
        except Exception as e:
            logger.error(f"加载工作流文件失败 {prompt_file}: {e}")
            return None
    
    def list_available_workflows(self) -> List[str]:
        """列出所有可用的工作流"""
        return list(self.workflows.keys())
    
    def has_workflow(self, intent: str) -> bool:
        """检查是否有对应意图的工作流"""
        return intent in self.workflows
