#!/usr/bin/env python3
"""
验证超时配置是否正确

检查所有超时配置是否统一为 1800 秒（30分钟）
"""

import yaml
import sys
from pathlib import Path


def check_config_file():
    """检查配置文件"""
    config_path = Path(__file__).parent / "config" / "llm_config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    timeout = config.get('default', {}).get('timeout')
    
    if timeout == 1800:
        print(f"✅ 配置文件超时: {timeout}秒 (30分钟)")
        return True
    else:
        print(f"❌ 配置文件超时: {timeout}秒 (应该是 1800)")
        return False


def check_client_manager():
    """检查 client_manager.py"""
    file_path = Path(__file__).parent / "daoyoucode" / "agents" / "llm" / "client_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "timeout=httpx.Timeout(1800.0)" in content:
        print("✅ HTTP 客户端超时: 1800秒 (30分钟)")
        return True
    else:
        print("❌ HTTP 客户端超时配置不正确")
        return False


def check_unified_client():
    """检查 unified.py"""
    file_path = Path(__file__).parent / "daoyoucode" / "agents" / "llm" / "clients" / "unified.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查同步请求
    sync_ok = "timeout=1800.0" in content
    
    # 检查流式请求
    stream_ok = content.count("timeout=1800.0") >= 2
    
    if sync_ok and stream_ok:
        print("✅ 单次请求超时: 1800秒 (30分钟)")
        print("   - 同步请求: ✅")
        print("   - 流式请求: ✅")
        return True
    else:
        print("❌ 单次请求超时配置不正确")
        if not sync_ok:
            print("   - 同步请求: ❌")
        if not stream_ok:
            print("   - 流式请求: ❌")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("验证超时配置")
    print("=" * 60)
    print()
    
    results = []
    
    # 检查配置文件
    print("1. 检查配置文件 (llm_config.yaml)")
    results.append(check_config_file())
    print()
    
    # 检查 client_manager
    print("2. 检查 HTTP 客户端 (client_manager.py)")
    results.append(check_client_manager())
    print()
    
    # 检查 unified client
    print("3. 检查单次请求 (unified.py)")
    results.append(check_unified_client())
    print()
    
    # 总结
    print("=" * 60)
    if all(results):
        print("✅ 所有超时配置正确！")
        print()
        print("超时时间: 1800秒 (30分钟)")
        print()
        print("支持的场景:")
        print("  • 简单查询: 10-30秒")
        print("  • 中等复杂度: 30-90秒")
        print("  • 复杂查询: 90-180秒")
        print("  • 大规模操作: 180-1200秒 (3-20分钟)")
        print("  • 极端情况: 1200-1800秒 (20-30分钟)")
        print()
        return 0
    else:
        print("❌ 部分配置不正确，请检查！")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
