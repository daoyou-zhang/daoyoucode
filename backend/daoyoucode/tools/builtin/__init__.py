"""
内置工具注册

所有内置工具在这里注册
"""

def register_builtin_tools():
    """注册所有内置工具"""
    
    # 导入会自动注册（因为使用了@tool装饰器）
    from .. import file_tools
    
    # 未来添加更多工具
    # from .. import git_tools
    # from .. import search_tools
    # from .. import lsp_tools


__all__ = ['register_builtin_tools']
