"""
工具元数据定义

为每个工具提供丰富的元数据，帮助大模型智能选择工具
"""

from typing import Dict, Any, List

# 工具分类
TOOL_CATEGORIES = {
    "project_understanding": "项目理解",
    "code_search": "代码搜索",
    "file_operation": "文件操作",
    "code_edit": "代码编辑",
    "code_analysis": "代码分析",
    "git": "Git操作",
    "lsp": "LSP增强",
    "command": "命令执行",
}

# 成本级别
COST_LEVELS = {
    "low": "低成本（<1秒，<500 tokens）",
    "medium": "中等成本（1-5秒，500-2000 tokens）",
    "high": "高成本（>5秒，>2000 tokens）",
}

# 价值级别
VALUE_LEVELS = {
    "low": "低价值（辅助信息）",
    "medium": "中等价值（有用信息）",
    "high": "高价值（关键信息）",
}


def get_tool_metadata(tool_name: str) -> Dict[str, Any]:
    """获取工具的元数据"""
    return TOOL_METADATA.get(tool_name, {})


# 所有工具的元数据
TOOL_METADATA: Dict[str, Dict[str, Any]] = {
    # ========== 项目理解工具 ==========
    "repo_map": {
        "category": "project_understanding",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "初次了解项目",
            "快速定位核心代码",
            "理解项目架构",
            "查看项目全貌"
        ],
        "when_to_use": "用户想了解项目全貌时，这是最高效的工具。使用PageRank算法智能排序，优先展示最重要的代码",
        "when_not_to_use": "用户只想查看具体文件内容时，直接用 read_file 更合适",
        "typical_output": "2000-4000 tokens，包含类、函数、模块的概览",
        "execution_time": "2-5秒",
        "best_practices": [
            "首次了解项目时优先使用",
            "chat_files 为空时会自动扩大token预算",
            "结合 discover_project_docs 可以获得更全面的理解"
        ],
        "examples": [
            {
                "scenario": "用户问：这个项目是干什么的？",
                "usage": "repo_map(repo_path='.')",
                "why": "快速获取项目核心代码概览"
            }
        ]
    },
    
    "discover_project_docs": {
        "category": "project_understanding",
        "cost": "low",
        "value": "high",
        "use_cases": [
            "了解项目文档",
            "查看README",
            "理解项目说明",
            "获取项目介绍"
        ],
        "when_to_use": "需要项目的文字说明、使用指南、架构文档时使用",
        "when_not_to_use": "只需要代码结构时，用 repo_map 更高效",
        "typical_output": "500-2000 tokens，README和主要文档内容",
        "execution_time": "<1秒",
        "best_practices": [
            "与 repo_map 配合使用效果最好",
            "适合获取项目的文字描述",
            "包含README、ARCHITECTURE等关键文档"
        ]
    },
    
    "get_repo_structure": {
        "category": "project_understanding",
        "cost": "low",
        "value": "medium",
        "use_cases": [
            "查看目录结构",
            "了解文件组织",
            "查找文件位置"
        ],
        "when_to_use": "需要了解项目的目录组织结构时",
        "when_not_to_use": "需要代码内容时，用 repo_map 或 read_file",
        "typical_output": "300-1000 tokens，目录树结构",
        "execution_time": "<1秒",
        "best_practices": [
            "max_depth=3 通常足够",
            "主要用于了解文件组织"
        ]
    },
    
    # ========== 代码搜索工具 ==========
    "semantic_code_search": {
        "category": "code_search",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "定位具体功能",
            "查找相关代码",
            "语义搜索",
            "找实现位置"
        ],
        "when_to_use": "需要精准定位代码时，支持自然语言查询",
        "when_not_to_use": "已知文件名时，直接用 read_file",
        "typical_output": "500-1500 tokens，相关代码片段和位置",
        "execution_time": "1-3秒",
        "best_practices": [
            "用自然语言描述要找的功能",
            "返回最相关的代码片段",
            "找到后用 read_file 查看完整内容"
        ],
        "examples": [
            {
                "scenario": "用户问：登录功能在哪里？",
                "usage": "semantic_code_search(query='登录功能', top_k=5)",
                "why": "语义搜索最精准"
            }
        ]
    },
    
    "text_search": {
        "category": "code_search",
        "cost": "low",
        "value": "medium",
        "use_cases": [
            "关键词搜索",
            "查找文件",
            "搜索字符串"
        ],
        "when_to_use": "知道确切的关键词时使用",
        "when_not_to_use": "需要语义理解时，用 semantic_code_search",
        "typical_output": "200-800 tokens，匹配的文件和行号",
        "execution_time": "<1秒"
    },
    
    "list_files": {
        "category": "code_search",
        "cost": "low",
        "value": "low",
        "use_cases": [
            "列出文件",
            "查看目录内容"
        ],
        "when_to_use": "需要查看某个目录下有哪些文件时",
        "when_not_to_use": "需要文件内容时，直接用 read_file",
        "typical_output": "100-500 tokens，文件列表",
        "execution_time": "<1秒"
    },
    
    # ========== 文件操作工具 ==========
    "read_file": {
        "category": "file_operation",
        "cost": "low",
        "value": "high",
        "use_cases": [
            "读取文件内容",
            "查看代码",
            "理解实现"
        ],
        "when_to_use": "需要查看具体文件内容时",
        "when_not_to_use": "不知道文件位置时，先用搜索工具定位",
        "typical_output": "200-8000 tokens，文件完整内容",
        "execution_time": "<1秒",
        "best_practices": [
            "先用搜索工具找到文件位置",
            "使用相对路径",
            "大文件会自动截断"
        ]
    },
    
    "batch_read_files": {
        "category": "file_operation",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "批量读取文件",
            "查看多个文件"
        ],
        "when_to_use": "需要同时查看多个文件时，比多次调用 read_file 更高效",
        "when_not_to_use": "只需要一个文件时，用 read_file",
        "typical_output": "500-10000 tokens，多个文件内容",
        "execution_time": "1-3秒"
    },
    
    "write_file": {
        "category": "file_operation",
        "cost": "low",
        "value": "high",
        "use_cases": [
            "创建文件",
            "重写文件",
            "保存内容"
        ],
        "when_to_use": "需要创建新文件或完全重写文件时",
        "when_not_to_use": "只修改部分内容时，用 search_replace 更安全",
        "typical_output": "简短的成功/失败消息",
        "execution_time": "<1秒",
        "best_practices": [
            "大改时使用",
            "小改用 search_replace",
            "确认后再执行"
        ]
    },
    
    "batch_write_files": {
        "category": "file_operation",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "批量创建文件",
            "批量修改文件"
        ],
        "when_to_use": "需要同时修改多个文件时",
        "when_not_to_use": "只修改一个文件时，用 write_file",
        "typical_output": "简短的成功/失败消息",
        "execution_time": "1-3秒"
    },
    
    # ========== 代码编辑工具 ==========
    "search_replace": {
        "category": "code_edit",
        "cost": "low",
        "value": "high",
        "use_cases": [
            "精确修改代码",
            "替换内容",
            "小范围修改"
        ],
        "when_to_use": "需要精确修改代码的某个部分时，最安全的修改方式",
        "when_not_to_use": "需要大范围重写时，用 write_file",
        "typical_output": "简短的成功/失败消息",
        "execution_time": "<1秒",
        "best_practices": [
            "优先使用（最安全）",
            "search 内容要精确匹配",
            "一次修改一个明确的点"
        ],
        "examples": [
            {
                "scenario": "修改token过期时间",
                "usage": "search_replace(file_path='auth/login.py', search='expires_in=3600', replace='expires_in=86400')",
                "why": "精确、安全"
            }
        ]
    },
    
    # ========== 代码分析工具 ==========
    "get_file_symbols": {
        "category": "code_analysis",
        "cost": "low",
        "value": "medium",
        "use_cases": [
            "获取类和函数列表",
            "查看代码结构",
            "了解符号定义"
        ],
        "when_to_use": "需要快速了解文件中有哪些类、函数时",
        "when_not_to_use": "需要完整代码时，用 read_file",
        "typical_output": "200-1000 tokens，符号列表",
        "execution_time": "<1秒"
    },
    
    # ========== LSP工具 ==========
    "lsp_diagnostics": {
        "category": "lsp",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "检查代码错误",
            "查看警告",
            "验证代码"
        ],
        "when_to_use": "修改代码后验证是否有错误",
        "when_not_to_use": "只是查看代码时不需要",
        "typical_output": "100-500 tokens，错误和警告列表",
        "execution_time": "1-3秒"
    },
    
    "lsp_find_references": {
        "category": "lsp",
        "cost": "medium",
        "value": "high",
        "use_cases": [
            "查找函数调用",
            "查找变量使用",
            "影响分析"
        ],
        "when_to_use": "需要知道某个函数/变量在哪里被使用时",
        "when_not_to_use": "只是查看定义时，用 read_file",
        "typical_output": "200-1000 tokens，引用位置列表",
        "execution_time": "2-5秒"
    },
    
    # ========== Git工具 ==========
    "git_status": {
        "category": "git",
        "cost": "low",
        "value": "medium",
        "use_cases": [
            "查看修改状态",
            "查看未提交文件"
        ],
        "when_to_use": "需要知道哪些文件被修改了",
        "when_not_to_use": "需要具体修改内容时，用 git_diff",
        "typical_output": "100-500 tokens，文件状态列表",
        "execution_time": "<1秒"
    },
    
    "git_diff": {
        "category": "git",
        "cost": "low",
        "value": "high",
        "use_cases": [
            "查看具体修改",
            "审查变更",
            "对比差异"
        ],
        "when_to_use": "需要查看具体修改了什么内容时",
        "when_not_to_use": "只需要知道哪些文件变了，用 git_status",
        "typical_output": "200-2000 tokens，diff内容",
        "execution_time": "<1秒"
    },
}


def get_tools_by_category(category: str) -> List[str]:
    """获取某个分类下的所有工具"""
    return [
        name for name, meta in TOOL_METADATA.items()
        if meta.get("category") == category
    ]


def get_high_value_tools() -> List[str]:
    """获取高价值工具"""
    return [
        name for name, meta in TOOL_METADATA.items()
        if meta.get("value") == "high"
    ]


def get_low_cost_tools() -> List[str]:
    """获取低成本工具"""
    return [
        name for name, meta in TOOL_METADATA.items()
        if meta.get("cost") == "low"
    ]
