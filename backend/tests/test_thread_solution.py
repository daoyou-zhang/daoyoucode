"""测试线程方案解决事件循环冲突"""
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

async def async_task():
    """模拟异步任务"""
    print("异步任务开始")
    await asyncio.sleep(0.5)
    print("异步任务完成")
    return "成功"

def run_in_thread():
    """在新线程中运行异步代码"""
    print("在新线程中运行")
    
    # 创建新的事件循环
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    
    try:
        result = new_loop.run_until_complete(async_task())
        return result
    finally:
        new_loop.close()

def test_with_running_loop():
    """测试在有运行中的事件循环时使用线程方案"""
    print("=== 测试1: 模拟有运行中的事件循环 ===\n")
    
    # 检查是否有运行中的事件循环
    try:
        running_loop = asyncio.get_running_loop()
        print("检测到运行中的事件循环")
    except RuntimeError:
        print("没有运行中的事件循环")
    
    # 使用线程池执行
    print("使用线程方案...")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        result = future.result(timeout=5)
        print(f"结果: {result}")

def test_without_running_loop():
    """测试没有运行中的事件循环时直接执行"""
    print("\n=== 测试2: 没有运行中的事件循环 ===\n")
    
    # 检查是否有运行中的事件循环
    try:
        running_loop = asyncio.get_running_loop()
        print("检测到运行中的事件循环（不应该）")
    except RuntimeError:
        print("没有运行中的事件循环（正常）")
    
    # 直接执行
    print("直接执行...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(async_task())
        print(f"结果: {result}")
    finally:
        loop.close()

if __name__ == "__main__":
    test_with_running_loop()
    test_without_running_loop()
    print("\n=== 测试完成 ===")
