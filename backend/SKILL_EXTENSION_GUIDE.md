# Skill扩展指南 - 支持任意业务场景

## 概述

DaoyouCode的Agent架构**不仅限于代码任务**，通过Skill机制，可以轻松扩展到任何业务场景：
- 📝 写作（小说、文章、报告）
- 🎨 创意（设计、策划、营销）
- 📊 分析（数据、市场、用户）
- 🎓 教育（课程、培训、辅导）
- 💼 商务（合同、邮件、提案）
- ...任何你能想到的场景

---

## 核心理念

### 为什么可以支持任意场景？

DaoyouCode的架构是**领域无关**的：

```
┌─────────────────────────────────────────┐
│         Executor（执行器）               │  ← 通用入口
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│      Orchestrator（编排器）              │  ← 通用编排逻辑
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│         Agent（智能体）                  │  ← 领域专用
│  CodeAgent │ NovelAgent │ DesignAgent   │
└─────────────────────────────────────────┘
```

**关键点**：
- Executor和Orchestrator是**领域无关**的
- 只需要创建**领域专用的Agent和Skill**
- 所有18大核心系统都可以复用

---

## 示例：写小说Skill

### 1. 创建NovelAgent

```python
# backend/daoyoucode/agents/builtin/novel_writer.py
"""
小说写作Agent
"""

from typing import Dict, Any, List
from ..core.agent import BaseAgent
from ..core.skill import Skill


class NovelWriterAgent(BaseAgent):
    """小说写作Agent"""
    
    def __init__(self):
        super().__init__(
            name="NovelWriter",
            description="专业的小说写作助手，擅长创作各类小说",
            capabilities=[
                "plot_design",      # 情节设计
                "character_dev",    # 角色塑造
                "scene_writing",    # 场景描写
                "dialogue",         # 对话创作
                "revision",         # 修改润色
            ]
        )
    
    async def execute(
        self,
        instruction: str,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """执行写作任务"""
        
        # 1. 分析写作需求
        writing_type = self._analyze_writing_type(instruction)
        
        # 2. 准备写作上下文
        writing_context = self._prepare_context(context)
        
        # 3. 调用LLM生成内容
        result = await self._generate_content(
            instruction,
            writing_type,
            writing_context
        )
        
        # 4. 后处理
        result = self._post_process(result)
        
        return {
            'success': True,
            'content': result['content'],
            'word_count': result['word_count'],
            'metadata': result['metadata'],
        }
    
    def _analyze_writing_type(self, instruction: str) -> str:
        """分析写作类型"""
        if '情节' in instruction or 'plot' in instruction.lower():
            return 'plot'
        elif '角色' in instruction or 'character' in instruction.lower():
            return 'character'
        elif '场景' in instruction or 'scene' in instruction.lower():
            return 'scene'
        elif '对话' in instruction or 'dialogue' in instruction.lower():
            return 'dialogue'
        else:
            return 'general'
    
    def _prepare_context(self, context: Dict) -> Dict:
        """准备写作上下文"""
        return {
            'genre': context.get('genre', '现代都市'),
            'style': context.get('style', '轻松幽默'),
            'characters': context.get('characters', []),
            'previous_chapters': context.get('previous_chapters', []),
        }
    
    async def _generate_content(
        self,
        instruction: str,
        writing_type: str,
        context: Dict
    ) -> Dict:
        """生成内容"""
        # 构建提示词
        prompt = self._build_prompt(instruction, writing_type, context)
        
        # 调用LLM
        response = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.8,  # 创意写作需要更高的温度
        )
        
        return {
            'content': response['text'],
            'word_count': len(response['text']),
            'metadata': {
                'type': writing_type,
                'genre': context['genre'],
            }
        }
    
    def _build_prompt(
        self,
        instruction: str,
        writing_type: str,
        context: Dict
    ) -> str:
        """构建提示词"""
        prompt_parts = [
            f"你是一位专业的{context['genre']}小说作家。",
            f"写作风格：{context['style']}",
            "",
            f"任务：{instruction}",
            "",
        ]
        
        # 添加角色信息
        if context['characters']:
            prompt_parts.append("角色信息：")
            for char in context['characters']:
                prompt_parts.append(f"- {char['name']}: {char['description']}")
            prompt_parts.append("")
        
        # 添加前文
        if context['previous_chapters']:
            prompt_parts.append("前文概要：")
            for chapter in context['previous_chapters'][-3:]:  # 最近3章
                prompt_parts.append(f"- {chapter['title']}: {chapter['summary']}")
            prompt_parts.append("")
        
        prompt_parts.append("请开始创作：")
        
        return "\n".join(prompt_parts)
    
    def _post_process(self, result: Dict) -> Dict:
        """后处理"""
        # 可以添加：
        # - 格式化
        # - 错别字检查
        # - 敏感词过滤
        # - 段落优化
        return result
```

---

### 2. 创建写作Skills

