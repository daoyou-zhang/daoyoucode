"""
最简单的快速开始 - 仅使用通义千问
只需要配置一个API密钥即可运行
"""

import asyncio
from daoyoucode.llm import get_orchestrator, get_client_manager


async def main():
    """快速开始 - 仅通义千问"""
    
    print("\n" + "=" * 60)
    print("LLM模块快速开始 - 仅通义千问")
    print("=" * 60 + "\n")
    
    # ========================================
    # 第1步: 配置通义千问API密钥
    # ========================================
    
    # 方式1: 直接在这里填入（适合测试）
    API_KEY = "sk-d2971f2015574377bdf97046b1a03b87"  # 👈 在这里填入你的通义千问API密钥
    
    # 方式2: 从环境变量读取（推荐生产环境）
    # import os
    # API_KEY = os.getenv("QWEN_API_KEY", "your-qwen-api-key-here")
    
    if API_KEY == "your-qwen-api-key-here":
        print("❌ 请先配置API密钥！")
        print("\n📝 获取API密钥的步骤:")
        print("1. 访问 https://dashscope.aliyun.com/")
        print("2. 注册/登录阿里云账号")
        print("3. 进入控制台 → API-KEY管理")
        print("4. 创建新的API-KEY")
        print("5. 复制密钥（格式：sk-xxxxxx）")
        print("6. 填入上面第18行的 API_KEY 变量")
        return
    
    # 配置客户端
    client_manager = get_client_manager()
    client_manager.configure_provider(
        provider="qwen",
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    print("✅ 通义千问API配置完成\n")
    
    # ========================================
    # 第2步: 配置Skill目录
    # ========================================
    
    from pathlib import Path
    from daoyoucode.llm.skills import SkillLoader
    
    # 指定Skill目录
    skill_dir = Path(__file__).parent / "daoyoucode" / "llm" / "skills" / "examples"
    skill_loader = SkillLoader(skills_dirs=[str(skill_dir)])
    skill_loader.load_all_skills()
    
    print(f"✅ 已加载 {len(skill_loader.skills)} 个Skill: {list(skill_loader.skills.keys())}\n")
    
    # ========================================
    # 第3步: 使用LLM
    # ========================================
    
    orchestrator = get_orchestrator()
    orchestrator.skill_loader = skill_loader  # 使用我们配置的loader
    
    # 示例1: 简单对话（使用qwen-turbo，最便宜）
    print("=" * 60)
    print("示例1: 简单对话（qwen-turbo）")
    print("=" * 60)
    
    result = await orchestrator.chat(
        user_message="用一句话介绍Python",
        session_id="demo_1",
        model="qwen-turbo"  # 最便宜的模型
    )
    
    print(f"\n👤 用户: 用一句话介绍Python")
    print(f"🤖 AI: {result['response']}")
    print(f"\n📊 统计:")
    print(f"   模型: {result.get('model', 'unknown')}")
    print(f"   Tokens: {result.get('tokens_used', 0)}")
    print(f"   成本: ¥{result.get('cost', 0):.6f}")
    print(f"   延迟: {result.get('latency', 0):.2f}秒\n")
    
    # 示例2: 使用Skill（使用qwen-plus，性价比高）
    print("=" * 60)
    print("示例2: 使用Skill生成文档（qwen-plus）")
    print("=" * 60)
    
    result = await orchestrator.execute_skill(
        skill_name="documentation",
        user_message="帮我写一个Python函数的文档，函数名是calculate_sum，功能是计算两个数的和",
        session_id="demo_2"
    )
    
    print(f"\n👤 用户: 帮我写一个Python函数的文档")
    print(f"🤖 AI:\n{result['response']}")
    print(f"\n📊 统计:")
    print(f"   模型: {result.get('_metadata', {}).get('model', 'unknown')}")
    print(f"   Tokens: {result.get('_metadata', {}).get('tokens_used', 0)}")
    print(f"   成本: ¥{result.get('_metadata', {}).get('cost', 0):.6f}\n")
    
    # 示例3: 追问对话
    print("=" * 60)
    print("示例3: 追问对话（自动节省tokens）")
    print("=" * 60)
    
    session_id = "demo_3"
    
    # 第一轮
    print("\n👤 用户: 介绍一下Python的装饰器")
    result1 = await orchestrator.chat(
        user_message="介绍一下Python的装饰器",
        session_id=session_id,
        model="qwen-plus"
    )
    print(f"🤖 AI: {result1['response'][:100]}...")
    print(f"   Tokens: {result1.get('tokens_used', 0)}")
    
    # 第二轮（追问）
    print("\n👤 用户: 能举个例子吗？")
    result2 = await orchestrator.chat(
        user_message="能举个例子吗？",
        session_id=session_id,  # 相同session_id
        model="qwen-plus"
    )
    print(f"🤖 AI: {result2['response'][:100]}...")
    print(f"   是否追问: {result2['is_followup']}")
    print(f"   Tokens: {result2.get('tokens_used', 0)}")
    
    if result2['is_followup']:
        tokens1 = result1.get('tokens_used', 0)
        tokens2 = result2.get('tokens_used', 0)
        if tokens1 > 0 and tokens2 < tokens1:
            print(f"   💰 追问模式节省了约{(1-tokens2/tokens1)*100:.0f}%的tokens！")
    
    print("\n" + "=" * 60)
    print("✅ 运行成功！")
    print("=" * 60)
    
    print("\n💡 提示:")
    print("   - qwen-turbo: 最便宜，适合简单任务")
    print("   - qwen-plus: 性价比高，适合大多数任务（推荐）")
    print("   - qwen-max: 最强大，适合复杂任务")
    print("\n   查看更多示例: python example_real_usage.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
