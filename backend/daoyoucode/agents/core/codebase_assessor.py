"""
代码库评估器

评估代码库成熟度和状态。
灵感来源：oh-my-opencode的Codebase Assessment
"""

from pathlib import Path
from typing import Dict, Any
import logging
from .behavior_guide import CodebaseState

logger = logging.getLogger(__name__)


class CodebaseAssessor:
    """代码库评估器"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
    
    def assess(self) -> CodebaseState:
        """评估代码库状态"""
        # 1. 检查配置文件
        has_linter = self._check_linter_config()
        has_formatter = self._check_formatter_config()
        has_type_config = self._check_type_config()
        
        # 2. 检查测试
        has_tests = self._check_tests()
        
        # 3. 检查依赖
        dependency_age = self._check_dependency_age()
        
        # 4. 分类
        config_score = sum([has_linter, has_formatter, has_type_config])
        
        if config_score >= 2 and has_tests:
            return CodebaseState.DISCIPLINED
        elif config_score >= 1:
            return CodebaseState.TRANSITIONAL
        elif dependency_age > 3:
            return CodebaseState.LEGACY
        elif not list(self.repo_path.rglob('*.py')):
            return CodebaseState.GREENFIELD
        else:
            return CodebaseState.CHAOTIC
    
    def get_behavior_guide(self, state: CodebaseState) -> Dict[str, str]:
        """根据状态获取行为指南"""
        guides = {
            CodebaseState.DISCIPLINED: {
                'approach': 'follow_existing_patterns',
                'message': '代码库规范良好，严格遵循现有风格',
            },
            CodebaseState.TRANSITIONAL: {
                'approach': 'ask_user',
                'message': '代码库存在多种模式，请选择要遵循的模式',
            },
            CodebaseState.LEGACY: {
                'approach': 'modernize',
                'message': '代码库较旧，建议应用现代最佳实践',
            },
            CodebaseState.CHAOTIC: {
                'approach': 'propose_standards',
                'message': '代码库缺乏规范，建议引入标准',
            },
            CodebaseState.GREENFIELD: {
                'approach': 'modern_standards',
                'message': '新项目，应用现代最佳实践',
            },
        }
        return guides[state]
    
    def _check_linter_config(self) -> bool:
        """检查linter配置"""
        configs = ['.pylintrc', '.flake8', 'pyproject.toml', '.eslintrc', '.eslintrc.json']
        return any((self.repo_path / config).exists() for config in configs)
    
    def _check_formatter_config(self) -> bool:
        """检查formatter配置"""
        configs = ['.black', 'pyproject.toml', '.prettierrc', '.prettierrc.json']
        return any((self.repo_path / config).exists() for config in configs)
    
    def _check_type_config(self) -> bool:
        """检查类型配置"""
        configs = ['mypy.ini', 'pyproject.toml', 'tsconfig.json']
        return any((self.repo_path / config).exists() for config in configs)
    
    def _check_tests(self) -> bool:
        """检查测试"""
        test_dirs = ['tests', 'test', '__tests__']
        return any((self.repo_path / test_dir).exists() for test_dir in test_dirs)
    
    def _check_dependency_age(self) -> int:
        """检查依赖年龄（简化版）"""
        # 简化实现：检查requirements.txt或package.json的修改时间
        dep_files = ['requirements.txt', 'package.json', 'Pipfile']
        for dep_file in dep_files:
            file_path = self.repo_path / dep_file
            if file_path.exists():
                import time
                mtime = file_path.stat().st_mtime
                age_years = (time.time() - mtime) / (365 * 24 * 3600)
                return int(age_years)
        return 0