```python
# backend/daoyoucode/agents/skills/novel_skills.py
"""
小说写作技能
"""

from ..core.skill import Skill
from ..builtin.novel_writer import NovelWriterAgent


# Skill 1: 创作新章节
write_chapter_skill = Skill(
    name="write_chapter",
    description="创作小说新章节",
    agent=NovelWriterAgent(),
    triggers=[
        "写一章",
        "创作章节",
        "write chapter",
        "继续写",
    ],
    parameters={
        'genre': '小说类型（现代都市/玄幻/科幻/言情等）',
        'style': '写作风格（轻松幽默/严肃深沉/热血激昂等）',
        'word_count': '字数要求',
    },
    examples=[
        "写一章现代都市小说，轻松幽默风格，3000字",
        "继续写上一章的故事",
        "创作一个转折性的章节",
    ]
)


# Skill 2: 设计角色
design_character_skill = Skill(
    name="design_character",
    description="设计小说角色",
    agent=NovelWriterAgent(),
    triggers=[
        "设计角色",
        "创建人物",
        "design character",
        "角色设定",
    ],
    parameters={
        'role': '角色定位（主角/配角/反派）',
        'personality': '性格特点',
        'background': '背景故事',
    },
    examples=[
        "设计一个幽默风趣的主角",
        "创建一个神秘的反派角色",
        "设计女主角的闺蜜",
    ]
)


# Skill 3: 构思情节
plot_design_skill = Skill(
    name="plot_design",
    description="构思小说情节",
    agent=NovelWriterAgent(),
    triggers=[
        "构思情节",
        "设计剧情",
        "plot design",
        "情节大纲",
    ],
    parameters={
        'arc': '故事弧（开端/发展/高潮/结局）',
        'conflict': '冲突类型',
        'twist': '是否需要反转',
    },
    examples=[
        "构思一个悬疑情节",
        "设计高潮部分的剧情",
        "创作一个意外的转折",
    ]
)


# Skill 4: 场景描写
scene_writing_skill = Skill(
    name="scene_writing",
    description="描写小说场景",
    agent=NovelWriterAgent(),
    triggers=[
        "描写场景",
        "场景描写",
        "write scene",
        "环境描写",
    ],
    parameters={
        'location': '地点',
        'atmosphere': '氛围',
        'details': '重点细节',
    },
    examples=[
        "描写一个紧张的会议室场景",
        "写一段浪漫的海边日落",
        "描写古代宫殿的宏伟",
    ]
)


# Skill 5: 对话创作
dialogue_skill = Skill(
    name="dialogue",
    description="创作人物对话",
    agent=NovelWriterAgent(),
    triggers=[
        "写对话",
        "对话创作",
        "write dialogue",
        "人物对话",
    ],
    parameters={
        'characters': '参与对话的角色',
        'emotion': '情感基调',
        'purpose': '对话目的',
    },
    examples=[
        "写两个朋友的日常对话",
        "创作一段激烈的争吵",
        "写主角和反派的对峙",
    ]
)


# 注册所有技能
NOVEL_SKILLS = [
    write_chapter_skill,
    design_character_skill,
    plot_design_skill,
    scene_writing_skill,
    dialogue_skill,
]
```

---

### 3. 配置Skill

```yaml
# config/skills.yaml
skills:
  # 代码相关技能
  - name: code_analysis
    enabled: true
    agent: CodeAnalyzer
    
  - name: code_generation
    enabled: true
    agent: CodeGenerator
  
  # 小说写作技能
  - name: write_chapter
    enabled: true
    agent: NovelWriter
    config:
      default_genre: "现代都市"
      default_style: "轻松幽默"
      default_word_count: 3000
  
  - name: design_character
    enabled: true
    agent: NovelWriter
  
  - name: plot_design
    enabled: true
    agent: NovelWriter
  
  - name: scene_writing
    enabled: true
    agent: NovelWriter
  
  - name: dialogue
    enabled: true
    agent: NovelWriter
```

---

### 4. 使用示例

#### 示例1：创作新章节

```python
# 用户输入
instruction = "写一章现代都市小说，主角在咖啡厅遇到了初恋，3000字"

# 系统处理流程
# 1. BehaviorGuide识别 → RequestType.SKILL_MATCH
# 2. 匹配到 write_chapter_skill
# 3. 调用 NovelWriterAgent
# 4. 生成内容

# 输出
{
    'success': True,
    'content': '第五章：咖啡厅的重逢\n\n阳光透过落地窗...',
    'word_count': 3127,
    'metadata': {
        'type': 'chapter',
        'genre': '现代都市',
        'style': '轻松幽默',
    }
}
```

#### 示例2：设计角色

```python
instruction = "设计一个神秘的反派角色，有复杂的背景故事"

# 输出
{
    'success': True,
    'character': {
        'name': '林墨',
        'role': '反派',
        'personality': '冷静、智慧、神秘',
        'background': '曾是主角的导师，因误会而走上对立面...',
        'appearance': '总是穿着黑色风衣，眼神深邃...',
        'motivation': '寻找失踪的妹妹，不择手段...',
    }
}
```

