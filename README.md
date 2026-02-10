# daoyoucode

<div align="center">

**新一代AI编程助手**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue.svg)](https://www.typescriptlang.org/)
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

> ⚠️ 项目正在开发中，敬请期待！

```bash
# 安装（开发中）
npm install -g daoyoucode

# 启动
daoyoucode

# 或使用简写
dyc
```

## 📚 文档

- [架构设计方案](融合系统架构设计方案.md) - 完整的技术架构和实施计划
- [开发指南](docs/DEVELOPMENT.md) - 开发者文档（即将推出）
- [用户手册](docs/USER_GUIDE.md) - 使用说明（即将推出）
- [API文档](docs/API.md) - API参考（即将推出）

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
├── packages/           # Monorepo包
│   ├── core/          # 核心引擎
│   ├── cli/           # 命令行工具
│   ├── tui/           # 终端UI
│   ├── gui/           # 桌面应用
│   ├── lsp/           # LSP集成
│   └── ast/           # AST工具
├── plugins/           # 插件
├── skills/            # 内置Skills
├── docs/              # 文档
└── examples/          # 示例
```

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
