"""
测试对话树可视化功能

验证各种可视化格式的生成
"""

import tempfile
from pathlib import Path
from daoyoucode.agents.memory.conversation_tree import ConversationTree
from daoyoucode.agents.memory.tree_visualizer import TreeVisualizer, visualize_tree


def create_sample_tree():
    """创建示例对话树"""
    tree = ConversationTree(enabled=True)
    
    # 分支1：猫的健康问题
    tree.add_conversation(
        user_message="我的猫最近不吃饭，怎么办？",
        ai_response="猫不吃饭可能有多种原因，包括肠胃问题、压力、环境变化等。建议先观察是否有其他症状。",
        detect_topic_switch=True
    )
    
    tree.add_conversation(
        user_message="它还有呕吐的症状",
        ai_response="呕吐加上食欲不振，可能是肠胃炎。建议尽快带去宠物医院检查，同时暂时禁食12小时。",
        detect_topic_switch=True
    )
    
    tree.add_conversation(
        user_message="需要做什么检查吗？",
        ai_response="医生可能会做血液检查、X光或超声波检查，以确定具体原因。",
        detect_topic_switch=True
    )
    
    # 分支2：狗的皮肤问题（话题切换）
    tree.add_conversation(
        user_message="那狗的皮肤有红点是怎么回事？",
        ai_response="狗皮肤出现红点可能是过敏、寄生虫或皮肤感染。需要检查红点的分布和狗狗是否有瘙痒症状。",
        detect_topic_switch=True
    )
    
    tree.add_conversation(
        user_message="它一直在挠",
        ai_response="持续瘙痒可能是跳蚤、螨虫或过敏引起的。建议使用驱虫药，并检查是否有食物过敏。",
        detect_topic_switch=True
    )
    
    return tree


def test_ascii_visualization():
    """测试ASCII可视化"""
    print("\n" + "="*60)
    print("测试：ASCII可视化")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 生成ASCII树
    ascii_tree = tree.visualize(format='ascii', show_content=False)
    print("\n" + ascii_tree)
    
    # 带内容的版本
    print("\n" + "="*60)
    print("带内容的ASCII树：")
    print("="*60)
    ascii_tree_full = tree.visualize(format='ascii', show_content=True)
    print("\n" + ascii_tree_full)
    
    print("\n✅ ASCII可视化测试通过")


def test_mermaid_visualization():
    """测试Mermaid可视化"""
    print("\n" + "="*60)
    print("测试：Mermaid可视化")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 生成Mermaid图
    mermaid = tree.visualize(format='mermaid')
    print("\n" + mermaid)
    
    print("\n✅ Mermaid可视化测试通过")
    print("   提示：可以复制上面的代码到 https://mermaid.live 查看图形")


def test_json_visualization():
    """测试JSON可视化"""
    print("\n" + "="*60)
    print("测试：JSON可视化")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 生成JSON
    json_tree = tree.visualize(format='json', pretty=True)
    print("\n" + json_tree)
    
    print("\n✅ JSON可视化测试通过")


def test_html_visualization():
    """测试HTML可视化"""
    print("\n" + "="*60)
    print("测试：HTML可视化")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 生成HTML
    html = tree.visualize(format='html', title="宠物健康咨询对话树")
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        temp_path = f.name
    
    print(f"\n✓ HTML已生成: {temp_path}")
    print(f"   可以在浏览器中打开查看")
    
    # 显示部分HTML
    print("\nHTML预览（前500字符）:")
    print(html[:500] + "...")
    
    print("\n✅ HTML可视化测试通过")
    
    return temp_path


def test_export_to_file():
    """测试导出到文件"""
    print("\n" + "="*60)
    print("测试：导出到文件")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    # 导出各种格式
    formats = {
        'ascii': temp_dir / 'tree.txt',
        'mermaid': temp_dir / 'tree.md',
        'json': temp_dir / 'tree.json',
        'html': temp_dir / 'tree.html'
    }
    
    for format_name, filepath in formats.items():
        tree.export_visualization(str(filepath), format=format_name)
        assert filepath.exists(), f"文件未创建: {filepath}"
        print(f"✓ 导出成功: {filepath} ({format_name})")
    
    print(f"\n所有文件已导出到: {temp_dir}")
    print("\n✅ 导出测试通过")
    
    return temp_dir


def test_empty_tree():
    """测试空树"""
    print("\n" + "="*60)
    print("测试：空树可视化")
    print("="*60)
    
    tree = ConversationTree(enabled=True)
    
    # ASCII
    ascii_tree = tree.visualize(format='ascii')
    print("\nASCII:")
    print(ascii_tree)
    
    # Mermaid
    mermaid = tree.visualize(format='mermaid')
    print("\nMermaid:")
    print(mermaid)
    
    print("\n✅ 空树测试通过")


def test_visualizer_class():
    """测试TreeVisualizer类"""
    print("\n" + "="*60)
    print("测试：TreeVisualizer类")
    print("="*60)
    
    tree = create_sample_tree()
    visualizer = TreeVisualizer(tree)
    
    # 测试各种方法
    print("\n1. to_ascii():")
    ascii_result = visualizer.to_ascii()
    assert len(ascii_result) > 0, "ASCII结果为空"
    print("✓ ASCII生成成功")
    
    print("\n2. to_mermaid():")
    mermaid_result = visualizer.to_mermaid()
    assert "graph TD" in mermaid_result, "Mermaid格式错误"
    print("✓ Mermaid生成成功")
    
    print("\n3. to_json():")
    json_result = visualizer.to_json()
    assert "tree" in json_result, "JSON格式错误"
    print("✓ JSON生成成功")
    
    print("\n4. to_html():")
    html_result = visualizer.to_html()
    assert "<!DOCTYPE html>" in html_result, "HTML格式错误"
    print("✓ HTML生成成功")
    
    print("\n✅ TreeVisualizer类测试通过")


def test_max_depth():
    """测试深度限制"""
    print("\n" + "="*60)
    print("测试：深度限制")
    print("="*60)
    
    tree = create_sample_tree()
    
    # 限制深度为1
    ascii_tree = tree.visualize(format='ascii', max_depth=1)
    print("\n深度限制为1:")
    print(ascii_tree)
    
    # 限制深度为2
    mermaid = tree.visualize(format='mermaid', max_depth=2)
    print("\n深度限制为2 (Mermaid):")
    print(mermaid)
    
    print("\n✅ 深度限制测试通过")


if __name__ == "__main__":
    print("="*60)
    print("对话树可视化测试套件")
    print("="*60)
    
    test_ascii_visualization()
    test_mermaid_visualization()
    test_json_visualization()
    html_path = test_html_visualization()
    export_dir = test_export_to_file()
    test_empty_tree()
    test_visualizer_class()
    test_max_depth()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成")
    print("="*60)
    print(f"\n生成的文件:")
    print(f"  HTML: {html_path}")
    print(f"  导出目录: {export_dir}")
    print("\n提示：可以在浏览器中打开HTML文件查看可视化效果")
