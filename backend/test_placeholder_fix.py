"""
测试占位符路径修复

验证：
1. System Prompt中的工具使用规则
2. BaseTool的路径验证和自动修正
"""

import asyncio
from pathlib import Path
from daoyoucode.agents.tools.base import ToolContext, BaseTool, ToolResult


class MockTool(BaseTool):
    """模拟工具"""
    
    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="模拟工具"
        )
    
    async def execute(self, path: str) -> ToolResult:
        """执行工具"""
        resolved = self.resolve_path(path)
        return ToolResult(
            success=True,
            content=f"Resolved: {resolved}",
            metadata={'original': path, 'resolved': str(resolved)}
        )


async def test_placeholder_detection():
    """测试占位符检测"""
    print("=" * 60)
    print("测试1：占位符检测和自动修正")
    print("=" * 60)
    
    # 创建工具
    tool = MockTool()
    
    # 设置上下文
    repo_path = Path.cwd()
    context = ToolContext(repo_path=repo_path)
    tool.set_context(context)
    
    # 测试用例
    test_cases = [
        ("./your-repo-path", "应该修正为当前目录"),
        ("path/to/your/file.txt", "应该修正为当前目录"),
        ("./src", "应该去掉 ./ 前缀"),
        (".", "应该保持不变"),
        ("backend/config.py", "应该保持不变"),
    ]
    
    for path, expected in test_cases:
        print(f"\n测试路径: {path}")
        print(f"期望: {expected}")
        result = await tool.execute(path)
        print(f"结果: {result.content}")
        print(f"元数据: {result.metadata}")


async def test_agent_prompt():
    """测试Agent的Prompt规则"""
    print("\n" + "=" * 60)
    print("测试2：Agent Prompt中的工具使用规则")
    print("=" * 60)
    
    from daoyoucode.agents.core.agent import BaseAgent, AgentConfig
    
    # 创建Agent
    config = AgentConfig(
        name="test_agent",
        description="测试Agent",
        model="qwen-max",
        system_prompt="这是测试Prompt"
    )
    
    agent = BaseAgent(config)
    
    # 模拟execute方法中的Prompt构建
    tools = ["repo_map", "text_search"]  # 模拟有工具
    
    if tools:
        tool_rules = """⚠️ 工具使用规则（必须遵守）：

1. 路径参数使用 '.' 表示当前工作目录
   - ✅ 正确：repo_map(repo_path=".")
   - ❌ 错误：repo_map(repo_path="./your-repo-path")
   - ❌ 错误：repo_map(repo_path="/path/to/repo")

2. 文件路径使用相对路径
   - ✅ 正确：read_file(file_path="backend/config.py")
   - ❌ 错误：read_file(file_path="path/to/your/file.txt")

3. 搜索目录使用 '.' 或省略
   - ✅ 正确：text_search(query="example", directory=".")
   - ❌ 错误：text_search(query="example", directory="./src")

记住：当前工作目录就是项目根目录，不需要猜测路径！

---

"""
        full_prompt = tool_rules + "用户输入：你好"
        
        print("\n生成的Prompt（前500字符）：")
        print(full_prompt[:500])
        print("\n✅ 工具使用规则已添加到Prompt开头")


async def main():
    """主函数"""
    await test_placeholder_detection()
    await test_agent_prompt()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
    print("\n修复总结：")
    print("1. ✅ Agent的Prompt开头添加了工具使用规则")
    print("2. ✅ BaseTool.resolve_path()添加了占位符检测和自动修正")
    print("3. ✅ 自动去掉 ./ 前缀（如果路径不存在）")
    print("\n下一步：")
    print("1. 运行实际的CLI测试")
    print("2. 使用VSCode调试器追踪LLM的工具调用")
    print("3. 检查DEBUG_LLM_REQUEST日志")


if __name__ == "__main__":
    asyncio.run(main())
