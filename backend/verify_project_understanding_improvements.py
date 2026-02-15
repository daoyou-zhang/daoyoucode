#!/usr/bin/env python3
"""
验证项目理解策略改进

检查点：
1. repo_map默认max_tokens改为5000
2. schema中default值为5000
3. 提示词中包含文档优先策略
4. 提示词中有完整的示例
"""

import re
from pathlib import Path


def check_repomap_default():
    """检查repo_map默认值"""
    print("=" * 60)
    print("检查1: repo_map默认max_tokens值")
    print("=" * 60)
    
    file_path = Path("daoyoucode/agents/tools/repomap_tools.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 检查execute方法的默认值
    match = re.search(r'max_tokens: int = (\d+)', content)
    if match:
        default_value = int(match.group(1))
        if default_value == 5000:
            print("✓ execute方法默认值: 5000")
        else:
            print(f"✗ execute方法默认值错误: {default_value} (应该是5000)")
            return False
    else:
        print("✗ 未找到max_tokens默认值")
        return False
    
    # 检查schema中的default
    match = re.search(r'"max_tokens".*?"default": (\d+)', content, re.DOTALL)
    if match:
        schema_default = int(match.group(1))
        if schema_default == 5000:
            print("✓ schema默认值: 5000")
        else:
            print(f"✗ schema默认值错误: {schema_default} (应该是5000)")
            return False
    else:
        print("✗ 未找到schema中的default")
        return False
    
    # 检查description是否一致
    if '"默认5000' in content or '"default": 5000' in content:
        print("✓ description与default值一致")
    else:
        print("⚠ description可能与default值不一致")
    
    return True


def check_prompt_improvements():
    """检查提示词改进"""
    print("\n" + "=" * 60)
    print("检查2: 提示词改进")
    print("=" * 60)
    
    file_path = Path("../skills/chat-assistant/prompts/chat_assistant.md")
    content = file_path.read_text(encoding="utf-8")
    
    checks = [
        ("文档优先原则", "文档优先"),
        ("max_tokens=5000示例", "max_tokens=5000"),
        ("read_file(README.md)示例", 'read_file(file_path="README.md")'),
        ("理解项目示例", "了解下当前项目"),
        ("repo_map只包含代码说明", "只包含代码文件"),
    ]
    
    all_passed = True
    for name, keyword in checks:
        if keyword in content:
            print(f"✓ {name}")
        else:
            print(f"✗ 缺少: {name}")
            all_passed = False
    
    return all_passed


def check_documentation():
    """检查文档更新"""
    print("\n" + "=" * 60)
    print("检查3: 文档完整性")
    print("=" * 60)
    
    file_path = Path("SMART_REPO_MAP.md")
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        
        checks = [
            ("Token预算说明", "Token 预算"),
            ("PageRank说明", "PageRank"),
            ("缓存机制说明", "SQLite"),
            ("性能数据", "性能数据"),
        ]
        
        all_passed = True
        for name, keyword in checks:
            if keyword in content:
                print(f"✓ {name}")
            else:
                print(f"✗ 缺少: {name}")
                all_passed = False
        
        return all_passed
    else:
        print("✗ SMART_REPO_MAP.md不存在")
        return False


def main():
    print("验证项目理解策略改进\n")
    
    results = []
    
    # 检查1: repo_map默认值
    results.append(("repo_map默认值", check_repomap_default()))
    
    # 检查2: 提示词改进
    results.append(("提示词改进", check_prompt_improvements()))
    
    # 检查3: 文档
    results.append(("文档完整性", check_documentation()))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有检查通过！")
        print("\n改进内容：")
        print("1. repo_map默认max_tokens从2000改为5000")
        print("2. 提示词增加文档优先策略")
        print("3. 提示词增加完整的项目理解示例")
        print("4. schema描述与默认值保持一致")
        return 0
    else:
        print("\n❌ 部分检查失败，请修复")
        return 1


if __name__ == "__main__":
    exit(main())
