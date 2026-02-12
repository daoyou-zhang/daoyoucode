"""测试repo_map工具"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools import get_tool_registry

async def test_repo_map():
    print("="*60)
    print("测试repo_map工具")
    print("="*60)
    
    # 获取工具
    tool_registry = get_tool_registry()
    tool = tool_registry.get_tool("repo_map")
    
    if not tool:
        print("❌ repo_map工具未找到")
        return False
    
    print(f"\n✓ 找到repo_map工具")
    print(f"  • 描述: {tool.description}")
    
    # 测试执行
    print(f"\n执行repo_map(repo_path='.')...")
    try:
        result = await tool.execute(repo_path=".", max_tokens=500)
        
        print(f"\n✓ 执行完成")
        print(f"  • 成功: {result.success}")
        if result.success:
            content_preview = str(result.content)[:200]
            print(f"  • 内容预览: {content_preview}...")
        else:
            print(f"  • 错误: {result.error}")
        
        return result.success
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_repo_map())
    print("\n" + "="*60)
    if success:
        print("✅ repo_map工具测试通过")
    else:
        print("❌ repo_map工具测试失败")
    print("="*60)
