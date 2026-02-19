"""测试CLI输出问题"""
import sys
import os

# 设置环境变量，禁用输出缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

print("=== 测试开始 ===")
sys.stdout.flush()

# 测试1：直接print
print("测试1: 直接print")
sys.stdout.flush()

# 测试2：sys.stdout.write
sys.stdout.write("测试2: sys.stdout.write\n")
sys.stdout.flush()

# 测试3：中文输出
try:
    print("测试3: 中文输出 - 你好")
    sys.stdout.flush()
except Exception as e:
    sys.stderr.write(f"中文输出失败: {e}\n")
    sys.stderr.flush()

# 测试4：模拟AI响应
ai_response = "道友你好！有什么我可以帮你的？"
try:
    sys.stdout.write("\nAI > ")
    sys.stdout.flush()
    sys.stdout.write(ai_response + "\n")
    sys.stdout.flush()
    print("测试4: 模拟AI响应成功")
except Exception as e:
    sys.stderr.write(f"AI响应输出失败: {e}\n")
    sys.stderr.flush()

print("=== 测试完成 ===")
sys.stdout.flush()
