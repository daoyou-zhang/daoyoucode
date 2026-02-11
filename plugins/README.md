# daoyoucode Plugins

独立插件系统，每个插件都是独立的 Python 包。

## 目录结构

```
plugins/
├── lsp-plugin/         # LSP 集成插件
├── git-plugin/         # Git 操作插件
├── ast-plugin/         # AST 工具插件
└── template/           # 插件模板
```

## 创建新插件

```bash
# 复制模板
cp -r template my-plugin

# 编辑插件代码
cd my-plugin/src
# 实现 __init__.py

# 安装插件
pip install -e .
```

## 插件接口

每个插件必须实现 `BasePlugin` 接口：

```python
from daoyoucode.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "我的插件"
    
    def initialize(self, config):
        pass
    
    def execute(self, action, params):
        pass
    
    def cleanup(self):
        pass
```
