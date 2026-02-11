"""
Skill加载器
支持多种Skill格式，兼容三个工程的Skill
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from ..exceptions import SkillNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class SkillConfig:
    """Skill配置"""
    name: str
    version: str
    description: str
    
    # Prompt配置
    prompt_template: str
    prompt_files: Dict[str, str] = field(default_factory=dict)
    
    # LLM配置
    llm: Dict = field(default_factory=lambda: {
        'model': 'qwen-max',
        'temperature': 0.7,
        'max_tokens': 2000
    })
    
    # 输入输出
    inputs: List[Dict] = field(default_factory=list)
    outputs: List[Dict] = field(default_factory=list)
    
    # 触发器（可选）
    triggers: Dict = field(default_factory=dict)
    
    # 作用域（可选）
    scope: Dict = field(default_factory=dict)
    
    # 后处理
    post_process: List[str] = field(default_factory=list)
    
    # 元数据
    skill_path: Path = None
    skill_type: str = "prompt"  # prompt, agent, command


class SkillLoader:
    """
    Skill加载器
    
    支持多种Skill格式：
    1. daoyoucode格式（YAML + MD）
    2. OpenCode格式（Markdown frontmatter）
    """
    
    def __init__(self, skills_dirs: Optional[List[str]] = None):
        """
        初始化加载器
        
        Args:
            skills_dirs: Skill目录列表，按优先级排序
        """
        if skills_dirs is None:
            # 默认搜索路径
            skills_dirs = [
                "skills",  # 项目级
                str(Path.home() / ".daoyoucode" / "skills"),  # 用户级
                "opencode/.opencode/agent",  # 兼容OpenCode agent
                "opencode/.opencode/command",  # 兼容OpenCode command
            ]
        
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
                    if skill:
                        # 不覆盖已加载的Skill（优先级）
                        if skill.name not in self.skills:
                            self.skills[skill.name] = skill
                            logger.info(f"已加载Skill: {skill.name} v{skill.version} from {skill_dir}")
                except Exception as e:
                    logger.error(f"加载Skill {skill_dir.name} 失败: {e}", exc_info=True)
        
        logger.info(f"共加载了 {len(self.skills)} 个Skill")
        return self.skills
    
    def load_skill(self, skill_path: Path) -> Optional[SkillConfig]:
        """
        加载单个Skill（自动检测格式）
        
        Args:
            skill_path: Skill目录或文件路径
        
        Returns:
            SkillConfig或None
        """
        if skill_path.is_file():
            # 单文件Skill（OpenCode格式）
            return self._load_opencode_skill(skill_path)
        
        elif skill_path.is_dir():
            # 目录Skill
            yaml_path = skill_path / "skill.yaml"
            
            if yaml_path.exists():
                # daoyoucode格式
                return self._load_yaml_skill(skill_path)
            else:
                logger.warning(f"Skill目录 {skill_path} 缺少 skill.yaml")
                return None
        
        return None
    
    def _load_yaml_skill(self, skill_dir: Path) -> SkillConfig:
        """加载YAML格式的Skill"""
        yaml_path = skill_dir / "skill.yaml"
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 验证必需字段
        required_fields = ['name', 'version', 'description']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' in {yaml_path}")
        
        # 加载Prompt模板
        prompt_template = ""
        prompt_files = {}
        
        # 方式1: 单个prompt.md文件（daoyoucode格式）
        prompt_md = skill_dir / "prompt.md"
        if prompt_md.exists():
            with open(prompt_md, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        
        # 方式2: prompts目录（兼容格式）
        elif 'prompts' in config:
            prompts_config = config['prompts']
            
            if isinstance(prompts_config, dict):
                # 多个prompt文件
                for key, file_path in prompts_config.items():
                    full_path = skill_dir / file_path
                    if full_path.exists():
                        with open(full_path, 'r', encoding='utf-8') as f:
                            prompt_files[key] = f.read()
                
                # 使用main作为主模板
                prompt_template = prompt_files.get('main', '')
            
            elif isinstance(prompts_config, str):
                # 单个prompt文件
                prompt_path = skill_dir / prompts_config
                if prompt_path.exists():
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompt_template = f.read()
        
        return SkillConfig(
            name=config['name'],
            version=config['version'],
            description=config['description'],
            prompt_template=prompt_template,
            prompt_files=prompt_files,
            llm=config.get('llm', {}),
            inputs=config.get('inputs', []),
            outputs=config.get('outputs', []),
            triggers=config.get('triggers', {}),
            scope=config.get('scope', {}),
            post_process=config.get('post_process', []),
            skill_path=skill_dir,
            skill_type=config.get('type', 'prompt')
        )
    
    def _load_opencode_skill(self, skill_file: Path) -> Optional[SkillConfig]:
        """加载OpenCode格式的Skill（Markdown frontmatter）"""
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析frontmatter
        if not content.startswith('---'):
            return None
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        try:
            frontmatter = yaml.safe_load(parts[1])
            prompt_content = parts[2].strip()
        except Exception as e:
            logger.error(f"解析frontmatter失败: {e}")
            return None
        
        # 从文件名推断名称
        name = skill_file.stem
        
        return SkillConfig(
            name=name,
            version="1.0.0",
            description=frontmatter.get('description', ''),
            prompt_template=prompt_content,
            llm={
                'model': frontmatter.get('model', 'qwen-max'),
                'temperature': frontmatter.get('temperature', 0.7)
            },
            skill_path=skill_file.parent,
            skill_type='agent' if 'agent' in str(skill_file) else 'command'
        )
    
    def get_skill(self, name: str, version: str = "latest") -> Optional[SkillConfig]:
        """
        获取指定Skill
        
        Args:
            name: Skill名称
            version: 版本号（暂不支持多版本）
        
        Returns:
            SkillConfig或None
        """
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有Skill信息"""
        return [
            {
                'name': skill.name,
                'version': skill.version,
                'description': skill.description,
                'type': skill.skill_type
            }
            for skill in self.skills.values()
        ]
    
    def search_skills(self, keyword: str) -> List[SkillConfig]:
        """
        搜索Skill
        
        Args:
            keyword: 关键词
        
        Returns:
            匹配的Skill列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for skill in self.skills.values():
            # 搜索名称和描述
            if (keyword_lower in skill.name.lower() or
                keyword_lower in skill.description.lower()):
                results.append(skill)
                continue
            
            # 搜索触发器关键词
            if 'keywords' in skill.triggers:
                for kw in skill.triggers['keywords']:
                    if keyword_lower in kw.lower():
                        results.append(skill)
                        break
        
        return results
    
    def reload_skill(self, name: str) -> bool:
        """
        重新加载Skill（热更新）
        
        Args:
            name: Skill名称
        
        Returns:
            是否成功
        """
        if name not in self.skills:
            return False
        
        old_skill = self.skills[name]
        
        try:
            new_skill = self.load_skill(old_skill.skill_path)
            if new_skill:
                self.skills[name] = new_skill
                logger.info(f"已重新加载Skill: {name}")
                return True
        except Exception as e:
            logger.error(f"重新加载Skill {name} 失败: {e}")
        
        return False


def get_skill_loader(skills_dirs: Optional[List[str]] = None) -> SkillLoader:
    """获取Skill加载器"""
    if not hasattr(get_skill_loader, '_instance'):
        get_skill_loader._instance = SkillLoader(skills_dirs)
    return get_skill_loader._instance
