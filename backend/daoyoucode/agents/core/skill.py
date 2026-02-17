"""
Skill配置和加载器

负责加载和管理Skill配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillConfig:
    """Skill配置"""
    name: str
    version: str
    description: str
    
    # 编排器配置
    orchestrator: str = "simple"
    
    # Agent配置
    agent: str = None  # 单个Agent
    agents: List[str] = field(default_factory=list)  # 多个Agent
    
    # Prompt配置（可插拔）
    prompt: Dict = field(default_factory=dict)
    
    # LLM配置
    llm: Dict = field(default_factory=lambda: {
        'model': 'qwen-max',
        'temperature': 0.7,
        'max_tokens': 2000
    })
    
    # 中间件配置
    middleware: List[str] = field(default_factory=list)
    
    # 工具配置
    tools: List[str] = field(default_factory=list)
    # 按 Agent 分配工具（仅 multi_agent 使用）：agent 名 -> 工具名列表，未列出的 Agent 用 tools
    agent_tools: Dict[str, List[str]] = field(default_factory=dict)
    
    # 权限配置
    permissions: Dict = field(default_factory=dict)
    
    # Hook配置
    hooks: List[str] = field(default_factory=list)
    
    # 输入输出
    inputs: List[Dict] = field(default_factory=list)
    outputs: List[Dict] = field(default_factory=list)
    
    # 元数据
    metadata: Dict = field(default_factory=dict)
    skill_path: Path = None
    # 可选：了解项目预取触发词（字符串列表），用户输入包含任一词即预取三层
    project_understanding_triggers: List[str] = field(default_factory=list)
    # 为 true 时用 LLM 判断「是否想了解项目/架构」意图，不依赖触发词；与 triggers 二选一或并用（intent 优先）
    project_understanding_use_intent: bool = False


class SkillLoader:
    """Skill加载器"""
    
    def __init__(self, skills_dirs: Optional[List[str]] = None):
        if skills_dirs is None:
            # 尝试多个可能的路径
            possible_dirs = [
                "skills",
                "../skills",
                Path(__file__).parent.parent.parent.parent / "skills"
            ]
            skills_dirs = [str(d) for d in possible_dirs if Path(d).exists()]
        
        self.skills_dirs = [Path(d) for d in skills_dirs if Path(d).exists()]
        self.skills: Dict[str, SkillConfig] = {}
        
        logger.info(f"Skill加载器初始化，搜索路径: {[str(d) for d in self.skills_dirs]}")
    
    def load_all_skills(self) -> Dict[str, SkillConfig]:
        """加载所有Skill"""
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir() or skill_dir.name.startswith(('_', '.')):
                    continue
                
                try:
                    skill = self.load_skill(skill_dir)
                    if skill and skill.name not in self.skills:
                        self.skills[skill.name] = skill
                        logger.info(f"已加载Skill: {skill.name} v{skill.version}")
                except Exception as e:
                    logger.error(f"加载Skill {skill_dir.name} 失败: {e}")
        
        logger.info(f"共加载了 {len(self.skills)} 个Skill")
        return self.skills
    
    def load_skill(self, skill_path: Path) -> Optional[SkillConfig]:
        """加载单个Skill"""
        if not skill_path.is_dir():
            return None
        
        yaml_path = skill_path / "skill.yaml"
        if not yaml_path.exists():
            logger.warning(f"Skill目录 {skill_path} 缺少 skill.yaml")
            return None
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 验证必需字段
        required_fields = ['name', 'version', 'description']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' in {yaml_path}")
        
        # 处理prompt配置
        prompt_config = config.get('prompt', {})
        if isinstance(prompt_config, dict) and 'file' in prompt_config:
            # 转换为绝对路径
            prompt_file = skill_path / prompt_config['file']
            if prompt_file.exists():
                prompt_config['file'] = str(prompt_file)
        
        return SkillConfig(
            name=config['name'],
            version=config['version'],
            description=config['description'],
            orchestrator=config.get('orchestrator', 'simple'),
            agent=config.get('agent'),
            agents=config.get('agents', []),
            prompt=prompt_config,
            llm=config.get('llm', {}),
            middleware=config.get('middleware', []),
            tools=config.get('tools', []),
            agent_tools=config.get('agent_tools', {}),
            permissions=config.get('permissions', {}),
            hooks=config.get('hooks', []),
            inputs=config.get('inputs', []),
            outputs=config.get('outputs', []),
            metadata=config.get('metadata', {}),
            skill_path=skill_path,
            project_understanding_triggers=config.get('project_understanding_triggers', []),
            project_understanding_use_intent=config.get('project_understanding_use_intent', False)
        )
    
    def get_skill(self, name: str) -> Optional[SkillConfig]:
        """获取指定Skill"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有Skill信息"""
        return [
            {
                'name': skill.name,
                'version': skill.version,
                'description': skill.description,
                'orchestrator': skill.orchestrator
            }
            for skill in self.skills.values()
        ]


# 全局单例
_skill_loader = None


def get_skill_loader(skills_dirs: Optional[List[str]] = None) -> SkillLoader:
    """获取Skill加载器单例"""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader(skills_dirs)
        _skill_loader.load_all_skills()
    return _skill_loader
