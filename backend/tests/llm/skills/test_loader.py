"""
测试Skill加载器
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from daoyoucode.llm.skills import SkillLoader, SkillConfig


@pytest.fixture
def temp_skills_dir():
    """创建临时Skill目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_yaml_skill(temp_skills_dir):
    """创建示例YAML格式Skill"""
    skill_dir = temp_skills_dir / "test_skill"
    skill_dir.mkdir()
    
    # skill.yaml
    yaml_content = """name: test_skill
version: "1.0.0"
description: "测试Skill"

llm:
  model: qwen-max
  temperature: 0.7
  max_tokens: 1000

inputs:
  - name: user_message
    type: string
    required: true

outputs:
  - name: response
    type: string
"""
    
    (skill_dir / "skill.yaml").write_text(yaml_content, encoding='utf-8')
    
    # prompt.md
    prompt_content = """你是一个测试助手。

用户消息: {{ user_message }}

请回复用户。"""
    
    (skill_dir / "prompt.md").write_text(prompt_content, encoding='utf-8')
    
    return skill_dir


@pytest.fixture
def sample_opencode_skill(temp_skills_dir):
    """创建示例OpenCode格式Skill"""
    skill_file = temp_skills_dir / "test_agent.md"
    
    content = """---
description: Test agent
model: qwen-max
temperature: 0.7
---

You are a test agent.

User message: {{ user_message }}

Please respond.
"""
    
    skill_file.write_text(content, encoding='utf-8')
    return skill_file


class TestSkillLoader:
    """测试SkillLoader"""
    
    def test_init(self):
        """测试初始化"""
        loader = SkillLoader()
        assert loader is not None
        assert isinstance(loader.skills_dirs, list)
    
    def test_load_yaml_skill(self, sample_yaml_skill):
        """测试加载YAML格式Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        skill = loader.load_skill(sample_yaml_skill)
        
        assert skill is not None
        assert skill.name == "test_skill"
        assert skill.version == "1.0.0"
        assert skill.description == "测试Skill"
        assert "你是一个测试助手" in skill.prompt_template
        assert skill.llm['model'] == "qwen-max"
        assert len(skill.inputs) == 1
        assert len(skill.outputs) == 1
    
    def test_load_opencode_skill(self, sample_opencode_skill):
        """测试加载OpenCode格式Skill"""
        loader = SkillLoader()
        skill = loader.load_skill(sample_opencode_skill)
        
        assert skill is not None
        assert skill.name == "test_agent"
        assert "You are a test agent" in skill.prompt_template
        assert skill.llm['model'] == "qwen-max"
    
    def test_load_all_skills(self, sample_yaml_skill):
        """测试加载所有Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        skills = loader.load_all_skills()
        
        assert len(skills) > 0
        assert "test_skill" in skills
    
    def test_get_skill(self, sample_yaml_skill):
        """测试获取Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        loader.load_all_skills()
        
        skill = loader.get_skill("test_skill")
        assert skill is not None
        assert skill.name == "test_skill"
        
        # 不存在的Skill
        skill = loader.get_skill("nonexistent")
        assert skill is None
    
    def test_list_skills(self, sample_yaml_skill):
        """测试列出Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        loader.load_all_skills()
        
        skills_list = loader.list_skills()
        assert len(skills_list) > 0
        assert any(s['name'] == 'test_skill' for s in skills_list)
    
    def test_search_skills(self, sample_yaml_skill):
        """测试搜索Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        loader.load_all_skills()
        
        # 搜索名称
        results = loader.search_skills("test")
        assert len(results) > 0
        
        # 搜索描述
        results = loader.search_skills("测试")
        assert len(results) > 0
        
        # 搜索不存在的
        results = loader.search_skills("nonexistent")
        assert len(results) == 0
    
    def test_reload_skill(self, sample_yaml_skill):
        """测试重新加载Skill"""
        loader = SkillLoader(skills_dirs=[str(sample_yaml_skill.parent)])
        loader.load_all_skills()
        
        # 重新加载
        success = loader.reload_skill("test_skill")
        assert success is True
        
        # 重新加载不存在的Skill
        success = loader.reload_skill("nonexistent")
        assert success is False
    
    def test_skill_priority(self, temp_skills_dir):
        """测试Skill优先级（不覆盖已加载的）"""
        # 创建两个同名Skill
        skill1_dir = temp_skills_dir / "dir1" / "test_skill"
        skill1_dir.mkdir(parents=True)
        
        yaml1 = """name: test_skill
version: "1.0.0"
description: "第一个Skill"
"""
        (skill1_dir / "skill.yaml").write_text(yaml1, encoding='utf-8')
        (skill1_dir / "prompt.md").write_text("Prompt 1", encoding='utf-8')
        
        skill2_dir = temp_skills_dir / "dir2" / "test_skill"
        skill2_dir.mkdir(parents=True)
        
        yaml2 = """name: test_skill
version: "2.0.0"
description: "第二个Skill"
"""
        (skill2_dir / "skill.yaml").write_text(yaml2, encoding='utf-8')
        (skill2_dir / "prompt.md").write_text("Prompt 2", encoding='utf-8')
        
        # 加载（dir1优先）
        loader = SkillLoader(skills_dirs=[
            str(temp_skills_dir / "dir1"),
            str(temp_skills_dir / "dir2")
        ])
        loader.load_all_skills()
        
        skill = loader.get_skill("test_skill")
        assert skill.version == "1.0.0"
        assert skill.description == "第一个Skill"


class TestSkillConfig:
    """测试SkillConfig"""
    
    def test_skill_config_creation(self):
        """测试创建SkillConfig"""
        config = SkillConfig(
            name="test",
            version="1.0.0",
            description="Test skill",
            prompt_template="Hello {{ name }}"
        )
        
        assert config.name == "test"
        assert config.version == "1.0.0"
        assert config.llm['model'] == 'qwen-max'
        assert config.inputs == []
        assert config.outputs == []
