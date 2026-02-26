"""
测试批量文件读写工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.tools.file_tools import BatchReadFilesTool, BatchWriteFilesTool
from daoyoucode.agents.tools.base import ToolContext


async def test_batch_tools():
    """测试批量文件工具"""
    
    print("=" * 70)
    print("测试：批量文件读写工具")
    print("=" * 70)
    
    # 创建工具
    batch_read_tool = BatchReadFilesTool()
    batch_write_tool = BatchWriteFilesTool()
    
    # 设置上下文
    context = ToolContext(repo_path=Path(__file__).parent)
    batch_read_tool.set_context(context)
    batch_write_tool.set_context(context)
    
    # ========== 测试1: 批量写入文件 ==========
    print("\n" + "=" * 70)
    print("测试1: 批量写入10个文件")
    print("=" * 70)
    
    files_to_write = []
    for i in range(1, 11):
        files_to_write.append({
            'path': f'test_batch_file_{i}.py',
            'content': f'''"""
测试文件 {i}
"""

def function_{i}():
    """函数 {i}"""
    return {i}


class Class{i}:
    """类 {i}"""
    
    def method_{i}(self):
        """方法 {i}"""
        return {i}
'''
        })
    
    print(f"\n准备写入 {len(files_to_write)} 个文件...")
    
    # 非流式写入
    result = await batch_write_tool.execute(
        files=files_to_write,
        verify=False  # 跳过 LSP 验证以加快测试
    )
    
    if result.success:
        print(f"✅ 批量写入成功")
        print(f"   成功: {result.metadata['success_count']} 个")
        print(f"   失败: {result.metadata['error_count']} 个")
    else:
        print(f"❌ 批量写入失败: {result.error}")
    
    # ========== 测试2: 批量读取文件 ==========
    print("\n" + "=" * 70)
    print("测试2: 批量读取10个文件")
    print("=" * 70)
    
    files_to_read = [f'test_batch_file_{i}.py' for i in range(1, 11)]
    
    print(f"\n准备读取 {len(files_to_read)} 个文件...")
    
    result = await batch_read_tool.execute(file_paths=files_to_read)
    
    if result.success:
        print(f"✅ 批量读取成功")
        print(f"   成功: {result.metadata['success_count']} 个")
        print(f"   失败: {result.metadata['error_count']} 个")
        
        # 显示前3个文件的内容预览
        print("\n📄 前3个文件内容预览:")
        for i, (file_path, content) in enumerate(result.metadata['results'].items(), 1):
            if i > 3:
                break
            lines = content.count('\n') + 1
            print(f"\n  {i}. {file_path} ({lines} 行)")
            print(f"     前3行: {chr(10).join(content.split(chr(10))[:3])}")
    else:
        print(f"❌ 批量读取失败: {result.error}")
    
    # ========== 测试3: 流式批量写入 ==========
    print("\n" + "=" * 70)
    print("测试3: 流式批量写入5个文件")
    print("=" * 70)
    
    files_to_write_stream = []
    for i in range(11, 16):
        files_to_write_stream.append({
            'path': f'test_batch_file_{i}.py',
            'content': f'# 测试文件 {i}\nprint("Hello from file {i}")\n'
        })
    
    print(f"\n准备流式写入 {len(files_to_write_stream)} 个文件...")
    
    event_count = 0
    async for event in batch_write_tool.execute_streaming(
        files=files_to_write_stream,
        verify=False
    ):
        event_count += 1
        
        if event.type == 'edit_start':
            total = event.data.get('total_files', 0)
            print(f"📝 开始批量写入: {total} 个文件")
        
        elif event.type == 'edit_applying':
            current = event.data.get('current', 0)
            total = event.data.get('total', 0)
            file_path = event.data.get('file_path', '')
            progress = event.data.get('progress', 0)
            print(f"✍️  [{current}/{total}] {progress:.0%} - {file_path}")
        
        elif event.type == 'edit_line':
            file_path = event.data.get('file_path', '')
            status = event.data.get('status', '')
            if status == 'success':
                print(f"  ✅ {file_path}")
        
        elif event.type == 'edit_complete':
            success = event.data.get('success_count', 0)
            errors = event.data.get('error_count', 0)
            print(f"\n✅ 批量写入完成: {success} 成功, {errors} 失败")
        
        elif event.type == 'edit_error':
            error = event.data.get('error', '')
            print(f"❌ 错误: {error}")
    
    print(f"\n收集了 {event_count} 个编辑事件")
    
    # ========== 清理测试文件 ==========
    print("\n" + "=" * 70)
    print("清理测试文件")
    print("=" * 70)
    
    for i in range(1, 16):
        test_file = Path(__file__).parent / f'test_batch_file_{i}.py'
        if test_file.exists():
            test_file.unlink()
    
    print("✅ 清理完成")
    
    # ========== 性能对比 ==========
    print("\n" + "=" * 70)
    print("性能对比")
    print("=" * 70)
    
    import time
    
    # 测试单个文件写入（10次）
    print("\n测试: 单个文件写入 10 次")
    start = time.time()
    for i in range(1, 11):
        with open(Path(__file__).parent / f'test_single_{i}.py', 'w') as f:
            f.write(f'# Test {i}\n')
    single_time = time.time() - start
    print(f"耗时: {single_time:.3f} 秒")
    
    # 测试批量写入（10个文件）
    print("\n测试: 批量写入 10 个文件")
    start = time.time()
    files = [{'path': f'test_batch_{i}.py', 'content': f'# Test {i}\n'} for i in range(1, 11)]
    await batch_write_tool.execute(files=files, verify=False)
    batch_time = time.time() - start
    print(f"耗时: {batch_time:.3f} 秒")
    
    speedup = single_time / batch_time if batch_time > 0 else 0
    print(f"\n⚡ 加速比: {speedup:.2f}x")
    
    # 清理
    for i in range(1, 11):
        (Path(__file__).parent / f'test_single_{i}.py').unlink(missing_ok=True)
        (Path(__file__).parent / f'test_batch_{i}.py').unlink(missing_ok=True)
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_batch_tools())
