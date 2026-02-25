#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分层存储功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.memory.storage import MemoryStorage


def test_basic_storage():
    """测试基础存储功能"""
    print("=" * 80)
    print("测试分层存储功能")
    print("=" * 80)
    print()
    
    # 创建存储实例（指定项目路径）
    project_path = Path(".").resolve()
    storage = MemoryStorage(project_path=project_path)
    
    print(f"✓ 存储实例已创建")
    print(f"  用户级目录: {storage.user_dir}")
    print(f"  项目级目录: {storage.project_dir}")
    print()
    
    # 测试用户级存储
    print("测试用户级存储（用户画像）...")
    user_id = "test-user"
    profile = {
        "coding_style": {
            "indentation": "4 spaces",
            "naming_convention": "snake_case"
        },
        "communication_style": {
            "verbosity": "detailed"
        }
    }
    storage.save_user_profile(user_id, profile)
    print(f"✓ 保存用户画像")
    
    loaded_profile = storage.get_user_profile(user_id)
    if loaded_profile == profile:
        print(f"✓ 加载用户画像成功")
    else:
        print(f"✗ 加载用户画像失败")
    print()
    
    # 测试项目级存储
    print("测试项目级存储（项目上下文）...")
    context = {
        "architecture": {
            "type": "microservices",
            "patterns": ["DDD", "CQRS"]
        }
    }
    storage.save_project_context(context)
    print(f"✓ 保存项目上下文")
    
    loaded_context = storage.get_project_context()
    if loaded_context == context:
        print(f"✓ 加载项目上下文成功")
    else:
        print(f"✗ 加载项目上下文失败")
    print()
    
    # 测试对话历史
    print("测试对话历史...")
    session_id = "test-session"
    storage.add_conversation(
        session_id=session_id,
        user_message="你好，这是测试消息",
        ai_response="你好！我收到了你的测试消息。",
        metadata={"test": True},
        user_id=user_id
    )
    print(f"✓ 添加对话")
    
    # 检查对话历史文件
    if storage._chat_history_file and storage._chat_history_file.exists():
        print(f"✓ 对话历史文件已创建: {storage._chat_history_file}")
        
        # 读取内容
        content = storage._chat_history_file.read_text(encoding='utf-8')
        if "你好，这是测试消息" in content:
            print(f"✓ 对话历史内容正确")
        else:
            print(f"✗ 对话历史内容不正确")
    else:
        print(f"✗ 对话历史文件未创建")
    print()
    
    # 获取统计信息
    print("存储统计信息:")
    stats = storage.get_stats()
    print(f"  会话数: {stats['total_sessions']}")
    print(f"  对话数: {stats['total_conversations']}")
    print(f"  用户数: {stats['total_users']}")
    print(f"  用户画像数: {stats['user_profiles']}")
    print(f"  用户级目录: {stats['storage']['user_dir']}")
    print(f"  项目级目录: {stats['storage']['project_dir']}")
    print()
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print()
    
    print("检查生成的文件:")
    print(f"  用户级: {storage.user_dir}")
    if storage.user_dir.exists():
        for file in storage.user_dir.iterdir():
            if file.is_file():
                size = file.stat().st_size
                print(f"    - {file.name} ({size} bytes)")
    
    print(f"  项目级: {storage.project_dir}")
    if storage.project_dir and storage.project_dir.exists():
        for file in storage.project_dir.iterdir():
            if file.is_file():
                size = file.stat().st_size
                print(f"    - {file.name} ({size} bytes)")


if __name__ == "__main__":
    test_basic_storage()
