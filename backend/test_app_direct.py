#!/usr/bin/env python
"""直接测试app.py"""

import sys
sys.path.insert(0, '.')

print("开始导入...")

try:
    print("1. 导入typer...")
    import typer
    print("   ✓ typer导入成功")
    
    print("2. 导入cli...")
    import cli
    print(f"   ✓ cli导入成功, version={cli.__version__}")
    
    print("3. 导入cli.app...")
    import cli.app as app_module
    print(f"   ✓ cli.app导入成功")
    print(f"   模块内容: {[x for x in dir(app_module) if not x.startswith('_')]}")
    
    if hasattr(app_module, 'main'):
        print("   ✓ 找到main函数")
        print("   尝试运行 --help...")
        sys.argv = ['test', '--help']
        app_module.main()
    else:
        print("   ✗ 没有找到main函数")
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
