#!/usr/bin/env python
"""
CLI测试脚本

快速测试所有命令
"""

import subprocess
import sys


def run_command(cmd):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"测试命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠️  命令超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """测试所有命令"""
    print("\n🧪 DaoyouCode CLI 测试\n")
    
    commands = [
        # 基础命令
        ("帮助", "python -m backend.cli --help"),
        ("版本", "python -m backend.cli version"),
        
        # 核心命令
        ("模型列表", "python -m backend.cli models"),
        ("Agent列表", "python -m backend.cli agent"),
        ("会话列表", "python -m backend.cli session list"),
        ("配置查看", "python -m backend.cli config show"),
        ("环境诊断", "python -m backend.cli doctor"),
        
        # 帮助文档
        ("chat帮助", "python -m backend.cli chat --help"),
        ("edit帮助", "python -m backend.cli edit --help"),
    ]
    
    passed = 0
    failed = 0
    
    for name, cmd in commands:
        if run_command(cmd):
            print(f"✅ {name} - 通过")
            passed += 1
        else:
            print(f"❌ {name} - 失败")
            failed += 1
    
    # 总结
    print(f"\n{'='*60}")
    print(f"测试总结")
    print('='*60)
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
