"""
Agent工具分组配置

每个专业Agent只使用它需要的工具子集
"""

# ============================================================================
# 主编排Agent工具集（4个）
# ============================================================================
ORCHESTRATOR_TOOLS = [
    'repo_map',              # 生成代码地图
    'get_repo_structure',    # 获取目录结构
    'text_search',           # 快速搜索
    'read_file'              # 读取文件
]

# ============================================================================
# 代码探索Agent工具集（8个）
# ============================================================================
EXPLORE_TOOLS = [
    # 项目结构
    'repo_map',
    'get_repo_structure',
    
    # 搜索工具
    'text_search',
    'regex_search',
    
    # 文件读取
    'read_file',
    'list_files',
    'get_file_info',
    
    # AST搜索
    'find_function'
]

# ============================================================================
# 代码分析Agent工具集（10个）
# ============================================================================
ANALYZER_TOOLS = [
    # 项目理解
    'repo_map',
    'get_repo_structure',
    'read_file',
    
    # 搜索
    'text_search',
    'regex_search',
    
    # LSP工具（代码理解）
    'get_diagnostics',      # 获取诊断信息
    'find_references',      # 查找引用
    'get_symbols',          # 获取符号
    
    # AST工具
    'parse_ast',            # 解析AST
    'find_function'         # 查找函数
]

# ============================================================================
# 编程Agent工具集（12个）
# ============================================================================
PROGRAMMER_TOOLS = [
    # 文件操作
    'read_file',
    'write_file',
    'list_files',
    'get_file_info',
    
    # 搜索
    'text_search',
    'find_function',
    
    # Git工具
    'git_status',
    'git_diff',
    'git_commit',
    
    # 基础诊断
    'get_diagnostics',
    
    # 命令执行
    'run_command'
]

# ============================================================================
# 重构Agent工具集（14个）
# ============================================================================
REFACTOR_TOOLS = [
    # 文件操作
    'read_file',
    'write_file',
    'list_files',
    
    # 搜索
    'text_search',
    'regex_search',
    
    # LSP工具（重构必备）
    'get_diagnostics',      # 检查错误
    'find_references',      # 查找所有引用
    'semantic_rename',      # 语义重命名
    'get_symbols',          # 获取符号
    
    # AST工具
    'parse_ast',
    'find_function',
    
    # Git工具
    'git_diff',
    'git_commit'
]

# ============================================================================
# 测试Agent工具集（11个）
# ============================================================================
TEST_TOOLS = [
    # 文件操作
    'read_file',
    'write_file',
    'list_files',
    
    # 搜索
    'text_search',
    'find_function',
    
    # 测试执行
    'run_command',          # 运行测试命令
    'run_tests',            # 专用测试工具
    
    # Git工具
    'git_diff',
    'git_commit',
    
    # 诊断
    'get_diagnostics'
]

# ============================================================================
# 翻译Agent工具集（6个）
# ============================================================================
TRANSLATOR_TOOLS = [
    # 文件操作
    'read_file',
    'write_file',
    'list_files',
    
    # 搜索
    'text_search',
    'regex_search',
    
    # Git工具
    'git_commit'
]

# ============================================================================
# 工具分类（按功能）
# ============================================================================

# 只读工具（探索和分析）
READONLY_TOOLS = [
    'repo_map',
    'get_repo_structure',
    'read_file',
    'list_files',
    'get_file_info',
    'text_search',
    'regex_search',
    'find_function',
    'parse_ast',
    'get_symbols',
    'get_diagnostics',
    'find_references'
]

# 写入工具（编写和修改）
WRITE_TOOLS = [
    'write_file',
    'semantic_rename'
]

# Git工具（版本控制）
GIT_TOOLS = [
    'git_status',
    'git_diff',
    'git_commit',
    'git_log'
]

# 执行工具（运行和测试）
EXECUTION_TOOLS = [
    'run_command',
    'run_tests'
]

