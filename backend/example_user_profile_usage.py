"""
用户画像使用示例

展示如何在实际场景中正确使用用户画像
"""

import asyncio
from daoyoucode.agents.core.agent import BaseAgent, AgentConfig


class SmartAgent(BaseAgent):
    """智能Agent示例"""
    
    async def execute(self, prompt_source, user_input, context=None, **kwargs):
        """执行任务"""
        if context is None:
            context = {}
        
        user_id = context.get('user_id', 'default')
        
        # ========== 场景1：日常对话（不使用用户画像）==========
        if not self._is_special_command(user_input):
            # ✅ 使用用户偏好（轻量级）
            prefs = self.memory.get_preferences(user_id)
            
            # ✅ 使用对话历史
            session_id = context.get('session_id', 'default')
            history_context = await self.memory.load_context_smart(
                session_id=session_id,
                user_id=user_id,
                user_input=user_input,
                is_followup=False
            )
            
            # 正常处理
            return await super().execute(
                prompt_source, user_input, context, **kwargs
            )
        
        # ========== 场景2：特殊命令（使用用户画像）==========
        
        # 生成用户报告
        if user_input.startswith('/report'):
            return await self._generate_user_report(user_id)
        
        # 个性化推荐
        elif user_input.startswith('/recommend'):
            return await self._recommend_tools(user_id)
        
        # 分析用户习惯
        elif user_input.startswith('/analyze'):
            return await self._analyze_user_habits(user_id)
        
        # 默认处理
        return await super().execute(
            prompt_source, user_input, context, **kwargs
        )
    
    def _is_special_command(self, user_input: str) -> bool:
        """判断是否为特殊命令"""
        special_commands = ['/report', '/recommend', '/analyze']
        return any(user_input.startswith(cmd) for cmd in special_commands)
    
    async def _generate_user_report(self, user_id: str):
        """生成用户报告"""
        from daoyoucode.agents.core.agent import AgentResult
        
        # 按需加载用户画像
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return AgentResult(
                success=False,
                content="暂无用户画像数据",
                error="No profile data"
            )
        
        # 生成报告
        report = f"""
📊 用户报告
{'='*50}

基本信息：
  - 用户ID: {user_id}
  - 总对话数: {profile.get('total_conversations', 0)}
  - 技能水平: {profile.get('skill_level', '未知')}

常讨论话题：
{self._format_topics(profile.get('common_topics', []))}

活动模式：
  - 活跃时段: {profile.get('activity_pattern', '未知')}
  - 偏好风格: {profile.get('preferred_style', '未知')}

最近项目：
{self._format_projects(profile.get('recent_projects', []))}
"""
        
        return AgentResult(
            success=True,
            content=report.strip()
        )
    
    async def _recommend_tools(self, user_id: str):
        """个性化推荐工具"""
        from daoyoucode.agents.core.agent import AgentResult
        
        # 按需加载用户画像
        profile = self.get_user_profile(user_id)
        
        if not profile:
            # 降级：使用用户偏好
            prefs = self.memory.get_preferences(user_id)
            return await self._recommend_by_preferences(prefs)
        
        # 基于用户画像推荐
        topics = profile.get('common_topics', [])
        recommendations = []
        
        if 'testing' in topics:
            recommendations.extend([
                '🧪 pytest - Python测试框架',
                '📊 coverage - 代码覆盖率工具',
                '🔍 unittest - 单元测试框架'
            ])
        
        if 'refactoring' in topics:
            recommendations.extend([
                '🎨 black - 代码格式化工具',
                '📝 pylint - 代码质量检查',
                '🔧 mypy - 类型检查工具'
            ])
        
        if 'performance' in topics:
            recommendations.extend([
                '⚡ cProfile - 性能分析工具',
                '📈 memory_profiler - 内存分析',
                '🚀 line_profiler - 行级性能分析'
            ])
        
        if not recommendations:
            recommendations = ['暂无推荐，继续使用以获得个性化推荐']
        
        content = "🎯 个性化工具推荐\n" + "="*50 + "\n\n"
        content += "\n".join(recommendations)
        
        return AgentResult(
            success=True,
            content=content
        )
    
    async def _analyze_user_habits(self, user_id: str):
        """分析用户习惯"""
        from daoyoucode.agents.core.agent import AgentResult
        
        # 按需加载用户画像
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return AgentResult(
                success=False,
                content="暂无足够数据进行分析",
                error="Insufficient data"
            )
        
        # 分析
        analysis = f"""
🔍 用户习惯分析
{'='*50}

编程习惯：
  - 常用语言: {self._get_primary_language(profile)}
  - 代码风格: {profile.get('preferred_style', '未知')}
  - 技能水平: {profile.get('skill_level', '未知')}

工作模式：
  - 活跃时段: {profile.get('activity_pattern', '未知')}
  - 平均会话长度: {self._calculate_avg_session_length(profile)}
  - 常用功能: {self._get_common_features(profile)}

建议：
{self._generate_suggestions(profile)}
"""
        
        return AgentResult(
            success=True,
            content=analysis.strip()
        )
    
    async def _recommend_by_preferences(self, prefs):
        """基于用户偏好推荐（降级方案）"""
        from daoyoucode.agents.core.agent import AgentResult
        
        language = prefs.get('language', 'python')
        
        recommendations = {
            'python': ['pytest', 'black', 'mypy'],
            'javascript': ['jest', 'eslint', 'prettier'],
            'java': ['junit', 'checkstyle', 'spotbugs']
        }
        
        tools = recommendations.get(language, ['暂无推荐'])
        content = f"基于你的语言偏好（{language}），推荐：\n"
        content += "\n".join(f"  - {tool}" for tool in tools)
        
        return AgentResult(
            success=True,
            content=content
        )
    
    def _format_topics(self, topics):
        """格式化话题列表"""
        if not topics:
            return "  - 暂无数据"
        return "\n".join(f"  - {topic}" for topic in topics[:5])
    
    def _format_projects(self, projects):
        """格式化项目列表"""
        if not projects:
            return "  - 暂无数据"
        return "\n".join(f"  - {project}" for project in projects[:3])
    
    def _get_primary_language(self, profile):
        """获取主要编程语言"""
        topics = profile.get('common_topics', [])
        languages = ['python', 'javascript', 'java', 'go', 'rust']
        
        for lang in languages:
            if lang in topics:
                return lang
        
        return '未知'
    
    def _calculate_avg_session_length(self, profile):
        """计算平均会话长度"""
        total = profile.get('total_conversations', 0)
        sessions = profile.get('total_sessions', 1)
        
        if sessions == 0:
            return '未知'
        
        avg = total / sessions
        return f"{avg:.1f}轮/会话"
    
    def _get_common_features(self, profile):
        """获取常用功能"""
        # 这里可以从任务历史中分析
        return "代码编辑、测试生成、重构"
    
    def _generate_suggestions(self, profile):
        """生成个性化建议"""
        suggestions = []
        
        skill_level = profile.get('skill_level', 'beginner')
        
        if skill_level == 'beginner':
            suggestions.append("  - 建议多练习基础语法和常用库")
        elif skill_level == 'intermediate':
            suggestions.append("  - 建议学习设计模式和最佳实践")
        elif skill_level == 'advanced':
            suggestions.append("  - 建议深入研究性能优化和架构设计")
        
        topics = profile.get('common_topics', [])
        if 'testing' not in topics:
            suggestions.append("  - 建议加强测试相关知识")
        
        return "\n".join(suggestions) if suggestions else "  - 继续保持当前学习节奏"


