"""
测试智能 Diff 编辑工具的流式显示功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.diff_tools import IntelligentDiffEditTool
from daoyoucode.agents.tools.base import ToolContext, EditEvent


async def test_streaming_diff_edit():
    """测试流式 Diff 编辑"""
    
    print("=" * 60)
    print("测试：智能 Diff 编辑工具 - 流式显示")
    print("=" * 60)
    
    # 创建测试文件
    test_file = Path(__file__).parent / "test_streaming_diff_target.py"
    
    original_content = '''def calculate_sum(numbers):
    """计算数字列表的总和"""
    total = 0
    for num in numbers:
        total += num
    return total


def calculate_average(numbers):
    """计算平均值"""
    if not numbers:
        return 0
    return calculate_sum(numbers) / len(numbers)


class Calculator:
    """简单计算器"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(('subtract', a, b, result))
        return result
'''
    
    test_file.write_text(original_content, encoding='utf-8')
    print(f"✅ 创建测试文件: {test_file.name}\n")
    
    # 创建工具
    tool = IntelligentDiffEditTool()
    tool.set_context(ToolContext(repo_path=Path(__file__).parent))
    
    # 测试1: 流式编辑 - 简单函数替换
    print("\n" + "=" * 60)
    print("测试1: 流式编辑 - 简单函数替换")
    print("=" * 60)
    
    search_block = """def calculate_sum(numbers):
    \"\"\"计算数字列表的总和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total"""
    
    replace_block = """def calculate_sum(numbers):
    \"\"\"计算数字列表的总和（优化版）\"\"\"
    return sum(numbers)"""
    
    event_count = 0
    async for event in tool.execute_streaming(
        file_path=test_file.name,
        search_block=search_block,
        replace_block=replace_block,
        fuzzy_match=True,
        similarity_threshold=0.8,
        verify=False  # 跳过 LSP 验证以加快测试
    ):
        event_count += 1
        
        # 显示事件
        if event.type == EditEvent.EDIT_START:
            print(f"📝 开始编辑: {event.data.get('file_path')}")
        
        elif event.type == EditEvent.EDIT_ANALYZING:
            status = event.data.get('status')
            if 'size' in event.data:
                print(f"🔍 分析: {status} | {event.data.get('lines')} 行, {event.data.get('size')} 字节")
            else:
                print(f"🔍 分析: {status}")
        
        elif event.type == EditEvent.EDIT_PLANNING:
            status = event.data.get('status')
            if 'similarity' in event.data:
                similarity = event.data.get('similarity', 0)
                start_line = event.data.get('match_start_line', 0)
                end_line = event.data.get('match_end_line', 0)
                print(f"🎯 匹配: {status} | 相似度 {similarity:.1%} | 行 {start_line}-{end_line}")
            else:
                print(f"🔍 规划: {status}")
        
        elif event.type == EditEvent.EDIT_APPLYING:
            status = event.data.get('status')
            print(f"✍️  应用: {status}")
        
        elif event.type == EditEvent.EDIT_BLOCK:
            added = event.data.get('added_lines', 0)
            removed = event.data.get('removed_lines', 0)
            print(f"📊 变更: +{added} -{removed} 行")
        
        elif event.type == EditEvent.EDIT_VERIFYING:
            status = event.data.get('status')
            if 'errors' in event.data:
                errors = event.data.get('errors', 0)
                warnings = event.data.get('warnings', 0)
                print(f"🔍 验证: {status} | {errors} 错误, {warnings} 警告")
            else:
                print(f"🔍 验证: {status}")
        
        elif event.type == EditEvent.EDIT_COMPLETE:
            similarity = event.data.get('similarity', 0)
            added = event.data.get('added_lines', 0)
            removed = event.data.get('removed_lines', 0)
            print(f"✅ 完成: {event.data.get('file_path')} | 相似度 {similarity:.1%} | +{added} -{removed}")
        
        elif event.type == EditEvent.EDIT_ERROR:
            print(f"❌ 错误: {event.data.get('error')}")
    
    print(f"\n收集了 {event_count} 个编辑事件")
    
    # 验证结果
    new_content = test_file.read_text(encoding='utf-8')
    if 'return sum(numbers)' in new_content:
        print("✅ 验证通过: 文件已正确修改")
    else:
        print("❌ 验证失败: 文件未正确修改")
    
    # 测试2: 流式编辑 - 类方法替换
    print("\n" + "=" * 60)
    print("测试2: 流式编辑 - 类方法替换")
    print("=" * 60)
    
    search_block2 = """    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result"""
    
    replace_block2 = """    def add(self, a, b):
        \"\"\"加法运算\"\"\"
        result = a + b
        self.history.append(('add', a, b, result))
        return result"""
    
    event_count2 = 0
    async for event in tool.execute_streaming(
        file_path=test_file.name,
        search_block=search_block2,
        replace_block=replace_block2,
        fuzzy_match=True,
        similarity_threshold=0.8,
        verify=False
    ):
        event_count2 += 1
        
        # 只显示关键事件
        if event.type == EditEvent.EDIT_START:
            print(f"📝 开始: {event.data.get('file_path')}")
        elif event.type == EditEvent.EDIT_PLANNING and 'similarity' in event.data:
            similarity = event.data.get('similarity', 0)
            print(f"🎯 匹配: 相似度 {similarity:.1%}")
        elif event.type == EditEvent.EDIT_COMPLETE:
            print(f"✅ 完成: {event.data.get('file_path')}")
        elif event.type == EditEvent.EDIT_ERROR:
            print(f"❌ 错误: {event.data.get('error')}")
    
    print(f"\n收集了 {event_count2} 个编辑事件")
    
    # 验证结果
    new_content2 = test_file.read_text(encoding='utf-8')
    if '"""加法运算"""' in new_content2:
        print("✅ 验证通过: 类方法已正确修改")
    else:
        print("❌ 验证失败: 类方法未正确修改")
    
    # 清理
    test_file.unlink()
    print(f"\n🧹 清理测试文件")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_streaming_diff_edit())
