#!/usr/bin/env python
"""测试重新加载"""

import sys
import importlib
sys.path.insert(0, '.')

# 清除缓存
if 'cli' in sys.modules:
    del sys.modules['cli']
if 'cli.app' in sys.modules:
    del sys.modules['cli.app']

print("导入cli.app...")
import cli.app

print(f"模块内容: {[x for x in dir(cli.app) if not x.startswith('_')]}")
print(f"有main: {hasattr(cli.app, 'main')}")
print(f"有app: {hasattr(cli.app, 'app')}")

if hasattr(cli.app, 'app'):
    print(f"app类型: {type(cli.app.app)}")
    print(f"app命令数: {len(cli.app.app.registered_commands)}")
