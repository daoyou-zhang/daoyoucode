"""
测试CLI帮助系统

验证所有帮助命令都能正常工作
"""

import subprocess
import sys
import os

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        encoding='utf-8'
    )
    return result.returncode, result.stdout, result.stderr


def test_help_commands():
    """测试所有--help命令"""
    commands = [
        "python daoyoucode.py --help",
        "python daoyoucode.py chat --help",
        "python daoyoucode.py agent --help",
        "python daoyoucode.py skills --help",
        "python daoyoucode.py examples --help",
    ]
    
    print("=" * 60)
    print("测试 --help 命令")
    print("=" * 60)
    
    for cmd in commands:
        print(f"\n测试: {cmd}")
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print("✓ 成功")
            # 检查是否包含关键内容
            if "Usage:" in stdout and "Options" in stdout:
                print("✓ 输出格式正确")
            else:
                print("✗ 输出格式不正确")
        else:
            print(f"✗ 失败: {stderr}")


def test_examples_commands():
    """测试所有--examples命令"""
    commands = [
        "python daoyoucode.py examples",
        "python daoyoucode.py examples chat",
        "python daoyoucode.py examples agent",
        "python daoyoucode.py examples skills",
        "python daoyoucode.py chat --examples",
        "python daoyoucode.py agent --examples",
        "python daoyoucode.py skills --examples",
    ]
    
    print("\n" + "=" * 60)
    print("测试 examples 命令")
    print("=" * 60)
    
    for cmd in commands:
        print(f"\n测试: {cmd}")
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print("✓ 成功")
            # 检查是否包含示例内容
            if "示例" in stdout or "用法" in stdout:
                print("✓ 输出包含示例")
            else:
                print("✗ 输出不包含示例")
        else:
            print(f"✗ 失败: {stderr}")


def test_help_content():
    """测试帮助内容的完整性"""
    print("\n" + "=" * 60)
    print("测试帮助内容完整性")
    print("=" * 60)
    
    # 测试chat --help
    print("\n测试: chat --help 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py chat --help")
    
    required_content = [
        "启动交互式对话",
        "--model",
        "--skill",
        "--repo",
        "--examples",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")
    
    # 测试agent --help
    print("\n测试: agent --help 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py agent --help")
    
    required_content = [
        "Agent管理",
        "--tools",
        "--examples",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")
    
    # 测试skills --help
    print("\n测试: skills --help 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py skills --help")
    
    required_content = [
        "Skill和编排器管理",
        "--orchestrators",
        "--examples",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")


def test_examples_content():
    """测试示例内容的完整性"""
    print("\n" + "=" * 60)
    print("测试示例内容完整性")
    print("=" * 60)
    
    # 测试chat --examples
    print("\n测试: chat --examples 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py chat --examples")
    
    required_content = [
        "基本用法",
        "指定Skill",
        "指定模型",
        "加载文件",
        "交互式命令",
        "推荐Skill",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")
    
    # 测试agent --examples
    print("\n测试: agent --examples 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py agent --examples")
    
    required_content = [
        "基本用法",
        "查看Agent详情",
        "查看Agent工具",
        "可用Agent",
        "Agent与Skill的关系",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")
    
    # 测试skills --examples
    print("\n测试: skills --examples 内容")
    returncode, stdout, stderr = run_command("python daoyoucode.py skills --examples")
    
    required_content = [
        "基本用法",
        "查看Skill详情",
        "查看编排器",
        "推荐Skill",
        "编排器类型",
        "Multi-Agent协作模式",
    ]
    
    for content in required_content:
        if content in stdout:
            print(f"✓ 包含: {content}")
        else:
            print(f"✗ 缺失: {content}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("CLI帮助系统测试")
    print("=" * 60)
    
    test_help_commands()
    test_examples_commands()
    test_help_content()
    test_examples_content()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
