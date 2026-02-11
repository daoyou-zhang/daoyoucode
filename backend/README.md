# daoyoucode Backend

Python 后端服务，包含核心引擎、智能体系统和工具集。

## 目录结构

```
backend/
├── daoyoucode/          # 主包
│   ├── api/            # FastAPI 接口
│   ├── core/           # 核心编排器
│   ├── agents/         # 智能体系统
│   ├── tools/          # 工具集
│   ├── llm/            # LLM 集成
│   ├── plugins/        # 插件管理
│   ├── skills/         # Skill 系统
│   ├── hooks/          # Hook 系统
│   ├── storage/        # 存储层
│   └── utils/          # 工具函数
├── cli/                # CLI 工具
└── tests/              # 测试
```

## 开发

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 启动服务
uvicorn daoyoucode.api.main:app --reload
```
