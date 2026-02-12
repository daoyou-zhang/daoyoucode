"""
智能模型选择器

根据任务复杂度和上下文大小动态选择最优模型。
灵感来源：daoyouCodePilot的模型角色系统
"""

from typing import Tuple, Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class ModelSelector:
    """智能模型选择器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.main_model = None
        self.weak_model = None
        self.editor_model = None
        self._initialized = True
        logger.info("ModelSelector 初始化完成")
    
    def configure(
        self,
        main_model: str,
        weak_model: Optional[str] = None,
        editor_model: Optional[str] = None
    ):
        """
        配置模型
        
        Args:
            main_model: 主模型（复杂任务）
            weak_model: 弱模型（简单任务、摘要）
            editor_model: 编辑模型（代码修改）
        """
        self.main_model = main_model
        self.weak_model = weak_model or main_model
        self.editor_model = editor_model or main_model
        logger.info(f"模型配置: main={main_model}, weak={weak_model}, editor={editor_model}")
    
    def select_model(
        self,
        instruction: str,
        context_size: int = 0,
        task_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        选择最优模型
        
        Args:
            instruction: 指令
            context_size: 上下文大小（字节）
            task_type: 任务类型（可选）
        
        Returns:
            (model_name, task_type)
        """
        # 如果明确指定了任务类型
        if task_type:
            return self._get_model_by_task(task_type), task_type
        
        # 1. 分析指令复杂度
        complexity = self._analyze_complexity(instruction)
        
        # 2. 根据复杂度和上下文大小选择
        if complexity == 'simple' and context_size < 10000:
            return self.weak_model, 'weak'
        elif complexity == 'edit':
            return self.editor_model, 'editor'
        elif complexity == 'complex':
            return self.main_model, 'main'
        else:
            # 中等复杂度，根据上下文大小决定
            if context_size < 50000:
                return self.weak_model, 'weak'
            else:
                return self.main_model, 'main'
    
    def _get_model_by_task(self, task_type: str) -> str:
        """根据任务类型获取模型"""
        if task_type == 'weak':
            return self.weak_model
        elif task_type == 'editor':
            return self.editor_model
        else:
            return self.main_model
    
    def _analyze_complexity(self, instruction: str) -> str:
        """
        分析指令复杂度
        
        Returns:
            'simple', 'edit', 'medium', 'complex'
        """
        instruction_lower = instruction.lower()
        
        # 简单任务特征
        simple_patterns = [
            r'添加注释',
            r'修改变量名',
            r'格式化代码',
            r'添加类型提示',
            r'添加文档字符串',
            r'修复拼写',
            r'更新版本号',
            r'add comment',
            r'rename variable',
            r'format code',
            r'add type hint',
            r'fix typo',
        ]
        
        # 编辑任务特征
        edit_patterns = [
            r'修改.*代码',
            r'更新.*实现',
            r'调整.*逻辑',
            r'修复.*bug',
            r'edit.*code',
            r'update.*implementation',
            r'fix.*bug',
            r'change.*logic',
        ]
        
        # 复杂任务特征
        complex_patterns = [
            r'重构',
            r'实现.*功能',
            r'设计.*架构',
            r'优化.*性能',
            r'创建.*系统',
            r'构建.*模块',
            r'refactor',
            r'implement.*feature',
            r'design.*architecture',
            r'optimize.*performance',
            r'create.*system',
            r'build.*module',
        ]
        
        # 匹配模式
        for pattern in simple_patterns:
            if re.search(pattern, instruction_lower):
                return 'simple'
        
        for pattern in edit_patterns:
            if re.search(pattern, instruction_lower):
                return 'edit'
        
        for pattern in complex_patterns:
            if re.search(pattern, instruction_lower):
                return 'complex'
        
        # 根据指令长度判断
        if len(instruction) < 50:
            return 'simple'
        elif len(instruction) < 200:
            return 'medium'
        else:
            return 'complex'
    
    def get_model_info(
        self,
        instruction: str,
        context_size: int = 0
    ) -> Dict[str, Any]:
        """
        获取模型选择信息（用于显示）
        
        Returns:
            {
                'model': str,
                'task_type': str,
                'complexity': str,
                'reason': str
            }
        """
        complexity = self._analyze_complexity(instruction)
        model, task_type = self.select_model(instruction, context_size)
        
        reasons = {
            'simple': '简单任务，使用轻量模型',
            'edit': '代码编辑任务，使用编辑模型',
            'medium': '中等复杂度任务',
            'complex': '复杂任务，使用主模型',
        }
        
        return {
            'model': model,
            'task_type': task_type,
            'complexity': complexity,
            'reason': reasons.get(complexity, '自动选择'),
            'context_size': context_size,
        }


def get_model_selector() -> ModelSelector:
    """获取模型选择器实例"""
    return ModelSelector()
