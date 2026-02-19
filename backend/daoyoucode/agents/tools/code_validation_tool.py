"""
代码验证工具 - 智能代码补全验证

验证代码片段是否正确，提供修正建议
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CodeSnippetValidationTool(BaseTool):
    """验证代码片段工具"""
    
    def __init__(self):
        super().__init__(
            name="validate_code_snippet",
            description="验证代码片段是否正确，检测语法和类型错误"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code_snippet": {
                        "type": "string",
                        "description": "要验证的代码片段"
                    },
                    "context_file": {
                        "type": "string",
                        "description": "上下文文件路径（用于确定语言和导入）"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "javascript", "typescript", "go", "rust"],
                        "description": "编程语言（默认从context_file推断）",
                        "default": "python"
                    },
                    "add_context": {
                        "type": "boolean",
                        "description": "是否自动添加上下文（导入等）",
                        "default": True
                    }
                },
                "required": ["code_snippet"]
            }
        }
    
    async def execute(
        self,
        code_snippet: str,
        context_file: Optional[str] = None,
        language: str = "python",
        add_context: bool = True
    ) -> ToolResult:
        """
        验证代码片段
        
        Args:
            code_snippet: 要验证的代码片段
            context_file: 上下文文件（用于确定语言和导入）
            language: 编程语言
            add_context: 是否自动添加上下文
        
        Returns:
            验证结果（是否有错误、错误详情、修正建议）
        """
        try:
            # 1. 推断语言
            if context_file:
                language = self._infer_language(context_file)
            
            # 2. 创建完整的临时文件
            temp_file = await self._create_temp_file(
                code_snippet,
                context_file,
                language,
                add_context
            )
            
            # 3. 使用LSP验证
            diagnostics = await self._verify_with_lsp(temp_file, language)
            
            # 4. 分析错误
            errors = [d for d in diagnostics if d.get('severity') == 1]
            warnings = [d for d in diagnostics if d.get('severity') == 2]
            
            # 5. 生成修正建议
            suggestions = []
            if errors:
                suggestions = self._generate_fix_suggestions(code_snippet, errors)
            
            # 6. 清理临时文件
            self._cleanup_temp_file(temp_file)
            
            # 7. 格式化输出
            if errors:
                error_messages = [
                    f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown error')}"
                    for d in errors[:5]
                ]
                
                content = {
                    'valid': False,
                    'errors': error_messages,
                    'warnings': [d.get('message') for d in warnings[:3]],
                    'suggestions': suggestions
                }
                
                return ToolResult(
                    success=False,
                    content=content,
                    error=f"代码有{len(errors)}个错误",
                    metadata={
                        'error_count': len(errors),
                        'warning_count': len(warnings),
                        'language': language
                    }
                )
            else:
                content = {
                    'valid': True,
                    'warnings': [d.get('message') for d in warnings[:3]] if warnings else []
                }
                
                return ToolResult(
                    success=True,
                    content=content,
                    metadata={
                        'error_count': 0,
                        'warning_count': len(warnings),
                        'language': language
                    }
                )
        
        except Exception as e:
            logger.error(f"代码验证失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=f"验证失败: {str(e)}"
            )
    
    def _infer_language(self, file_path: str) -> str:
        """从文件扩展名推断语言"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        ext = Path(file_path).suffix
        return ext_to_lang.get(ext, 'python')
    
    async def _create_temp_file(
        self,
        code_snippet: str,
        context_file: Optional[str],
        language: str,
        add_context: bool
    ) -> Path:
        """创建临时文件"""
        # 确定文件扩展名
        lang_to_ext = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'go': '.go',
            'rust': '.rs'
        }
        ext = lang_to_ext.get(language, '.py')
        
        # 创建临时文件
        temp_dir = Path(tempfile.gettempdir()) / "daoyoucode_validation"
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"snippet_{id(code_snippet)}{ext}"
        
        # 构建完整内容
        full_content = []
        
        # 添加上下文（导入等）
        if add_context and context_file:
            context_imports = await self._extract_imports(context_file, language)
            if context_imports:
                full_content.append(context_imports)
                full_content.append("")
        
        # 添加代码片段
        full_content.append(code_snippet)
        
        # 写入文件
        temp_file.write_text('\n'.join(full_content), encoding='utf-8')
        
        return temp_file
    
    async def _extract_imports(self, context_file: str, language: str) -> str:
        """从上下文文件提取导入语句"""
        try:
            file_path = self.resolve_path(context_file)
            if not file_path.exists():
                return ""
            
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            imports = []
            
            if language == 'python':
                # 提取Python导入
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        imports.append(line)
                    elif stripped and not stripped.startswith('#'):
                        # 遇到非导入的代码，停止
                        if imports:
                            break
            
            elif language in ['javascript', 'typescript']:
                # 提取JS/TS导入
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('export '):
                        imports.append(line)
                    elif stripped and not stripped.startswith('//'):
                        if imports:
                            break
            
            return '\n'.join(imports)
        
        except Exception as e:
            logger.debug(f"提取导入失败: {e}")
            return ""
    
    async def _verify_with_lsp(self, file_path: Path, language: str) -> List[Dict]:
        """使用LSP验证代码"""
        try:
            from .lsp_tools import with_lsp_client
            import asyncio
            
            # 使用LSP验证
            result = await with_lsp_client(
                str(file_path),
                lambda client: client.diagnostics(str(file_path), wait_time=2.0)
            )
            
            diagnostics = result.get('items', [])
            logger.debug(f"LSP返回{len(diagnostics)}个诊断信息")
            
            return diagnostics
        
        except Exception as e:
            logger.error(f"LSP验证失败: {e}")
            return []
    
    def _generate_fix_suggestions(
        self,
        code: str,
        errors: List[Dict]
    ) -> List[str]:
        """生成修正建议"""
        suggestions = []
        
        for error in errors[:3]:  # 最多3个建议
            message = error.get('message', '').lower()
            
            # 常见错误模式匹配
            if 'missing' in message and 'argument' in message:
                # 缺少参数
                import re
                match = re.search(r"'(\w+)'", error.get('message', ''))
                if match:
                    param_name = match.group(1)
                    suggestions.append(f"添加缺少的参数: {param_name}=...")
                else:
                    suggestions.append("检查函数调用是否缺少必需参数")
            
            elif 'type' in message and ('mismatch' in message or 'cannot be assigned' in message):
                # 类型不匹配
                suggestions.append("检查参数类型是否匹配函数签名")
            
            elif 'undefined' in message or 'not defined' in message:
                # 未定义
                import re
                match = re.search(r'"(\w+)"', error.get('message', ''))
                if match:
                    name = match.group(1)
                    suggestions.append(f"'{name}' 未定义，检查是否需要导入或定义")
                else:
                    suggestions.append("检查变量/函数名是否正确，是否需要导入")
            
            elif 'expected' in message and ':' in message:
                # 语法错误（缺少冒号等）
                suggestions.append("检查语法，可能缺少冒号、括号或其他符号")
            
            elif 'too many' in message and 'argument' in message:
                # 参数过多
                suggestions.append("检查函数调用的参数数量是否正确")
            
            else:
                # 通用建议
                suggestions.append(f"修复错误: {error.get('message', 'Unknown error')}")
        
        return suggestions
    
    def _cleanup_temp_file(self, file_path: Path):
        """清理临时文件"""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.debug(f"清理临时文件失败: {e}")
