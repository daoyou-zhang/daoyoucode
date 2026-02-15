"""
对话树可视化

支持多种可视化格式：
1. Mermaid图（Markdown友好）
2. ASCII树（终端友好）
3. JSON树（程序友好）
4. HTML树（Web友好）
"""

from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


class TreeVisualizer:
    """
    对话树可视化器
    
    功能：
    1. 生成Mermaid图
    2. 生成ASCII树
    3. 生成JSON树
    4. 生成HTML树
    """
    
    def __init__(self, conversation_tree):
        """
        初始化可视化器
        
        Args:
            conversation_tree: ConversationTree实例
        """
        self.tree = conversation_tree
    
    def to_mermaid(self, max_depth: Optional[int] = None) -> str:
        """
        生成Mermaid图
        
        Args:
            max_depth: 最大深度（可选）
        
        Returns:
            Mermaid图代码
        """
        lines = ["graph TD"]
        
        # 获取所有节点
        nodes = self.tree._nodes
        
        if not nodes:
            return "graph TD\n    Empty[\"空树\"]"
        
        # 添加根节点
        lines.append('    Root["🌳 对话树"]')
        
        # 按分支组织节点
        branches = {}
        for node_id, node in nodes.items():
            branch_id = node.branch_id
            if branch_id not in branches:
                branches[branch_id] = []
            branches[branch_id].append((node_id, node))
        
        # 为每个分支生成节点
        for branch_id, branch_nodes in branches.items():
            # 排序（按深度）
            branch_nodes.sort(key=lambda x: x[1].depth)
            
            # 分支起点
            first_node_id, first_node = branch_nodes[0]
            topic = first_node.topic or "未知话题"
            
            # 添加分支节点
            branch_label = f"📁 {topic}"
            lines.append(f'    {branch_id}["{branch_label}"]')
            lines.append(f'    Root --> {branch_id}')
            
            # 添加对话节点
            prev_id = branch_id
            for node_id, node in branch_nodes:
                # 检查深度限制
                if max_depth and node.depth > max_depth:
                    continue
                
                # 节点标签（截断长文本）
                user_msg = node.user_message[:30] + "..." if len(node.user_message) > 30 else node.user_message
                label = f"💬 {user_msg}"
                
                # 添加节点
                safe_id = node_id.replace('-', '_')
                lines.append(f'    {safe_id}["{label}"]')
                lines.append(f'    {prev_id} --> {safe_id}')
                
                prev_id = safe_id
        
        return "\n".join(lines)
    
    def to_ascii(self, max_depth: Optional[int] = None, show_content: bool = False) -> str:
        """
        生成ASCII树
        
        Args:
            max_depth: 最大深度（可选）
            show_content: 是否显示对话内容
        
        Returns:
            ASCII树字符串
        """
        lines = ["🌳 对话树"]
        lines.append("=" * 60)
        
        nodes = self.tree._nodes
        
        if not nodes:
            lines.append("(空树)")
            return "\n".join(lines)
        
        # 按分支组织
        branches = {}
        for node_id, node in nodes.items():
            branch_id = node.branch_id
            if branch_id not in branches:
                branches[branch_id] = []
            branches[branch_id].append((node_id, node))
        
        # 为每个分支生成树
        for idx, (branch_id, branch_nodes) in enumerate(branches.items(), 1):
            # 排序
            branch_nodes.sort(key=lambda x: x[1].depth)
            
            # 分支信息
            first_node = branch_nodes[0][1]
            topic = first_node.topic or "未知话题"
            
            # 分支标题
            is_last_branch = idx == len(branches)
            branch_prefix = "└─" if is_last_branch else "├─"
            lines.append(f"{branch_prefix} 📁 分支 {idx}: {topic} ({len(branch_nodes)}轮)")
            
            # 对话节点
            for j, (node_id, node) in enumerate(branch_nodes):
                # 检查深度限制
                if max_depth and node.depth > max_depth:
                    continue
                
                is_last_node = j == len(branch_nodes) - 1
                node_prefix = "   └─" if is_last_branch else "│  └─" if is_last_node else "│  ├─"
                
                # 节点信息
                user_msg = node.user_message[:40] + "..." if len(node.user_message) > 40 else node.user_message
                lines.append(f"{node_prefix} 💬 {user_msg}")
                
                # 显示内容（可选）
                if show_content:
                    ai_msg = node.ai_response[:60] + "..." if len(node.ai_response) > 60 else node.ai_response
                    content_prefix = "      " if is_last_branch else "│     "
                    lines.append(f"{content_prefix}   ↳ {ai_msg}")
        
        # 统计信息
        lines.append("")
        lines.append("=" * 60)
        stats = self.tree.get_tree_stats()
        lines.append(f"统计: {stats['total_conversations']}轮对话, {stats['total_branches']}个分支")
        
        return "\n".join(lines)
    
    def to_json(self, pretty: bool = True) -> str:
        """
        生成JSON树
        
        Args:
            pretty: 是否格式化
        
        Returns:
            JSON字符串
        """
        nodes = self.tree._nodes
        
        if not nodes:
            return json.dumps({"tree": "empty"}, indent=2 if pretty else None)
        
        # 按分支组织
        branches = {}
        for node_id, node in nodes.items():
            branch_id = node.branch_id
            if branch_id not in branches:
                branches[branch_id] = {
                    'branch_id': branch_id,
                    'topic': node.topic,
                    'conversations': []
                }
            
            branches[branch_id]['conversations'].append({
                'conversation_id': node.conversation_id,
                'user_message': node.user_message,
                'ai_response': node.ai_response,
                'depth': node.depth,
                'timestamp': node.timestamp
            })
        
        # 排序
        for branch in branches.values():
            branch['conversations'].sort(key=lambda x: x['depth'])
        
        tree_data = {
            'tree': list(branches.values()),
            'stats': self.tree.get_tree_stats()
        }
        
        return json.dumps(tree_data, ensure_ascii=False, indent=2 if pretty else None)
    
    def to_html(self, title: str = "对话树") -> str:
        """
        生成HTML树
        
        Args:
            title: 标题
        
        Returns:
            HTML字符串
        """
        nodes = self.tree._nodes
        
        if not nodes:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .empty {{ color: #999; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="empty">空树</p>
</body>
</html>
"""
        
        # 按分支组织
        branches = {}
        for node_id, node in nodes.items():
            branch_id = node.branch_id
            if branch_id not in branches:
                branches[branch_id] = []
            branches[branch_id].append((node_id, node))
        
        # 生成HTML
        html_parts = [f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .stats {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .branch {{
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #2196F3;
            background: #f9f9f9;
        }}
        .branch-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 10px;
        }}
        .conversation {{
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        .user-message {{
            color: #1976D2;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .ai-response {{
            color: #666;
            padding-left: 20px;
            border-left: 3px solid #4CAF50;
        }}
        .metadata {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌳 {title}</h1>
"""]
        
        # 统计信息
        stats = self.tree.get_tree_stats()
        html_parts.append(f"""
        <div class="stats">
            <strong>统计信息：</strong>
            {stats['total_conversations']}轮对话 | 
            {stats['total_branches']}个分支 | 
            当前分支: {stats['current_branch_id']}
        </div>
""")
        
        # 分支和对话
        for idx, (branch_id, branch_nodes) in enumerate(branches.items(), 1):
            # 排序
            branch_nodes.sort(key=lambda x: x[1].depth)
            
            # 分支信息
            first_node = branch_nodes[0][1]
            topic = first_node.topic or "未知话题"
            
            html_parts.append(f"""
        <div class="branch">
            <div class="branch-title">📁 分支 {idx}: {topic} ({len(branch_nodes)}轮)</div>
""")
            
            # 对话节点
            for node_id, node in branch_nodes:
                html_parts.append(f"""
            <div class="conversation">
                <div class="user-message">💬 用户: {self._escape_html(node.user_message)}</div>
                <div class="ai-response">🤖 AI: {self._escape_html(node.ai_response[:200])}{'...' if len(node.ai_response) > 200 else ''}</div>
                <div class="metadata">深度: {node.depth} | 时间: {node.timestamp}</div>
            </div>
""")
            
            html_parts.append("        </div>")
        
        html_parts.append("""
    </div>
</body>
</html>
""")
        
        return "".join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def export_to_file(self, filepath: str, format: str = 'auto'):
        """
        导出到文件
        
        Args:
            filepath: 文件路径
            format: 格式（auto/mermaid/ascii/json/html）
        """
        from pathlib import Path
        
        path = Path(filepath)
        
        # 自动检测格式
        if format == 'auto':
            suffix = path.suffix.lower()
            if suffix == '.md':
                format = 'mermaid'
            elif suffix == '.txt':
                format = 'ascii'
            elif suffix == '.json':
                format = 'json'
            elif suffix == '.html':
                format = 'html'
            else:
                format = 'ascii'
        
        # 生成内容
        if format == 'mermaid':
            content = f"# 对话树\n\n```mermaid\n{self.to_mermaid()}\n```"
        elif format == 'ascii':
            content = self.to_ascii(show_content=True)
        elif format == 'json':
            content = self.to_json(pretty=True)
        elif format == 'html':
            content = self.to_html()
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        # 写入文件
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ 对话树已导出: {filepath} (格式: {format})")


def visualize_tree(conversation_tree, format: str = 'ascii', **kwargs) -> str:
    """
    快捷函数：可视化对话树
    
    Args:
        conversation_tree: ConversationTree实例
        format: 格式（mermaid/ascii/json/html）
        **kwargs: 其他参数
    
    Returns:
        可视化字符串
    """
    visualizer = TreeVisualizer(conversation_tree)
    
    if format == 'mermaid':
        return visualizer.to_mermaid(**kwargs)
    elif format == 'ascii':
        return visualizer.to_ascii(**kwargs)
    elif format == 'json':
        return visualizer.to_json(**kwargs)
    elif format == 'html':
        return visualizer.to_html(**kwargs)
    else:
        raise ValueError(f"不支持的格式: {format}")
