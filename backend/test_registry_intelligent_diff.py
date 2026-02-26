"""
测试工具注册表是否包含智能 Diff 编辑工具
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.registry import get_tool_registry


def test_registry():
    """测试工具注册表"""
    
    print("=" * 60)
    print("测试：工具注册表")
    print("=" * 60)
    
    # 获取工具注册表
    registry = get_tool_registry()
    
    # 列出所有工具
    tools = registry.list_tools()
    print(f"\n已注册 {len(tools)} 个工具:\n")
    
    # 按类别分组显示
    diff_tools = [t for t in tools if 'diff' in t.lower() or 'replace' in t.lower() or 'patch' in t.lower()]
    
    print("Diff 编辑工具:")
    for tool in sorted(diff_tools):
        print(f"  • {tool}")
    
    # 检查智能 Diff 编辑工具
    print("\n" + "=" * 60)
    print("检查智能 Diff 编辑工具")
    print("=" * 60)
    
    if 'intelligent_diff_edit' in tools:
        print("✅ IntelligentDiffEditTool 已注册")
        
        # 获取工具实例
        tool = registry.get_tool('intelligent_diff_edit')
        print(f"   名称: {tool.name}")
        print(f"   描述: {tool.description}")
        print(f"   支持流式: {tool.supports_streaming()}")
    else:
        print("❌ IntelligentDiffEditTool 未注册")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_registry()
