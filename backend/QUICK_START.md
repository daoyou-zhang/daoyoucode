# DaoyouCode 快速启动指南 🚀

## 启动命令

### 方式1：直接运行（推荐）

```bash
# 进入 backend 目录
cd backend

# 启动交互式对话
python -m cli chat

# 或者指定模型
python -m cli chat --model qwen-max

# 或者加载文件
python -m cli chat README.md STRUCTURE.txt
```

### 方式2：使用 Python 模块

```bash
# 在 backend 目录下
python cli/app.py chat
```

---

## 可用命令

### 1. 交互式对话（主要功能）

```bash
python -m cli chat [文件...] [选项]

选项:
  --model, -m TEXT    使用的模型 [默认: qwen-max]
  --repo, -r PATH     仓库路径 [默认: .]
  
示例:
  python -m cli chat
  python -m cli chat --model deepseek-coder
  python -m cli chat main.py utils.py
```

### 2. 单次编辑文件

```bash
python -m cli edit <文件...> <指令> [选项]

示例:
  python -m cli edit main.py "添加日志功能"
  python -m cli edit *.py "优化性能" --yes
```

### 3. 系统诊断

```bash
python -m cli doctor [--fix]

示例:
  python -m cli doctor          # 检查系统
  python -m cli doctor --fix    # 自动修复问题
```

### 4. 其他命令

```bash
python -m cli config    # 配置管理
python -m cli session   # 会话管理
python -m cli agent     # 列出所有Agent
python -m cli models    # 列出可用模型
python -m cli serve     # 启动HTTP服务器
python -m cli version   # 显示版本信息
```

---

## 对话中的命令

启动对话后，可以使用以下命令：

### 基本命令

```
/help              查看所有命令
/exit, /quit       退出对话
/clear             清空对话历史
/history           查看对话历史
```

### 文件管理

```
/add <file>        添加文件到上下文
/drop <file>       从上下文移除文件
/files             查看已加载的文件
```

### 配置

```
/model [name]      查看或切换模型
/session           查看会话ID
```

### 快捷键

```
Ctrl+C             退出对话
```

---

## 系统特性

### 🤖 智能对话
- 基于18大核心系统
- 完整的记忆系统
- 智能任务路由
- 多Agent协作

### 🛠️ 工具系统
AI可以主动调用以下工具：

1. **repo_map** - 生成智能代码地图
2. **get_repo_structure** - 获取目录树
3. **read_file** - 读取文件内容
4. **search_files** - 搜索文件
5. **grep_search** - 搜索代码

### 📊 优化效果
- 响应速度提升 50-100ms
- Token消耗节省 50-90%
- 文件I/O减少 80%+
- 支持流式输出

---

## 示例对话

### 示例1：了解项目

```
你 › 这个项目的结构是什么？

AI › [自动调用 repo_map 工具]
    
    这是一个智能AI代码助手项目，主要包含：
    
    1. 核心Agent系统 (daoyoucode/agents/)
       - BaseAgent - 基础Agent类
       - Memory系统 - 对话记忆管理
       - Orchestrator - 编排器
    
    2. CLI工具 (cli/)
       - 交互式对话
       - 文件编辑
       - 系统诊断
    
    3. 配置系统 (config/)
       - LLM配置
       - 工具配置
       - 权限规则
```

### 示例2：查看代码

```
你 › Agent系统是怎么实现的？

AI › [自动调用 search_files 和 read_file]
    
    Agent系统的核心实现在 daoyoucode/agents/core/agent.py：
    
    ```python
    class BaseAgent:
        """基础Agent类"""
        
        async def execute(self, prompt_source, user_input, context):
            # 1. 加载记忆
            memory_context = await self.memory.load_context_smart(...)
            
            # 2. 渲染Prompt
            full_prompt = self._render_prompt(...)
            
            # 3. 调用LLM
            response = await self._call_llm(...)
            
            # 4. 保存记忆
            await self.memory.save_conversation(...)
            
            return response
    ```
    
    主要特点：
    - 智能记忆加载
    - 工具调用支持
    - 流式输出
    - 完整的错误处理
```

### 示例3：添加文件

```
你 › /add backend/daoyoucode/agents/core/agent.py

AI › ✓ 已添加文件: backend/daoyoucode/agents/core/agent.py
     500 行, 15000 字符

你 › 这个文件的主要功能是什么？

AI › 这个文件实现了BaseAgent类，是整个Agent系统的核心...
```

---

## 配置要求

### 必需配置

1. **LLM配置** - `backend/config/llm_config.yaml`
   ```yaml
   providers:
     dashscope:
       api_key: "your-api-key"
       models:
         - qwen-max
         - qwen-plus
   ```

2. **Python环境** - Python 3.8+
   ```bash
   pip install -r backend/requirements.txt
   ```

### 可选配置

1. **Memory加载策略** - `backend/config/memory_load_strategies.yaml`
2. **工具配置** - `backend/config/tools_config.yaml`
3. **权限规则** - `backend/config/permissions.yaml`

---

## 故障排除

### 问题1：找不到模块

```bash
# 确保在 backend 目录下运行
cd backend
python -m cli chat
```

### 问题2：LLM配置错误

```bash
# 运行诊断
python -m cli doctor

# 检查配置文件
cat config/llm_config.yaml
```

### 问题3：导入错误

```bash
# 安装依赖
pip install -r requirements.txt

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 性能提示

### 1. 使用合适的模型

- **qwen-max**: 最强能力，适合复杂任务
- **qwen-plus**: 平衡性能和成本
- **qwen-turbo**: 快速响应，适合简单任务

### 2. 加载关键文件

系统会自动加载项目的关键文档（README、STRUCTURE等），你也可以手动添加：

```
/add backend/AGENT_OPTIMIZATION_PLAN.md
/add backend/FINAL_OPTIMIZATION_SUMMARY.md
```

### 3. 清理历史

长对话后可以清理历史以提升性能：

```
/clear
```

---

## 下一步

1. **启动对话**
   ```bash
   cd backend
   python -m cli chat
   ```

2. **尝试提问**
   - "这个项目的结构是什么？"
   - "Agent系统是怎么实现的？"
   - "帮我优化这段代码"

3. **查看文档**
   - `FINAL_OPTIMIZATION_SUMMARY.md` - 系统优化总结
   - `ORCHESTRATOR_REVIEW.md` - 编排器审查报告
   - `REACT_RESERVED_METHODS_GUIDE.md` - ReAct使用指南

---

## 联系支持

如有问题，请查看：
- 📚 文档：`backend/docs/`
- 🐛 问题：GitHub Issues
- 💬 讨论：GitHub Discussions

---

**祝你使用愉快！** 🎉
