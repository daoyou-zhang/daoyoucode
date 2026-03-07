import importlib
import inspect
import os
from typing import List, Tuple

# 定义一个函数来获取给定模块中的所有函数
def get_all_functions(module_name: str) -> List[Tuple[str, str]]:
    try:
        module = importlib.import_module(module_name)
        functions = [
            (name, func.__module__)
            for name, func in inspect.getmembers(module, inspect.isfunction)
        ]
        return functions
    except ImportError as e:
        print(f"Could not import {module_name}: {e}")
        return []

# 定义一个函数来检查函数是否被使用
def is_function_used(function_name: str, function_module: str, project_root: str) -> bool:
    # 构造grep命令来查找函数名
    cmd = f"grep -r --include=*.py '{function_name}' {project_root}"
    result = os.popen(cmd).read()
    # 如果结果为空，说明函数没有被使用
    return result != ''

# 主测试函数
def test_unused_functions():
    # 搜索所有包含'def'的关键字的文件和行
    search_results = [
        {'file': 'hello_world.py', 'line': 4, 'content': '    def __init__(self, value):', 'match': 'def '},
        # ... 其他搜索结果 ...
        {'file': 'backend\cli\utils\errors.py', 'line': 78, 'content': 'def handle_error(error: Exception):', 'match': 'def '}
    ]
    
    # 提取所有函数名及其所在模块
    all_functions = []
    for result in search_results:
        file_path = result['file']
        if file_path.endswith('.py'):
            module_name = file_path.replace(os.sep, '.').rstrip('.py')
            line_content = result['content'].strip()
            if line_content.startswith('def '):
                function_name = line_content.split('(')[0].split(' ')[1]
                all_functions.append((function_name, module_name))
    
    # 检查每个函数是否被使用
    unused_functions = []
    for function_name, function_module in all_functions:
        if not is_function_used(function_name, function_module, project_root='.'):
            unused_functions.append((function_name, function_module))
    
    # 断言没有未使用的函数
    assert len(unused_functions) == 0, f"Found unused functions: {unused_functions}"

if __name__ == "__main__":
    test_unused_functions()
