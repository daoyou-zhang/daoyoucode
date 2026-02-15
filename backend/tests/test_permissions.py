#!/usr/bin/env python3
"""
测试权限系统
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.core.permission import (
    get_permission_manager,
    apply_default_permissions,
    apply_strict_permissions,
    PermissionAction,
)
from daoyoucode.agents.core.decorators import require_permission


async def test_basic_permissions():
    """测试基本权限功能"""
    print("=" * 60)
    print("测试1: 基本权限功能")
    print("=" * 60)
    
    manager = get_permission_manager()
    manager.clear_rules()
    
    # 添加规则
    manager.add_rule("read", "*", "allow")
    manager.add_rule("read", "*.env", "deny")
    manager.add_rule("write", "*.py", "allow")
    manager.add_rule("write", "*.txt", "allow")
    manager.add_rule("write", "*.env", "deny")
    
    # 测试读取权限
    print("\n1. 测试读取权限...")
    
    allowed = await manager.check_permission("read", "test.py")
    print(f"   read test.py: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert allowed
    
    allowed = await manager.check_permission("read", ".env")
    print(f"   read .env: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert not allowed
    
    # 测试写入权限
    print("\n2. 测试写入权限...")
    
    allowed = await manager.check_permission("write", "test.py")
    print(f"   write test.py: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert allowed
    
    allowed = await manager.check_permission("write", ".env")
    print(f"   write .env: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert not allowed
    
    print("\n✅ 基本权限功能测试通过")


async def test_default_permissions():
    """测试默认权限配置"""
    print("\n" + "=" * 60)
    print("测试2: 默认权限配置")
    print("=" * 60)
    
    apply_default_permissions()
    manager = get_permission_manager()
    
    # 测试各种文件类型
    test_cases = [
        ("read", "test.py", True),
        ("read", "test.txt", True),
        ("read", ".env", False),  # ask -> 没有回调 -> deny
        ("write", "test.py", True),
        ("write", "test.md", True),
        ("write", ".env", False),
        ("write", "secret.key", False),
        ("execute", "script.sh", False),  # ask -> deny
        ("delete", "test.py", False),  # ask -> deny
    ]
    
    print("\n测试默认权限:")
    for action, path, expected in test_cases:
        allowed = await manager.check_permission(action, path)
        status = "✅" if allowed == expected else "❌"
        print(f"   {status} {action} {path}: {allowed}")
        assert allowed == expected, f"Expected {expected}, got {allowed}"
    
    print("\n✅ 默认权限配置测试通过")


async def test_strict_permissions():
    """测试严格权限配置"""
    print("\n" + "=" * 60)
    print("测试3: 严格权限配置")
    print("=" * 60)
    
    apply_strict_permissions()
    manager = get_permission_manager()
    
    # 测试各种文件类型
    test_cases = [
        ("read", "test.py", True),
        ("read", "test.md", True),
        ("read", "test.txt", True),
        ("read", "unknown.xyz", False),  # ask -> deny
        ("write", "test.md", True),
        ("write", "test.py", False),  # ask -> deny
        ("write", "test.txt", False),
        ("execute", "script.sh", False),
        ("delete", "test.py", False),
    ]
    
    print("\n测试严格权限:")
    for action, path, expected in test_cases:
        allowed = await manager.check_permission(action, path)
        status = "✅" if allowed == expected else "❌"
        print(f"   {status} {action} {path}: {allowed}")
        assert allowed == expected, f"Expected {expected}, got {allowed}"
    
    print("\n✅ 严格权限配置测试通过")


async def test_permission_decorator():
    """测试权限装饰器"""
    print("\n" + "=" * 60)
    print("测试4: 权限装饰器")
    print("=" * 60)
    
    apply_default_permissions()
    
    # 定义测试函数
    @require_permission('write', 'file_path')
    async def write_file(file_path: str, content: str):
        return f"写入 {file_path}: {content}"
    
    # 测试允许的操作
    print("\n1. 测试允许的操作...")
    try:
        result = await write_file("test.py", "print('hello')")
        print(f"   ✅ 成功: {result}")
    except PermissionError as e:
        print(f"   ❌ 失败: {e}")
        assert False
    
    # 测试拒绝的操作
    print("\n2. 测试拒绝的操作...")
    try:
        result = await write_file(".env", "SECRET=123")
        print(f"   ❌ 应该被拒绝")
        assert False
    except PermissionError as e:
        print(f"   ✅ 正确拒绝: {e}")
    
    print("\n✅ 权限装饰器测试通过")


async def test_ask_callback():
    """测试询问回调"""
    print("\n" + "=" * 60)
    print("测试5: 询问回调")
    print("=" * 60)
    
    manager = get_permission_manager()
    manager.clear_rules()
    
    # 添加ask规则
    manager.add_rule("execute", "*.sh", "ask")
    
    # 设置回调（自动允许）
    async def auto_allow(action, path, agent_name):
        print(f"   询问: {action} {path} (agent: {agent_name})")
        return True
    
    manager.set_ask_callback(auto_allow)
    
    # 测试
    print("\n1. 测试自动允许回调...")
    allowed = await manager.check_permission("execute", "test.sh", "test_agent")
    print(f"   结果: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert allowed
    
    # 设置回调（自动拒绝）
    async def auto_deny(action, path, agent_name):
        print(f"   询问: {action} {path} (agent: {agent_name})")
        return False
    
    manager.set_ask_callback(auto_deny)
    
    print("\n2. 测试自动拒绝回调...")
    allowed = await manager.check_permission("execute", "test.sh", "test_agent")
    print(f"   结果: {'✅ 允许' if allowed else '❌ 拒绝'}")
    assert not allowed
    
    print("\n✅ 询问回调测试通过")


async def test_pattern_matching():
    """测试模式匹配"""
    print("\n" + "=" * 60)
    print("测试6: 模式匹配")
    print("=" * 60)
    
    manager = get_permission_manager()
    manager.clear_rules()
    
    # 添加规则（注意顺序：后面的规则优先级更高）
    manager.add_rule("read", "*.py", "deny")  # 先deny所有.py
    manager.add_rule("read", "src/*.py", "allow")  # 然后allow src/下的
    manager.add_rule("read", "tests/*.py", "allow")  # 然后allow tests/下的
    
    # 测试
    test_cases = [
        ("src/main.py", True),  # 匹配src/*.py -> allow
        ("tests/test_main.py", True),  # 匹配tests/*.py -> allow
        ("main.py", False),  # 只匹配*.py -> deny
        ("lib/module.py", False),  # 只匹配*.py -> deny
    ]
    
    print("\n测试模式匹配:")
    for path, expected in test_cases:
        allowed = await manager.check_permission("read", path)
        status = "✅" if allowed == expected else "❌"
        print(f"   {status} read {path}: {allowed}")
        assert allowed == expected
    
    print("\n✅ 模式匹配测试通过")


async def main():
    """主函数"""
    print("🚀 开始测试权限系统\n")
    
    try:
        await test_basic_permissions()
        await test_default_permissions()
        await test_strict_permissions()
        await test_permission_decorator()
        await test_ask_callback()
        await test_pattern_matching()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