---

## 流程对比

### 代码任务 vs 写作任务

| 步骤 | 代码任务 | 写作任务 | 说明 |
|------|---------|---------|------|
| 1. 代码库评估 | ✅ 执行 | ❌ 跳过 | 写作不需要 |
| 2. 行为指南 | ✅ 识别代码任务 | ✅ 识别写作任务 | 都需要 |
| 3. 智能上下文选择 | ✅ 选择代码文件 | ✅ 选择前文章节 | 都需要 |
| 4. 智能路由 | ✅ 选择CodeAgent | ✅ 选择NovelAgent | 都需要 |
| 5. 智能模型选择 | ✅ 选择代码模型 | ✅ 选择创意模型 | 都需要 |
| 6. 执行规划 | ✅ 规划代码步骤 | ✅ 规划写作步骤 | 都需要 |
| 7. 权限检查 | ✅ 检查文件权限 | ❌ 跳过 | 写作不需要 |
| 8. 记忆加载 | ✅ 加载代码历史 | ✅ 加载写作历史 | 都需要 |
| 9. Agent执行 | ✅ 执行代码任务 | ✅ 执行写作任务 | 都需要 |
| 10. 独立验证 | ✅ 代码验证 | ⚠️ 可选验证 | 写作可选 |
| 11. 反馈评估 | ✅ 评估代码质量 | ✅ 评估文章质量 | 都需要 |

**关键发现**：
- 大部分步骤都可以复用！
- 只需要跳过不相关的步骤（代码库评估、权限检查）
- Agent层是唯一需要定制的部分

---

## 更多扩展示例

### 1. 数据分析Skill

```python
class DataAnalystAgent(BaseAgent):
    """数据分析Agent"""
    
    capabilities = [
        "data_cleaning",      # 数据清洗
        "statistical_analysis", # 统计分析
        "visualization",      # 可视化
        "report_generation",  # 报告生成
    ]
```

### 2. 设计创意Skill

```python
class DesignAgent(BaseAgent):
    """设计创意Agent"""
    
    capabilities = [
        "logo_design",        # Logo设计
        "color_scheme",       # 配色方案
        "layout_design",      # 布局设计
        "brand_identity",     # 品牌识别
    ]
```

### 3. 商务写作Skill

```python
class BusinessWriterAgent(BaseAgent):
    """商务写作Agent"""
    
    capabilities = [
        "email_writing",      # 邮件撰写
        "proposal",           # 提案书
        "contract",           # 合同
        "report",             # 报告
    ]
```

---

## 核心优势

### 1. 架构通用性

✅ **领域无关的核心系统**：
- TaskManager - 管理任何类型的任务
- MemorySystem - 记忆任何类型的历史
- IntelligentRouter - 路由到任何Agent
- ContextManager - 管理任何类型的上下文
- ExecutionPlanner - 规划任何类型的执行
- FeedbackLoop - 评估任何类型的结果

### 2. 灵活的扩展性

✅ **只需要创建**：
- 领域专用的Agent（如NovelWriterAgent）
- 领域专用的Skill（如write_chapter_skill）
- 领域专用的配置（如default_genre）

✅ **不需要修改**：
- 核心架构
- 编排器
- 其他系统

### 3. 完整的功能支持

✅ **所有高级功能都可用**：
- Hook系统 - 在写作前后插入自定义逻辑
- 权限系统 - 控制写作内容的访问
- ReAct循环 - 自动改进写作质量
- 并行执行 - 同时创作多个章节
- 会话管理 - 保持长篇创作的连续性
- 记忆系统 - 记住角色、情节、风格

---

## 总结

### 回答你的问题

> "假如既不是闲聊，也不是编程，而是其他业务需求，比如写小说，那我插入skill，能实现么？只是大材小用，但没问题吧？"

**答案**：

1. ✅ **完全可以实现** - 只需创建NovelAgent和相关Skills
2. ❌ **不是大材小用** - 这正是架构设计的初衷！
3. ✅ **没有任何问题** - 所有18大系统都可以复用
4. ✅ **反而更强大** - 写作任务也能享受：
   - 智能路由
   - 记忆管理
   - 执行规划
   - 反馈评估
   - 会话管理
   - ...所有高级功能

### 架构的真正价值

DaoyouCode的架构不是"代码Agent系统"，而是**通用的智能体编排系统**：

```
┌─────────────────────────────────────────┐
│      Universal Agent Framework           │
│         (通用智能体框架)                  │
├─────────────────────────────────────────┤
│  Code Domain  │  Writing  │  Design     │
│  (代码领域)    │  (写作)    │  (设计)     │
│               │           │             │
│  Analysis     │  Novel    │  Logo       │
│  Generation   │  Article  │  Layout     │
│  Debug        │  Report   │  Brand      │
└─────────────────────────────────────────┘
```

**这才是真正的"完美架构"！** 🎉
