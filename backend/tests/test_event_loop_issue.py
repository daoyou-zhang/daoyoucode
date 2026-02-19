"""测试事件循环问题"""
import asyncio
import sys

async def async_task():
    """模拟异步任务"""
    await asyncio.sleep(0.1)
    return "任务完成"

def sync_wrapper_bad():
    """错误的同步包装（可能导致问题）"""
    print("方法1: 使用get_event_loop + run_until_complete")
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(async_task())
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

def sync_wrapper_good():
    """正确的同步包装"""
    print("\n方法2: 使用asyncio.run")
    try:
        result = asyncio.run(async_task())
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

def sync_wrapper_better():
    """更好的同步包装（兼容已有循环）"""
    print("\n方法3: 检查并创建新循环")
    try:
        try:
            loop = asyncio.get_running_loop()
            print("检测到运行中的循环，这会导致问题！")
        except RuntimeError:
            print("没有运行中的循环，安全")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_task())
            print(f"结果: {result}")
        finally:
            loop.close()
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    print("=== 测试事件循环问题 ===\n")
    
    sync_wrapper_bad()
    sync_wrapper_good()
    sync_wrapper_better()
    
    print("\n=== 测试完成 ===")
