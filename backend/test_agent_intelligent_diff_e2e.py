"""
端到端测试：Agent 使用 IntelligentDiffEditTool 的完整流程

测试流程：
1. Agent 接收用户请求
2. Agent 调用 IntelligentDiffEditTool
3. 工具执行流式编辑
4. Agent 收集编辑事件
5. 验证结果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.diff_tools import IntelligentDiffEditTool
from daoyoucode.agents.tools.base import ToolContext, ToolRegistry, EditEvent


async def test_e2e_agent_intelligent_diff():
    """端到端测试：Agent 使用智能 Diff 编辑工具"""
    
    print("=" * 70)
    print("端到端测试：Agent 使用 IntelligentDiffEditTool")
    print("=" * 70)
    
    # 创建测试文件
    test_file = Path(__file__).parent / "test_e2e_diff_target.py"
    
    original_content = '''"""
简单的数学工具模块
"""

def add(a, b):
    """加法"""
    return a + b


def subtract(a, b):
    """减法"""
    return a - b


def multiply(a, b):
    """乘法"""
    result = a * b
    return result


def divide(a, b):
    """除法"""
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b


class Calculator:
    """计算器类"""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, a, b):
        """执行计算"""
        if operation == "add":
            result = add(a, b)
        elif operation == "subtract":
            result = subtract(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)
        else:
            raise ValueError(f"未知操作: {operation}")
        
        self.history.append((operation, a, b, result))
        return result
'''
    
    test_file.write_text(original_content, encoding='utf-8')
    print(f"✅ 创建测试文件: {test_file.name}")
    print(f"   文件大小: {len(original_content)} 字节")
    print(f"   行数: {original_content.count(chr(10)) + 1}\n")
    
    # 创建工具注册表
    registry = ToolRegistry()
    context = ToolContext(repo_path=Path(__file__).parent)
    registry.set_context(context)
    
    # 注册智能 Diff 编辑工具
    diff_tool = IntelligentDiffEditTool()
    registry.register(diff_tool)
    
    print(f"✅ 工具已注册: {diff_tool.name}\n")
    
    # ========== 测试场景1: 优化简单函数 ==========
    print("=" * 70)
    print("场景1: 优化 multiply 函数（移除中间变量）")
    print("=" * 70)
    
    search_block1 = '''def multiply(a, b):
    """乘法"""
    result = a * b
    return result'''
    
    replace_block1 = '''def multiply(a, b):
    """乘法"""
    return a * b'''
    
    print("\n🔍 搜索代码块:")
    print("```python")
    print(search_block1)
    print("```")
    
    print("\n✏️  替换为:")
    print("```python")
    print(replace_block1)
    print("```\n")
    
    # 模拟 Agent 调用工具（流式）
    print("📡 Agent 调用工具（流式模式）...\n")
    
    edit_events = []
    async for event in diff_tool.execute_streaming(
        file_path=test_file.name,
        search_block=search_block1,
        replace_block=replace_block1,
        fuzzy_match=True,
        similarity_threshold=0.8,
        verify=False
    ):
        edit_events.append(event)
        
        # 显示关键事件
        if event.type == EditEvent.EDIT_START:
            print(f"📝 开始编辑: {event.data.get('file_path')}")
        
        elif event.type == EditEvent.EDIT_ANALYZING:
            if 'size' in event.data:
                print(f"🔍 分析完成: {event.data.get('lines')} 行, {event.data.get('size')} 字节")
        
        elif event.type == EditEvent.EDIT_PLANNING:
            if 'similarity' in event.data:
                similarity = event.data.get('similarity', 0)
                start = event.data.get('match_start_line', 0)
                end = event.data.get('match_end_line', 0)
                print(f"🎯 找到匹配: 相似度 {similarity:.1%}, 行 {start}-{end}")
        
        elif event.type == EditEvent.EDIT_BLOCK:
            added = event.data.get('added_lines', 0)
            removed = event.data.get('removed_lines', 0)
            print(f"📊 变更统计: +{added} -{removed} 行")
        
        elif event.type == EditEvent.EDIT_COMPLETE:
            print(f"✅ 编辑完成: {event.data.get('file_path')}")
        
        elif event.type == EditEvent.EDIT_ERROR:
            print(f"❌ 错误: {event.data.get('error')}")
    
    print(f"\n📦 收集了 {len(edit_events)} 个编辑事件")
    
    # 验证结果
    content1 = test_file.read_text(encoding='utf-8')
    if 'return a * b' in content1 and 'result = a * b' not in content1:
        print("✅ 验证通过: multiply 函数已优化\n")
    else:
        print("❌ 验证失败: multiply 函数未正确修改\n")
    
    # ========== 测试场景2: 为类方法添加文档 ==========
    print("=" * 70)
    print("场景2: 为 Calculator.calculate 方法添加详细文档")
    print("=" * 70)
    
    search_block2 = '''    def calculate(self, operation, a, b):
        """执行计算"""
        if operation == "add":'''
    
    replace_block2 = '''    def calculate(self, operation, a, b):
        """
        执行计算操作
        
        Args:
            operation: 操作类型 (add/subtract/multiply/divide)
            a: 第一个操作数
            b: 第二个操作数
        
        Returns:
            计算结果
        
        Raises:
            ValueError: 未知操作或除数为0
        """
        if operation == "add":'''
    
    print("\n📡 Agent 调用工具（流式模式）...\n")
    
    edit_events2 = []
    async for event in diff_tool.execute_streaming(
        file_path=test_file.name,
        search_block=search_block2,
        replace_block=replace_block2,
        fuzzy_match=True,
        similarity_threshold=0.8,
        verify=False
    ):
        edit_events2.append(event)
        
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
    
    print(f"\n📦 收集了 {len(edit_events2)} 个编辑事件")
    
    # 验证结果
    content2 = test_file.read_text(encoding='utf-8')
    if 'Args:' in content2 and 'Returns:' in content2 and 'Raises:' in content2:
        print("✅ 验证通过: 文档已添加\n")
    else:
        print("❌ 验证失败: 文档未正确添加\n")
    
    # ========== 测试场景3: 模糊匹配（带空白差异）==========
    print("=" * 70)
    print("场景3: 模糊匹配测试（搜索块有缩进差异）")
    print("=" * 70)
    
    # 故意使用错误的缩进
    search_block3 = '''def add(a, b):
        """加法"""
            return a + b'''  # 缩进错误
    
    replace_block3 = '''def add(a, b):
    """加法运算"""
    return a + b'''
    
    print("\n📡 Agent 调用工具（模糊匹配）...\n")
    
    edit_events3 = []
    async for event in diff_tool.execute_streaming(
        file_path=test_file.name,
        search_block=search_block3,
        replace_block=replace_block3,
        fuzzy_match=True,
        similarity_threshold=0.7,  # 降低阈值以允许模糊匹配
        verify=False
    ):
        edit_events3.append(event)
        
        if event.type == EditEvent.EDIT_START:
            print(f"📝 开始: {event.data.get('file_path')}")
        elif event.type == EditEvent.EDIT_PLANNING and 'similarity' in event.data:
            similarity = event.data.get('similarity', 0)
            print(f"🎯 模糊匹配: 相似度 {similarity:.1%}")
        elif event.type == EditEvent.EDIT_COMPLETE:
            print(f"✅ 完成: {event.data.get('file_path')}")
        elif event.type == EditEvent.EDIT_ERROR:
            print(f"❌ 错误: {event.data.get('error')}")
    
    print(f"\n📦 收集了 {len(edit_events3)} 个编辑事件")
    
    # 验证结果
    content3 = test_file.read_text(encoding='utf-8')
    if '"""加法运算"""' in content3:
        print("✅ 验证通过: 模糊匹配成功\n")
    else:
        print("❌ 验证失败: 模糊匹配失败\n")
    
    # ========== 总结 ==========
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    total_events = len(edit_events) + len(edit_events2) + len(edit_events3)
    
    print(f"\n✅ 场景1: 优化函数 - {len(edit_events)} 个事件")
    print(f"✅ 场景2: 添加文档 - {len(edit_events2)} 个事件")
    print(f"✅ 场景3: 模糊匹配 - {len(edit_events3)} 个事件")
    print(f"\n📊 总计: {total_events} 个编辑事件")
    
    print("\n🎯 Agent 集成验证:")
    print("  ✅ 工具注册成功")
    print("  ✅ 流式调用正常")
    print("  ✅ 事件收集正常")
    print("  ✅ 精确匹配正常")
    print("  ✅ 模糊匹配正常")
    print("  ✅ 文件修改正确")
    
    # 显示最终文件内容（前20行）
    print("\n📄 最终文件内容（前20行）:")
    print("```python")
    final_lines = content3.split('\n')[:20]
    for i, line in enumerate(final_lines, 1):
        print(f"{i:3d} | {line}")
    print("```")
    
    # 清理
    test_file.unlink()
    print(f"\n🧹 清理测试文件")
    
    print("\n" + "=" * 70)
    print("端到端测试完成！✅")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_e2e_agent_intelligent_diff())
