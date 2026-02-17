# daoyoucode

<div align="center">

**新一代AI编程助手**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)]()

[English](README.md) • [中文文档](README.zh-CN.md)

</div>

---

## 📖 项目简介

**daoyoucode** 是一个融合多智能体协作、LSP重构工具、中文深度优化的新一代开源AI编程助手。

### 核心特性

- 🇨🇳 **中文优先** - 原生中文支持，深度优化国产LLM
- 🤖 **多智能体协作** - 8个专业智能体并行工作
- 🔧 **完整工具链** - LSP重构、AST搜索、Git集成
- 💰 **成本优化** - 智能模型选择，降低使用成本
- 🎯 **开箱即用** - 零配置启动，渐进式复杂度
- 🔌 **高度可扩展** - Hook系统、Skill系统、插件生态

## 🎯 设计理念

daoyoucode 融合了三个优秀项目的核心优势：

- **daoyouCodePilot** - 中文优化、国产LLM深度集成、完整工具链
- **oh-my-opencode** - 多智能体编排、LSP/AST工具、生产力增强
- **OpenCode** - 开源架构、模型无关、可扩展性

## 🚀 快速开始

当前主入口为 **Python 后端**（`backend/`），推荐在项目根目录执行：

```bash
# 依赖（若未装）
pip install -r backend/requirements.txt

# 查看命令
python backend/daoyoucode.py --help

# 交互对话（默认 chat-assistant）
python backend/daoyoucode.py chat

# 单次编辑
python backend/daoyoucode.py edit "把 timeout 改成 60"
```

更多命令与 Skill 用法见 [backend/README.md](backend/README.md)、[backend/CLI命令参考.md](backend/CLI命令参考.md)。

## 📚 文档

| 文档 | 说明 |
|------|------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | **代码级架构一览**（主数据流、关键目录、Cursor/aider/DaoyouCode 如何理解项目）— 人类与 AI 快速理解必读 |
| [backend/README.md](backend/README.md) | 后端文档导航、Skill/编排器/Agent 概念、使用场景 |
| [backend/CLI命令参考.md](backend/CLI命令参考.md) | CLI 命令与示例 |
| [融合系统架构设计方案.md](融合系统架构设计方案.md) | 技术架构与实施计划（规划向） |
| [docs/README.md](docs/README.md) | 文档导航与按角色/主题查阅 |

## 🗺️ 开发路线图

### 当前阶段：阶段0 - 项目初始化 ✅

- [x] 创建项目仓库
- [x] 编写架构设计文档
- [ ] 搭建Monorepo结构
- [ ] 配置开发环境
- [ ] 设置CI/CD

### 下一阶段：阶段1 - 核心引擎（预计4-6周）

- [ ] 实现Orchestrator编排器
- [ ] 实现智能体系统
- [ ] 集成LLM（Qwen, DeepSeek, Claude, GPT）
- [ ] 实现基础工具集

查看完整路线图：[融合系统架构设计方案.md](融合系统架构设计方案.md#61-开发阶段)

## 🏗️ 项目结构

```
daoyoucode/
├── ARCHITECTURE.md    # 代码级架构一览（AI/人类快速理解入口）
├── backend/           # Python 主实现
│   ├── daoyoucode.py  # CLI 入口
│   ├── cli/           # 子命令：chat, edit, doctor, skills 等
│   ├── daoyoucode/    # 核心包
│   │   ├── agents/    # Agent、编排器、工具、LLM、记忆
│   │   └── ...
│   ├── config/        # 配置示例
│   └── README.md      # 后端文档导航
├── skills/            # Skill 配置与 prompt（chat-assistant, oracle 等）
├── docs/              # 文档导航与设计/功能清单
└── config/            # 全局配置
```

## 🤖 AI 与代码级快速理解

- **Cursor**：先读 [ARCHITECTURE.md](ARCHITECTURE.md) 与 [backend/README.md](backend/README.md)，再用 @ 引用 `backend/daoyoucode/agents`、`backend/cli`、`skills` 等目录。
- **aider**：可将 `ARCHITECTURE.md`、`backend/README.md` 加入会话，作为项目上下文。
- **本仓库内置 Agent**：在 chat 中说「了解下项目」或「看看项目」，Agent 会按顺序调用 `discover_project_docs` → `get_repo_structure` → `repo_map`，其中 `discover_project_docs` 会读取本仓库的 README 与 ARCHITECTURE.md，再给出 1～3 句概括。详见 [ARCHITECTURE.md §5–6](ARCHITECTURE.md#5-如何快速理解整个项目cursor-vs-aider-vs-daoyoucode)。

## 🤝 贡献

欢迎贡献！项目正在积极开发中。

- 提交Issue：[GitHub Issues](https://github.com/你的用户名/daoyoucode/issues)
- 提交PR：[Pull Requests](https://github.com/你的用户名/daoyoucode/pulls)
- 加入讨论：[GitHub Discussions](https://github.com/你的用户名/daoyoucode/discussions)

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

本项目受到以下优秀项目的启发：

- [daoyouCodePilot](https://github.com/zhiming/daoyouCodePilot) - 中文AI代码助手
- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) - OpenCode增强插件
- [OpenCode](https://github.com/anomalyco/opencode) - 开源AI编码代理

## 📞 联系方式

- GitHub: [@你的用户名](https://github.com/你的用户名)
- Email: your.email@example.com
- 微信群: （待建立）

---

<div align="center">

**道友同行，智能编程**

Made with ❤️ by daoyoucode Team

</div>
