"""
Prompt 构建器 - 模板化 Prompt 系统

核心理念：
- Prompt 由多个 section 组成
- 每个 section 可以是独立的模板文件
- 通过配置动态组合 sections
- 支持变量替换和条件渲染
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Prompt 构建器
    
    功能：
    1. 加载 Prompt 模板文件
    2. 动态填充 sections
    3. 根据权限过滤工具
    4. 注入上下文和记忆
    5. 渲染最终 Prompt
    """
    
    def __init__(self, skill_config: 'SkillConfig'):
        """
        初始化 Prompt 构建器
        
        Args:
            skill_config: Skill 配置对象
        """
        self.skill = skill_config
        self.logger = logging.getLogger(f"prompt_builder.{skill_config.name}")
        
        # 获取 Skill 目录
        self.skill_dir = getattr(skill_config, 'skill_path', None)
        if not self.skill_dir:
            self.skill_dir = getattr(skill_config, 'skill_dir', None)
        
        # 初始化 Jinja2 环境
        if self.skill_dir:
            template_dir = Path(self.skill_dir) / 'prompts'
            if template_dir.exists():
                self.jinja_env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    trim_blocks=True,
                    lstrip_blocks=True
                )
            else:
                self.jinja_env = None
                self.logger.warning(f"Prompt 模板目录不存在: {template_dir}")
        else:
            self.jinja_env = None
            self.logger.warning("Skill 目录未设置，无法加载模板")
        
        # 模板缓存
        self._template_cache: Dict[str, str] = {}
        
        self.logger.info(f"Prompt 构建器初始化完成: {skill_config.name}")
    
    def build(
        self,
        workflow_prompt: Optional[str],
        context: Dict[str, Any],
        user_input: str
    ) -> str:
        """
        构建完整 Prompt
        
        Args:
            workflow_prompt: 工作流 Prompt（可选）
            context: 上下文（包含记忆、项目理解等）
            user_input: 用户输入
        
        Returns:
            完整的 Prompt 字符串
        """
        self.logger.debug("开始构建 Prompt")
        
        # 1. 加载基础模板
        base_template = self._load_base_template()
        
        # 2. 构建各个 section
        sections = {
            'role_section': self._build_role_section(),
            'capabilities_section': self._build_capabilities_section(),
            'constraints_section': self._build_constraints_section(),
            'tools_section': self._build_tools_section(context),
            'context_section': self._build_context_section(context),
            'workflow_section': workflow_prompt or '',
            'user_input': user_input
        }
        
        # 3. 渲染模板
        final_prompt = self._render_template(base_template, sections)
        
        self.logger.debug(f"Prompt 构建完成，长度: {len(final_prompt)} 字符")
        
        return final_prompt
    
    def _load_base_template(self) -> str:
        """
        加载基础模板
        
        Returns:
            基础模板字符串
        """
        # 检查配置中是否指定了模板
        prompt_config = getattr(self.skill, 'prompt_template', None)
        
        if prompt_config and isinstance(prompt_config, dict):
            base_template_path = prompt_config.get('base', 'base_template.md')
        else:
            base_template_path = 'base_template.md'
        
        # 尝试加载模板文件
        template_content = self._load_template_file(base_template_path)
        
        if template_content:
            return template_content
        
        # 如果没有模板文件，使用默认模板
        self.logger.info("使用默认基础模板")
        return self._get_default_base_template()
    
    def _load_template_file(self, filename: str) -> Optional[str]:
        """
        加载模板文件
        
        Args:
            filename: 模板文件名
        
        Returns:
            模板内容，如果文件不存在返回 None
        """
        # 检查缓存
        if filename in self._template_cache:
            return self._template_cache[filename]
        
        if not self.skill_dir:
            return None
        
        template_path = Path(self.skill_dir) / 'prompts' / filename
        
        if not template_path.exists():
            self.logger.debug(f"模板文件不存在: {template_path}")
            return None
        
        try:
            content = template_path.read_text(encoding='utf-8')
            self._template_cache[filename] = content
            self.logger.debug(f"加载模板文件: {filename}")
            return content
        except Exception as e:
            self.logger.error(f"加载模板文件失败: {filename}, 错误: {e}")
            return None
    
    def _get_default_base_template(self) -> str:
        """
        获取默认基础模板
        
        Returns:
            默认模板字符串
        """
        return """# 角色定义
{{ role_section }}

# 核心能力
{{ capabilities_section }}

# 约束条件
{{ constraints_section }}

# 可用工具
{{ tools_section }}

# 当前上下文
{{ context_section }}

# 工作流指导
{{ workflow_section }}

# 用户输入
{{ user_input }}
"""
    
    def _build_role_section(self) -> str:
        """
        构建角色定义 section
        
        Returns:
            角色定义字符串
        """
        # 检查配置中是否有 role 定义
        role_config = getattr(self.skill, 'role', None)
        
        if role_config and isinstance(role_config, dict):
            # 从配置构建
            name = role_config.get('name', self.skill.name)
            identity = role_config.get('identity', '')
            principles = role_config.get('core_principles', [])
            
            parts = [f"你是 {name}"]
            if identity:
                parts.append(f"，{identity}")
            parts.append("。")
            
            if principles:
                parts.append("\n\n核心原则：")
                for i, principle in enumerate(principles, 1):
                    parts.append(f"\n{i}. {principle}")
            
            return ''.join(parts)
        
        # 尝试从模板文件加载
        prompt_config = getattr(self.skill, 'prompt_template', None)
        if prompt_config and isinstance(prompt_config, dict):
            role_template = prompt_config.get('sections', {}).get('role')
            if role_template:
                content = self._load_template_file(role_template)
                if content:
                    return content
        
        # 默认角色定义
        return f"你是 {self.skill.name}，一个专业的 AI 助手。"
    
    def _build_capabilities_section(self) -> str:
        """
        构建能力说明 section
        
        Returns:
            能力说明字符串
        """
        # 尝试从模板文件加载
        prompt_config = getattr(self.skill, 'prompt_template', None)
        if prompt_config and isinstance(prompt_config, dict):
            cap_template = prompt_config.get('sections', {}).get('capabilities')
            if cap_template:
                content = self._load_template_file(cap_template)
                if content:
                    return content
        
        # 从 description 生成
        description = self.skill.description or "提供专业的技术支持"
        return f"核心能力：{description}"
    
    def _build_constraints_section(self) -> str:
        """
        构建约束条件 section
        
        Returns:
            约束条件字符串
        """
        # 尝试从模板文件加载
        prompt_config = getattr(self.skill, 'prompt_template', None)
        if prompt_config and isinstance(prompt_config, dict):
            const_template = prompt_config.get('sections', {}).get('constraints')
            if const_template:
                content = self._load_template_file(const_template)
                if content:
                    return content
        
        # 从权限配置生成
        permissions = getattr(self.skill, 'permissions', None)
        
        constraints = []
        
        if permissions and isinstance(permissions, dict):
            if permissions.get('read_only'):
                constraints.append("- 只读模式：不能修改任何文件")
            
            forbidden_tools = permissions.get('forbidden_tools', [])
            if forbidden_tools:
                constraints.append(f"- 禁止使用的工具：{', '.join(forbidden_tools)}")
        
        if constraints:
            return "约束条件：\n" + '\n'.join(constraints)
        
        return "约束条件：遵循最佳实践，确保代码质量和安全性。"
    
    def _build_tools_section(self, context: Dict[str, Any]) -> str:
        """
        构建工具列表 section
        
        Args:
            context: 上下文（可能包含过滤后的工具列表）
        
        Returns:
            工具列表字符串
        """
        # 获取工具列表（优先使用 context 中的，因为可能已经过滤）
        tools = context.get('available_tools') or self.skill.tools or []
        
        if not tools:
            return "可用工具：无"
        
        # 获取工具注册表
        from ..tools import get_tool_registry
        tool_registry = get_tool_registry()
        
        # 构建工具说明
        tool_descriptions = []
        for tool_name in tools:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                desc = getattr(tool, 'description', tool_name)
                tool_descriptions.append(f"- {tool_name}: {desc}")
            else:
                tool_descriptions.append(f"- {tool_name}")
        
        return "可用工具：\n" + '\n'.join(tool_descriptions)
    
    def _build_context_section(self, context: Dict[str, Any]) -> str:
        """
        构建上下文 section
        
        Args:
            context: 上下文（包含记忆、项目理解等）
        
        Returns:
            上下文字符串
        """
        parts = []
        
        # 1. 对话历史
        history = context.get('conversation_history', [])
        if history:
            parts.append("## 对话历史")
            for h in history[-3:]:  # 只显示最近 3 轮
                parts.append(f"用户: {h.get('user', '')}")
                parts.append(f"助手: {h.get('ai', '')}")
                parts.append("")
        
        # 2. 对话摘要
        summary = context.get('conversation_summary')
        if summary:
            parts.append("## 对话摘要")
            parts.append(summary)
            parts.append("")
        
        # 3. 项目理解
        project_block = context.get('project_understanding_block')
        if project_block:
            parts.append("## 项目理解")
            parts.append(project_block)
            parts.append("")
        
        # 4. 用户偏好
        preferences = context.get('user_preferences')
        if preferences:
            parts.append("## 用户偏好")
            for key, value in preferences.items():
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        if not parts:
            return "当前上下文：无"
        
        return '\n'.join(parts)
    
    def _render_template(self, template: str, sections: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template: 模板字符串
            sections: Section 数据
        
        Returns:
            渲染后的字符串
        """
        try:
            # 使用 Jinja2 渲染
            jinja_template = Template(template)
            return jinja_template.render(**sections)
        except Exception as e:
            self.logger.error(f"模板渲染失败: {e}")
            # 降级：简单字符串替换
            result = template
            for key, value in sections.items():
                result = result.replace(f"{{{{ {key} }}}}", str(value))
            return result
