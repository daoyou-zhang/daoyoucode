"""
智能上下文选择器

自动选择和添加相关文件到上下文。
灵感来源：daoyouCodePilot的auto_add_related_files
"""

from typing import List, Set, Dict, Optional
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class ContextSelector:
    """智能上下文选择器"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
    
    def auto_select_files(
        self,
        instruction: str,
        current_files: Set[str],
        max_files: int = 10,
        max_file_size: int = 100 * 1024  # 100KB
    ) -> List[str]:
        """
        自动选择相关文件
        
        Args:
            instruction: 指令
            current_files: 当前已有的文件
            max_files: 最大文件数
            max_file_size: 最大文件大小（字节）
        
        Returns:
            新添加的文件列表
        """
        added_files = []
        
        try:
            # 1. 提取引用
            references = self._extract_references(instruction)
            
            # 2. 添加直接提到的文件
            for file_path in references['files']:
                if file_path not in current_files:
                    abs_path = self.repo_path / file_path
                    if abs_path.exists() and abs_path.stat().st_size <= max_file_size:
                        added_files.append(file_path)
                        if len(added_files) >= max_files:
                            break
            
            # 3. 查找函数定义所在文件
            if len(added_files) < max_files:
                for func_name in references['functions']:
                    file_path = self._find_function_definition(func_name, current_files)
                    if file_path and file_path not in current_files and file_path not in added_files:
                        abs_path = self.repo_path / file_path
                        if abs_path.exists() and abs_path.stat().st_size <= max_file_size:
                            added_files.append(file_path)
                            if len(added_files) >= max_files:
                                break
            
            # 4. 查找类定义所在文件
            if len(added_files) < max_files:
                for class_name in references['classes']:
                    file_path = self._find_class_definition(class_name, current_files)
                    if file_path and file_path not in current_files and file_path not in added_files:
                        abs_path = self.repo_path / file_path
                        if abs_path.exists() and abs_path.stat().st_size <= max_file_size:
                            added_files.append(file_path)
                            if len(added_files) >= max_files:
                                break
            
            logger.info(f"自动选择了 {len(added_files)} 个相关文件")
            
        except Exception as e:
            logger.warning(f"自动选择文件失败: {e}")
        
        return added_files
    
    def _extract_references(self, instruction: str) -> Dict[str, List[str]]:
        """
        提取指令中的引用
        
        Returns:
            {
                'files': List[str],
                'functions': List[str],
                'classes': List[str]
            }
        """
        return {
            'files': self._extract_file_paths(instruction),
            'functions': self._extract_function_names(instruction),
            'classes': self._extract_class_names(instruction),
        }
    
    def _extract_file_paths(self, instruction: str) -> List[str]:
        """提取文件路径"""
        file_paths = []
        
        # 匹配常见的文件路径模式
        patterns = [
            r'`([^`]+\.(py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php))`',  # 反引号包裹
            r'"([^"]+\.(py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php))"',  # 双引号包裹
            r"'([^']+\.(py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php))'",  # 单引号包裹
            r'(\w+/[\w/]+\.(py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php))',  # 路径形式
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, instruction)
            for match in matches:
                if isinstance(match, tuple):
                    file_path = match[0]
                else:
                    file_path = match
                
                if file_path not in file_paths:
                    file_paths.append(file_path)
        
        return file_paths
    
    def _extract_function_names(self, instruction: str) -> List[str]:
        """提取函数名"""
        function_names = []
        
        # 匹配函数名模式
        patterns = [
            r'函数\s*`?(\w+)`?',
            r'方法\s*`?(\w+)`?',
            r'function\s+`?(\w+)`?',
            r'method\s+`?(\w+)`?',
            r'def\s+(\w+)',
            r'async\s+def\s+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, instruction, re.IGNORECASE)
            for match in matches:
                if match not in function_names and len(match) > 2:  # 过滤太短的
                    function_names.append(match)
        
        return function_names
    
    def _extract_class_names(self, instruction: str) -> List[str]:
        """提取类名"""
        class_names = []
        
        # 匹配类名模式
        patterns = [
            r'类\s*`([A-Z]\w+)`',  # 类 `ClassName`
            r'类\s+([A-Z]\w+)',     # 类 ClassName
            r'class\s+`([A-Z]\w+)`',  # class `ClassName`
            r'class\s+([A-Z]\w+)',    # class ClassName
            r'接口\s*`([A-Z]\w+)`',
            r'接口\s+([A-Z]\w+)',
            r'interface\s+`([A-Z]\w+)`',
            r'interface\s+([A-Z]\w+)',
            r'`([A-Z][a-zA-Z0-9_]+)`',  # 任何反引号包裹的大写开头标识符
            r'\b([A-Z][a-zA-Z0-9_]{2,})\b',  # 任何大写开头的标识符（至少3个字符）
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, instruction)
            for match in matches:
                if match not in class_names:
                    class_names.append(match)
        
        return class_names
    
    def _find_function_definition(
        self,
        func_name: str,
        exclude_files: Set[str]
    ) -> Optional[str]:
        """查找函数定义所在文件"""
        try:
            # 搜索Python文件
            for py_file in self.repo_path.rglob('*.py'):
                if str(py_file.relative_to(self.repo_path)) in exclude_files:
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    # 匹配函数定义
                    if re.search(rf'def\s+{re.escape(func_name)}\s*\(', content):
                        return str(py_file.relative_to(self.repo_path))
                except Exception:
                    continue
            
            # 搜索JavaScript/TypeScript文件
            for js_file in list(self.repo_path.rglob('*.js')) + list(self.repo_path.rglob('*.ts')):
                if str(js_file.relative_to(self.repo_path)) in exclude_files:
                    continue
                
                try:
                    content = js_file.read_text(encoding='utf-8', errors='ignore')
                    # 匹配函数定义
                    if re.search(rf'function\s+{re.escape(func_name)}\s*\(', content):
                        return str(js_file.relative_to(self.repo_path))
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"查找函数定义失败: {e}")
        
        return None
    
    def _find_class_definition(
        self,
        class_name: str,
        exclude_files: Set[str]
    ) -> Optional[str]:
        """查找类定义所在文件"""
        try:
            # 搜索Python文件
            for py_file in self.repo_path.rglob('*.py'):
                if str(py_file.relative_to(self.repo_path)) in exclude_files:
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    # 匹配类定义
                    if re.search(rf'class\s+{re.escape(class_name)}\s*[:\(]', content):
                        return str(py_file.relative_to(self.repo_path))
                except Exception:
                    continue
            
            # 搜索JavaScript/TypeScript文件
            for js_file in list(self.repo_path.rglob('*.js')) + list(self.repo_path.rglob('*.ts')):
                if str(js_file.relative_to(self.repo_path)) in exclude_files:
                    continue
                
                try:
                    content = js_file.read_text(encoding='utf-8', errors='ignore')
                    # 匹配类定义
                    if re.search(rf'class\s+{re.escape(class_name)}\s*[{{]', content):
                        return str(js_file.relative_to(self.repo_path))
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"查找类定义失败: {e}")
        
        return None