# ========== 使用示例 ==========

async def demo():
    """演示用户画像的使用"""
    print("\n" + "="*60)
    print("用户画像使用示例")
    print("="*60)
    
    # 创建Agent
    config = AgentConfig(
        name="SmartAgent",
        description="智能Agent",
        model="qwen-plus",
        system_prompt="你是一个智能助手"
    )
    
    agent = SmartAgent(config)
    
    # 模拟用户画像数据
    user_id = "demo-user"
    agent.memory.long_term_memory.storage.save_user_profile(
        user_id,
        {
            'common_topics': ['python', 'testing', 'refactoring'],
            'total_conversations': 50,
            'total_sessions': 10,
            'skill_level': 'intermediate',
            'activity_pattern': 'evening',
            'preferred_style': 'functional',
            'recent_projects': ['web-app', 'cli-tool', 'api-service']
        }
    )
    
    # 场景1：日常对话（不使用用户画像）
    print("\n场景1：日常对话")
    print("-" * 60)
    print("用户: 如何写一个Python函数？")
    print("Agent: [正常处理，不加载用户画像]")
    print("✅ 性能：快速（无额外开销）")
    
    # 场景2：生成报告（使用用户画像）
    print("\n场景2：生成用户报告")
    print("-" * 60)
    result = await agent._generate_user_report(user_id)
    print(result.content)
    print("✅ 首次加载：从磁盘读取 + 缓存")
    
    # 场景3：个性化推荐（使用缓存）
    print("\n场景3：个性化推荐")
    print("-" * 60)
    result = await agent._recommend_tools(user_id)
    print(result.content)
    print("✅ 后续访问：使用缓存（快速）")
    
    # 场景4：习惯分析（使用缓存）
    print("\n场景4：习惯分析")
    print("-" * 60)
    result = await agent._analyze_user_habits(user_id)
    print(result.content)
    print("✅ 后续访问：使用缓存（快速）")
    
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    print("✅ 日常对话：不加载用户画像（高性能）")
    print("✅ 特殊场景：按需加载用户画像（灵活）")
    print("✅ 缓存机制：首次加载后缓存（优化）")
    print("✅ 降级策略：无画像时使用用户偏好（健壮）")


if __name__ == "__main__":
    asyncio.run(demo())
