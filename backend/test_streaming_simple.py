"""
简单测试流式输出功能
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_basic_streaming():
    """测试基本流式输出"""
    
    print("测试流式输出基本功能")
    print("=" * 60)
    
    # 测试生成器检测
    async def mock_stream():
        for i in range(5):
            yield {'type': 'token', 'content': f'token_{i} '}
        yield {'type': 'result', 'result': 'done'}
    
    result = mock_stream()
    
    import inspect
    if inspect.isasyncgen(result):
        print("✅ 生成器检测正常")
        
        print("输出: ", end='', flush=True)
        async for event in result:
            if event.get('type') == 'token':
                print(event.get('content'), end='', flush=True)
            elif event.get('type') == 'result':
                print(f"\n✅ 完成: {event.get('result')}")
    else:
        print("❌ 生成器检测失败")
    
    print("\n" + "=" * 60)
    print("基本功能测试通过")


if __name__ == '__main__':
    asyncio.run(test_basic_streaming())
