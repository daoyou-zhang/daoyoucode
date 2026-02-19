"""
快速检查所有编排器

检查项：
1. 占位符路径问题
2. 超时配置
3. 错误处理
4. 基本功能
"""

import sys
from pathlib import Path
import asyncio
import logging
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加backend到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO, format='%(message)s')

from daoyoucode.agents.orchestrators import (
    SimpleOrchestrator,
    MultiAgentOrchestrator,
    WorkflowOrchestrator,
    ConditionalOrchestrator,
    ParallelOrchestrator,
    ParallelExploreOrchestrator,
    ReActOrchestrator
)


def check_orchestrator_code(orchestrator_name: str, file_path: Path):
    """检查编排器代码"""
    print(f"\n{'='*60}")
    print(f"检查: {orchestrator_name}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # 1. 检查占位符路径（排除条件表达式）
        import re
        placeholders = re.findall(r'\{SKILL_DIR\}|\{REPO_ROOT\}', content)
        if placeholders:
            issues.append(f"⚠️ 发现占位符路径: {set(placeholders)}")
        else:
            print("✅ 无占位符路径问题")
        
        # 2. 检查超时配置
        has_timeout = 'timeout' in content.lower()
        if has_timeout:
            print("✅ 有超时相关代码")
        else:
            issues.append("⚠️ 缺少超时配置")
        
        # 3. 检查错误处理
        try_count = content.count('try:')
        except_count = content.count('except')
        if try_count > 0 and except_count > 0:
            print(f"✅ 有错误处理 (try: {try_count}, except: {except_count})")
        else:
            issues.append(f"⚠️ 错误处理不足 (try: {try_count}, except: {except_count})")
        
        # 4. 检查日志记录
        logger_count = content.count('logger.')
        if logger_count > 5:
            print(f"✅ 有日志记录 ({logger_count} 处)")
        else:
            issues.append(f"⚠️ 日志记录较少 ({logger_count} 处)")
        
        # 5. 检查异步处理
        has_async = 'async def' in content
        has_await = 'await' in content
        if has_async and has_await:
            print("✅ 正确使用异步")
        else:
            issues.append("⚠️ 异步使用可能有问题")
        
        # 总结
        if issues:
            print(f"\n发现 {len(issues)} 个潜在问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✅ 所有检查通过")
        
        return len(issues) == 0
    
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def check_orchestrator_instantiation(orchestrator_class, name: str):
    """检查编排器是否能正常实例化"""
    print(f"\n测试实例化: {name}")
    try:
        orchestrator = orchestrator_class()
        print(f"  ✅ 实例化成功")
        
        # 检查基本属性
        if hasattr(orchestrator, 'get_name'):
            print(f"  ✅ 有get_name方法: {orchestrator.get_name()}")
        
        if hasattr(orchestrator, 'get_description'):
            desc = orchestrator.get_description()
            print(f"  ✅ 有get_description方法: {desc[:50]}...")
        
        return True
    
    except Exception as e:
        print(f"  ❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("编排器快速检查")
    print("="*60)
    
    orchestrators = [
        ('SimpleOrchestrator', SimpleOrchestrator, 'simple.py'),
        ('MultiAgentOrchestrator', MultiAgentOrchestrator, 'multi_agent.py'),
        ('WorkflowOrchestrator', WorkflowOrchestrator, 'workflow.py'),
        ('ConditionalOrchestrator', ConditionalOrchestrator, 'conditional.py'),
        ('ParallelOrchestrator', ParallelOrchestrator, 'parallel.py'),
        ('ParallelExploreOrchestrator', ParallelExploreOrchestrator, 'parallel_explore.py'),
        ('ReActOrchestrator', ReActOrchestrator, 'react.py'),
    ]
    
    results = []
    
    for name, cls, filename in orchestrators:
        # 检查代码
        file_path = backend_dir / 'daoyoucode' / 'agents' / 'orchestrators' / filename
        code_ok = check_orchestrator_code(name, file_path)
        
        # 检查实例化
        inst_ok = check_orchestrator_instantiation(cls, name)
        
        results.append((name, code_ok and inst_ok))
    
    # 总结
    print("\n" + "="*60)
    print("检查总结")
    print("="*60)
    
    for name, ok in results:
        status = "✅ 通过" if ok else "⚠️ 需要检查"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有编排器检查通过！")
    else:
        print(f"\n⚠️ 有 {total - passed} 个编排器需要检查")


if __name__ == "__main__":
    main()
