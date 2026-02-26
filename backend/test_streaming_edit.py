"""
测试流式编辑功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.file_tools import WriteFileTool
from daoyoucode.agents.tools.base import ToolContext, EditEvent


async def test_streaming_write():
    """测试流式写入文件"""
    
    print("=" * 80)
    print("测试流式写入文件")
    print("=" * 80)
    
    # 创建工具
    tool = WriteFileTool()
    tool.set_context(ToolContext(repo_path=Path.cwd()))
    
    # 准备测试内容
    test_content = """# 测试文件

def hello():
    print("Hello, World!")

def add(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def subtract(self, x):
        self.result -= x
        return self.result

if __name__ == "__main__":
    hello()
    print(add(1, 2))
"""
    
    # 流式写入
    print("\n开始流式写入...\n")
    
    async for event in tool.execute_streaming(
        file_path="test_streaming_output.py",
        content=test_content,
        verify=False  # 暂时不验证，避免LSP问题
    ):
        if event.type == EditEvent.EDIT_START:
            print(f"📝 开始编辑: {event.data['file_path']}")
            print(f"   总行数: {event.data['total_lines']}, 大小: {event.data['size']} 字节")
        
        elif event.type == EditEvent.EDIT_ANALYZING:
            print(f"🔍 分析文件: {event.data['file_path']}")
            print(f"   文件存在: {event.data['exists']}, 是代码: {event.data['is_code']}")
        
        elif event.type == EditEvent.EDIT_LINE:
            line_num = event.data['line_number']
            progress = event.data['progress']
            content = event.data['content']
            
            # 显示进度条
            bar_width = 40
            filled = int(bar_width * progress)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            # 只显示部分行（避免刷屏）
            if line_num % 5 == 0 or line_num == 1:
                print(f"\r✍️  [{bar}] {progress:>6.1%} | Line {line_num:>3}: {content[:50]}", end="")
        
        elif event.type == EditEvent.EDIT_VERIFYING:
            print(f"\n🔍 验证代码: {event.data['file_path']}")
        
        elif event.type == EditEvent.EDIT_COMPLETE:
            print(f"\n✅ 编辑完成!")
            print(f"   文件: {event.data['file_path']}")
            print(f"   行数: {event.data['lines']}, 大小: {event.data['size']} 字节")
            if event.data.get('verified'):
                print(f"   ✓ LSP验证通过")
            if event.data.get('warnings'):
                print(f"   ⚠️  {event.data['warning_count']} 个警告:")
                for warning in event.data['warnings']:
                    print(f"      - {warning}")
        
        elif event.type == EditEvent.EDIT_ERROR:
            print(f"\n❌ 编辑失败!")
            print(f"   错误: {event.data.get('error', 'Unknown')}")
            if event.data.get('errors'):
                print(f"   {event.data['error_count']} 个错误:")
                for error in event.data['errors']:
                    print(f"      - {error}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_streaming_write())
