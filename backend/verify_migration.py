#!/usr/bin/env python3
"""
验证目录迁移是否成功
"""

from pathlib import Path
import sys

def check_directory_structure():
    """检查目录结构"""
    print("🔍 检查目录结构...")
    
    base = Path("daoyoucode")
    
    # 检查agents目录存在
    agents_dir = base / "agents"
    if not agents_dir.exists():
        print("❌ agents目录不存在")
        return False
    print("✅ agents目录存在")
    
    # 检查子目录
    subdirs = ["core", "orchestrators", "middleware", "builtin", "llm"]
    for subdir in subdirs:
        path = agents_dir / subdir
        if not path.exists():
            print(f"❌ agents/{subdir}目录不存在")
            return False
        print(f"✅ agents/{subdir}目录存在")
    
    # 检查旧目录已删除
    old_dirs = ["skill_system", "llm"]
    for old_dir in old_dirs:
        path = base / old_dir
        if path.exists():
            print(f"❌ 旧目录{old_dir}仍然存在")
            return False
        print(f"✅ 旧目录{old_dir}已删除")
    
    return True


def check_files():
    """检查关键文件"""
    print("\n🔍 检查关键文件...")
    
    base = Path("daoyoucode/agents")
    
    files = [
        "__init__.py",
        "executor.py",
        "README.md",
        "core/skill.py",
        "core/agent.py",
        "core/orchestrator.py",
        "core/middleware.py",
        "orchestrators/simple.py",
        "orchestrators/multi_agent.py",
        "middleware/followup.py",
        "middleware/context.py",
        "builtin/translator.py",
        "builtin/programmer.py",
        "llm/base.py",
        "llm/client_manager.py",
    ]
    
    for file in files:
        path = base / file
        if not path.exists():
            print(f"❌ {file}不存在")
            return False
        print(f"✅ {file}存在")
    
    return True


def check_imports():
    """检查导入是否正常"""
    print("\n🔍 检查导入...")
    
    try:
        # 检查主包导入
        from daoyoucode import (
            execute_skill,
            list_skills,
            get_skill_info,
            register_agent,
            register_orchestrator,
            register_middleware,
        )
        print("✅ 主包导入成功")
        
        # 检查agents模块导入
        from daoyoucode.agents import (
            BaseAgent,
            BaseOrchestrator,
            BaseMiddleware,
            SkillConfig,
        )
        print("✅ agents模块导入成功")
        
        return True
    
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def check_docs():
    """检查文档"""
    print("\n🔍 检查文档...")
    
    docs = [
        "README.md",
        "daoyoucode/agents/README.md",
        "MIGRATION_SUMMARY.md",
    ]
    
    for doc in docs:
        path = Path(doc)
        if not path.exists():
            print(f"❌ {doc}不存在")
            return False
        print(f"✅ {doc}存在")
    
    # 检查旧文档已删除
    old_docs = [
        "NEW_DESIGN.md",
        "SKILL_SYSTEM_USAGE.md",
        "IMPLEMENTATION_COMPLETE.md",
    ]
    
    for doc in old_docs:
        path = Path(doc)
        if path.exists():
            print(f"❌ 旧文档{doc}仍然存在")
            return False
        print(f"✅ 旧文档{doc}已删除")
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始验证目录迁移")
    print("=" * 60)
    
    checks = [
        ("目录结构", check_directory_structure),
        ("关键文件", check_files),
        ("导入功能", check_imports),
        ("文档", check_docs),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有检查通过！迁移成功！")
        return 0
    else:
        print("⚠️ 部分检查失败，请检查上述错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())
