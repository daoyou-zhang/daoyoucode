"""
结果格式化器

将工具返回的原始结果格式化为用户友好的输出。
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResultFormatter:
    """结果格式化器"""
    
    def format(self, tool_name: str, result: Any) -> str:
        """
        格式化工具结果
        
        Args:
            tool_name: 工具名称
            result: 工具返回的结果
            
        Returns:
            格式化后的字符串
        """
        # 如果result是ToolResult对象，提取内容
        if hasattr(result, 'content'):
            content = result.content
            metadata = getattr(result, 'metadata', {})
            success = getattr(result, 'success', True)
            error = getattr(result, 'error', None)
        else:
            # 如果是字典
            if isinstance(result, dict):
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                success = result.get('success', True)
                error = result.get('error', None)
            else:
                # 其他类型，直接转字符串
                return str(result)
        
        # 如果失败，显示错误
        if not success and error:
            return f"❌ {tool_name} 失败: {error}"
        
        # 根据工具类型格式化
        formatter_method = getattr(self, f'_format_{tool_name}', None)
        if formatter_method:
            return formatter_method(content, metadata)
        
        # 默认格式化
        return self._format_default(tool_name, content, metadata)
    
    def _format_semantic_code_search(self, content: str, metadata: Dict) -> str:
        """格式化语义代码搜索结果"""
        if not content:
            return "🔍 未找到相关代码"
        
        count = metadata.get('count', 0)
        has_lsp = metadata.get('has_lsp_info', False)
        
        lines = [f"🔍 找到 {count} 个相关代码片段"]
        
        if has_lsp:
            lines.append("📊 包含LSP增强信息（质量评分、类型注解、引用计数）")
        
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_lsp_diagnostics(self, content: str, metadata: Dict) -> str:
        """格式化LSP诊断结果"""
        error_count = metadata.get('error_count', 0)
        warning_count = metadata.get('warning_count', 0)
        
        if error_count == 0 and warning_count == 0:
            return "✅ 代码检查通过，未发现问题"
        
        lines = []
        if error_count > 0:
            lines.append(f"❌ 发现 {error_count} 个错误")
        if warning_count > 0:
            lines.append(f"⚠️  发现 {warning_count} 个警告")
        
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_repo_map(self, content: str, metadata: Dict) -> str:
        """格式化代码地图结果"""
        file_count = metadata.get('file_count', 0)
        has_lsp = metadata.get('has_lsp_info', False)
        
        lines = [f"🗺️  代码地图（{file_count} 个文件）"]
        
        if has_lsp:
            lines.append("✓ LSP增强：显示类型签名和引用计数")
        
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_discover_project_docs(self, content: str, metadata: Dict) -> str:
        """格式化项目文档结果"""
        doc_count = metadata.get('doc_count', 0)
        
        if doc_count == 0:
            return "📄 未找到项目文档"
        
        lines = [f"📄 找到 {doc_count} 个项目文档"]
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_get_repo_structure(self, content: str, metadata: Dict) -> str:
        """格式化项目结构结果"""
        lines = ["📁 项目结构"]
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_write_file(self, content: str, metadata: Dict) -> str:
        """格式化写文件结果"""
        file_path = metadata.get('file_path', '')
        verified = metadata.get('verified', False)
        diagnostics = metadata.get('diagnostics', [])
        
        lines = [f"✅ 文件已写入: {file_path}"]
        
        if verified:
            if diagnostics:
                error_count = len([d for d in diagnostics if d.get('severity') == 1])
                warning_count = len([d for d in diagnostics if d.get('severity') == 2])
                
                if error_count > 0:
                    lines.append(f"❌ 代码验证失败: {error_count} 个错误")
                elif warning_count > 0:
                    lines.append(f"⚠️  代码验证通过，但有 {warning_count} 个警告")
                else:
                    lines.append("✓ 代码验证通过")
            else:
                lines.append("✓ 代码验证通过")
        
        return "\n".join(lines)
    
    def _format_lsp_find_references(self, content: str, metadata: Dict) -> str:
        """格式化查找引用结果"""
        ref_count = metadata.get('reference_count', 0)
        
        if ref_count == 0:
            return "🔗 未找到引用"
        
        lines = [f"🔗 找到 {ref_count} 个引用"]
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_lsp_hover(self, content: str, metadata: Dict) -> str:
        """格式化hover信息结果"""
        has_type = metadata.get('has_type_info', False)
        has_doc = metadata.get('has_documentation', False)
        
        lines = ["ℹ️  符号信息"]
        
        if has_type:
            lines.append("✓ 包含类型信息")
        if has_doc:
            lines.append("✓ 包含文档")
        
        lines.append("")
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_default(self, tool_name: str, content: str, metadata: Dict) -> str:
        """默认格式化"""
        if not content:
            return f"✓ {tool_name} 执行完成"
        
        return content


# 全局单例
_result_formatter = None


def get_result_formatter() -> ResultFormatter:
    """获取结果格式化器单例"""
    global _result_formatter
    if _result_formatter is None:
        _result_formatter = ResultFormatter()
    return _result_formatter
