"""
测试Memory加载策略配置功能

验证配置加载、验证、热重载等功能
"""

import asyncio
import tempfile
from pathlib import Path
from daoyoucode.agents.memory.load_strategy_config import (
    LoadStrategyConfig, get_load_strategy_config, DEFAULT_STRATEGIES
)
from daoyoucode.agents.memory.smart_loader import SmartLoader


def test_default_config():
    """测试默认配置"""
    print("\n" + "="*60)
    print("测试：默认配置")
    print("="*60)
    
    config = LoadStrategyConfig()
    
    # 检查默认策略
    strategies = config.get_all_strategies()
    print(f"\n默认策略数量: {len(strategies)}")
    
    for name, strategy in strategies.items():
        cost = strategy.get('cost', 0)
        desc = strategy.get('description', '无描述')
        print(f"  - {name}: cost={cost}, {desc}")
    
    # 验证必需策略存在
    required = ['new_conversation', 'simple_followup', 'medium_followup', 'complex_followup']
    for name in required:
        assert name in strategies, f"缺少必需策略: {name}"
    
    print("\n✅ 默认配置测试通过")


def test_load_from_yaml():
    """测试从YAML文件加载"""
    print("\n" + "="*60)
    print("测试：从YAML文件加载")
    print("="*60)
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write("""
strategies:
  custom_strategy:
    load_history: true
    history_limit: 5
    load_summary: true
    cost: 4
    description: "自定义策略"
  
  simple_followup:
    load_history: true
    history_limit: 1  # 覆盖默认值
    cost: 0.5
""")
        temp_path = f.name
    
    try:
        # 加载配置
        config = LoadStrategyConfig(temp_path)
        
        # 检查自定义策略
        custom = config.get_strategy('custom_strategy')
        assert custom is not None, "自定义策略未加载"
        assert custom['history_limit'] == 5, "自定义策略参数错误"
        print(f"✓ 自定义策略: {custom}")
        
        # 检查覆盖的策略
        simple = config.get_strategy('simple_followup')
        assert simple['history_limit'] == 1, "策略覆盖失败"
        assert simple['cost'] == 0.5, "策略覆盖失败"
        print(f"✓ 覆盖策略: {simple}")
        
        # 检查默认策略仍然存在
        medium = config.get_strategy('medium_followup')
        assert medium is not None, "默认策略丢失"
        print(f"✓ 默认策略保留: {medium}")
        
        print("\n✅ YAML加载测试通过")
    
    finally:
        Path(temp_path).unlink()


def test_load_from_json():
    """测试从JSON文件加载"""
    print("\n" + "="*60)
    print("测试：从JSON文件加载")
    print("="*60)
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write("""{
  "strategies": {
    "json_strategy": {
      "load_history": true,
      "history_limit": 7,
      "cost": 6,
      "description": "JSON策略"
    }
  }
}""")
        temp_path = f.name
    
    try:
        # 加载配置
        config = LoadStrategyConfig(temp_path)
        
        # 检查JSON策略
        json_strategy = config.get_strategy('json_strategy')
        assert json_strategy is not None, "JSON策略未加载"
        assert json_strategy['history_limit'] == 7, "JSON策略参数错误"
        print(f"✓ JSON策略: {json_strategy}")
        
        print("\n✅ JSON加载测试通过")
    
    finally:
        Path(temp_path).unlink()


def test_add_and_remove_strategy():
    """测试添加和删除策略"""
    print("\n" + "="*60)
    print("测试：添加和删除策略")
    print("="*60)
    
    config = LoadStrategyConfig()
    
    # 添加策略
    new_strategy = {
        'load_history': True,
        'history_limit': 8,
        'cost': 7
    }
    config.add_strategy('test_strategy', new_strategy)
    
    # 验证添加
    strategy = config.get_strategy('test_strategy')
    assert strategy is not None, "策略添加失败"
    assert strategy['history_limit'] == 8, "策略参数错误"
    print(f"✓ 添加策略成功: {strategy}")
    
    # 删除策略
    success = config.remove_strategy('test_strategy')
    assert success, "策略删除失败"
    
    # 验证删除
    strategy = config.get_strategy('test_strategy')
    assert strategy is None, "策略删除后仍存在"
    print(f"✓ 删除策略成功")
    
    print("\n✅ 添加删除测试通过")


