#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试聊天历史保存
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from daoyoucode.agents.memory.manager import get_memory_manager
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig


def test_chat_history():
    """测试聊天历史保存"""
    print("=" * 80)
    print("测试聊天历史保存")
    print("=" * 80)
    print()
    
    # 1. 初始化记忆管理器（指定项目路径）
    project_path = Path(".").resolve()
    memory_manager = get_memory_manager(project_path=project_path, force_new=True)
    
    print(f"✓ 记忆管理器已初始化")
    print(f"  用户级目录: {memory_manager.storage.user_dir}")
    print(f"  项目级目录: {memory_manager.storage.project_dir}")
    print()
    
    # 2. 创建 Agent（会使用单例的 memory_manager）
    config = AgentConfig(
        name="TestAgent",
        description="测试Agent",
        model="qwen-plus"
    )
    agent = BaseAgent(config)
    
    print(f"✓ Agent 已创建")
    print(f"  Agent 使用的 memory: {agent.memory}")
    print(f"  是否是同一个实例: {agent.memory is memory_manager}")
    print()
    
    # 3. 添加对话
    session_id = "test-session-123"
    user_id = "test-user"
    
    agent.memory.add_conversation(
        session_id=session_id,
        user_message="你好，这是测试消息",
        ai_response="你好！我收到了你的测试消息。",
        metadata={"test": True},
        user_id=user_id
    )
    
    print(f"✓ 添加对话")
    print()
    
    # 4. 检查对话历史文件
    chat_history_file = memory_manager.storage._chat_history_file
    
    if chat_history_file and chat_history_file.exists():
        print(f"✓ 对话历史文件已创建: {chat_history_file}")
        
        # 读取内容
        content = chat_history_file.read_text(encoding='utf-8')
        print(f"\n对话历史内容:")
        print("-" * 80)
        print(content)
        print("-" * 80)
        
        if "你好，这是测试消息" in content:
            print(f"\n✓ 对话历史内容正确")
        else:
            print(f"\n✗ 对话历史内容不正确")
    else:
        print(f"✗ 对话历史文件未创建")
        print(f"  预期路径: {chat_history_file}")
    
    print()
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_chat_history()