# 项目文档工具
DOC_TOOLS = [
    'generate_project_doc'
]

# ============================================================================
# Agent工具映射表
# ============================================================================
AGENT_TOOL_MAPPING = {
    'main_agent': ORCHESTRATOR_TOOLS,
    'sisyphus': ORCHESTRATOR_TOOLS,      # 主编排Agent（新增）
    'oracle': ANALYZER_TOOLS,            # 咨询Agent（新增）
    'librarian': EXPLORE_TOOLS,          # 搜索Agent（新增）
    'explore': EXPLORE_TOOLS,
    'code_analyzer': ANALYZER_TOOLS,
    'code_explorer': EXPLORE_TOOLS,
    'programmer': PROGRAMMER_TOOLS,
    'refactor_master': REFACTOR_TOOLS,
    'test_expert': TEST_TOOLS,
    'translator': TRANSLATOR_TOOLS
}

# ============================================================================
# 工具获取函数
# ============================================================================

def get_tools_for_agent(agent_name: str) -> list:
    """
    根据Agent名称获取工具集
    
    Args:
        agent_name: Agent名称
        
    Returns:
        工具名称列表
    """
    return AGENT_TOOL_MAPPING.get(agent_name, [])


def get_all_tools() -> list:
    """获取所有工具"""
    all_tools = set()
    for tools in AGENT_TOOL_MAPPING.values():
        all_tools.update(tools)
    return sorted(list(all_tools))


def get_tool_categories() -> dict:
    """获取工具分类"""
    return {
        'readonly': READONLY_TOOLS,
        'write': WRITE_TOOLS,
        'git': GIT_TOOLS,
        'execution': EXECUTION_TOOLS,
        'doc': DOC_TOOLS
    }


def validate_tools(agent_name: str, requested_tools: list) -> tuple:
    """
    验证Agent请求的工具是否合理
    
    Args:
        agent_name: Agent名称
        requested_tools: 请求的工具列表
        
    Returns:
        (is_valid, invalid_tools, suggestions)
    """
    allowed_tools = get_tools_for_agent(agent_name)
    
    if not allowed_tools:
        # 未配置工具集，允许所有工具
        return True, [], []
    
    invalid_tools = [t for t in requested_tools if t not in allowed_tools]
    
    if not invalid_tools:
        return True, [], []
    
    # 提供建议
    suggestions = []
    for tool in invalid_tools:
        # 查找哪些Agent可以使用这个工具
        agents_with_tool = [
            name for name, tools in AGENT_TOOL_MAPPING.items()
            if tool in tools
        ]
        if agents_with_tool:
            suggestions.append(
                f"工具 '{tool}' 可由以下Agent使用: {', '.join(agents_with_tool)}"
            )
    
    return False, invalid_tools, suggestions


# ============================================================================
# 统计信息
# ============================================================================

def get_tool_stats() -> dict:
    """获取工具使用统计"""
    stats = {
        'total_tools': len(get_all_tools()),
        'agents': {}
    }
    
    for agent_name, tools in AGENT_TOOL_MAPPING.items():
        stats['agents'][agent_name] = {
            'tool_count': len(tools),
            'tools': tools
        }
    
    return stats


if __name__ == '__main__':
    # 打印统计信息
    print("=" * 80)
    print("Agent工具分组统计")
    print("=" * 80)
    
    stats = get_tool_stats()
    print(f"\n总工具数: {stats['total_tools']}")
    print(f"Agent数量: {len(stats['agents'])}")
    
    print("\n各Agent工具数量:")
    for agent_name, info in sorted(stats['agents'].items(), 
                                   key=lambda x: x[1]['tool_count']):
        print(f"  {agent_name:20s}: {info['tool_count']:2d} 个工具")
    
    print("\n工具分类:")
    categories = get_tool_categories()
    for cat_name, tools in categories.items():
        print(f"  {cat_name:15s}: {len(tools):2d} 个工具")
    
    print("\n" + "=" * 80)