def test_save_and_reload():
    """测试保存和重载"""
    print("\n" + "="*60)
    print("测试：保存和重载")
    print("="*60)
    
    # 创建临时文件路径
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        # 创建配置并添加自定义策略
        config = LoadStrategyConfig()
        config.add_strategy('saved_strategy', {
            'load_history': True,
            'history_limit': 9,
            'cost': 8
        })
        
        # 保存到文件
        success = config.save_to_file(temp_path)
        assert success, "保存失败"
        print(f"✓ 保存成功: {temp_path}")
        
        # 创建新配置实例并加载
        config2 = LoadStrategyConfig(temp_path)
        
        # 验证加载
        strategy = config2.get_strategy('saved_strategy')
        assert strategy is not None, "重载后策略丢失"
        assert strategy['history_limit'] == 9, "重载后策略参数错误"
        print(f"✓ 重载成功: {strategy}")
        
        print("\n✅ 保存重载测试通过")
    
    finally:
        Path(temp_path).unlink()


def test_export_default_config():
    """测试导出默认配置"""
    print("\n" + "="*60)
    print("测试：导出默认配置")
    print("="*60)
    
    # 创建临时文件路径
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        config = LoadStrategyConfig()
        
        # 导出默认配置
        success = config.export_default_config(temp_path)
        assert success, "导出失败"
        print(f"✓ 导出成功: {temp_path}")
        
        # 验证文件存在
        assert Path(temp_path).exists(), "导出文件不存在"
        
        # 加载并验证
        config2 = LoadStrategyConfig(temp_path)
        strategies = config2.get_all_strategies()
        
        # 应该包含所有默认策略
        for name in DEFAULT_STRATEGIES.keys():
            assert name in strategies, f"默认策略 {name} 丢失"
        
        print(f"✓ 验证成功: {len(strategies)} 个策略")
        
        print("\n✅ 导出默认配置测试通过")
    
    finally:
        Path(temp_path).unlink()


def test_smart_loader_integration():
    """测试SmartLoader集成"""
    print("\n" + "="*60)
    print("测试：SmartLoader集成")
    print("="*60)
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write("""
strategies:
  custom_simple:
    load_history: true
    history_limit: 1
    cost: 0.5
    description: "自定义简单策略"
""")
        temp_path = f.name
    
    try:
        # 创建SmartLoader（使用自定义配置）
        loader = SmartLoader(enable_tree=False, config_path=temp_path)
        
        # 检查策略是否加载
        strategies = loader.list_strategies()
        print(f"✓ 加载的策略: {strategies}")
        
        assert 'custom_simple' in strategies, "自定义策略未加载到SmartLoader"
        
        # 获取策略信息
        info = loader.get_strategy_info('custom_simple')
        assert info is not None, "无法获取策略信息"
        assert info['history_limit'] == 1, "策略参数错误"
        print(f"✓ 策略信息: {info}")
        
        # 测试热重载
        print("\n测试热重载...")
        success = loader.reload_config()
        assert success, "热重载失败"
        print(f"✓ 热重载成功")
        
        print("\n✅ SmartLoader集成测试通过")
    
    finally:
        Path(temp_path).unlink()


def test_config_stats():
    """测试配置统计"""
    print("\n" + "="*60)
    print("测试：配置统计")
    print("="*60)
    
    config = LoadStrategyConfig()
    
    # 获取统计信息
    stats = config.get_stats()
    
    print("\n配置统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    assert stats['total_strategies'] > 0, "策略数量为0"
    assert len(stats['strategy_names']) == stats['total_strategies'], "策略名称数量不匹配"
    
    print("\n✅ 配置统计测试通过")


if __name__ == "__main__":
    print("="*60)
    print("Memory加载策略配置测试套件")
    print("="*60)
    
    test_default_config()
    test_load_from_yaml()
    test_load_from_json()
    test_add_and_remove_strategy()
    test_save_and_reload()
    test_export_default_config()
    test_smart_loader_integration()
    test_config_stats()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成")
    print("="*60)
