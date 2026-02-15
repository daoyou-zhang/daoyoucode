import sys
sys.path.insert(0, '.')

try:
    import cli.app
    print(f"导入成功")
    print(f"有main函数: {hasattr(cli.app, 'main')}")
    print(f"模块内容: {dir(cli.app)}")
except Exception as e:
    print(f"导入失败: {e}")
    import traceback
    traceback.print_exc()
