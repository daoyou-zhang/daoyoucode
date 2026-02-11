# daoyoucode Frontend

React 前端 Monorepo，包含 TUI、Web 和 Desktop 应用。

## 目录结构

```
frontend/
├── packages/
│   ├── shared/         # 共享代码
│   ├── tui/           # 终端 UI (React Ink)
│   ├── web/           # Web 应用
│   └── desktop/       # 桌面应用 (Electron)
└── turbo.json         # Turbo 配置
```

## 开发

```bash
# 安装依赖
pnpm install

# 开发 TUI
pnpm dev:tui

# 开发 Web
pnpm dev:web

# 开发 Desktop
pnpm dev:desktop

# 构建所有
pnpm build
```
