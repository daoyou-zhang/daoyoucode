"""
项目文档工具 - 自动发现和读取项目文档

用于项目理解的第一阶段：文档层
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class DiscoverProjectDocsTool(BaseTool):
    """
    自动发现并读取项目文档
    
    功能：
    - 查找README、ARCHITECTURE等关键文档
    - 提取package.json、pyproject.toml等元信息
    - 智能摘要，提取关键信息
    """
    
    # 文档优先级：根目录优先，再查 backend/、docs/（便于 DaoyouCode 等「更了解自己」）
    README_PATTERNS = [
        "README.md", "README.rst", "README.txt", "README",
        "readme.md", "readme.rst", "readme.txt", "readme",
        "backend/README.md", "docs/README.md",
    ]
    
    ARCHITECTURE_PATTERNS = [
        "ARCHITECTURE.md", "DESIGN.md", "STRUCTURE.md",
        "architecture.md", "design.md", "structure.md",
        "backend/ARCHITECTURE.md", "backend/DESIGN.md",
        "docs/ARCHITECTURE.md", "docs/architecture.md",
    ]
    
    CHANGELOG_PATTERNS = [
        "CHANGELOG.md", "HISTORY.md", "RELEASES.md",
        "changelog.md", "history.md", "releases.md"
    ]
    
    PACKAGE_INFO_PATTERNS = [
        "package.json",
        "pyproject.toml",
        "setup.py",
        "Cargo.toml",
        "go.mod"
    ]
    
    def __init__(self):
        super().__init__(
            name="discover_project_docs",
            description="自动发现并读取项目文档（README、架构文档、包信息等）"
        )
    
    def get_function_schema(self) -> Dict[str, Any]:
        """获取Function Calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "仓库根目录路径。必须使用 '.' 表示当前工作目录，不要使用占位符路径！"
                    },
                    "include_changelog": {
                        "type": "boolean",
                        "description": "是否包含CHANGELOG（默认false，避免过长）",
                        "default": False
                    },
                    "max_doc_length": {
                        "type": "integer",
                        "description": "单个文档最大长度（字符数，默认5000）",
                        "default": 5000
                    }
                },
                "required": ["repo_path"]
            }
        }
    
    async def execute(
        self,
        repo_path: str,
        include_changelog: bool = False,
        max_doc_length: int = 5000
    ) -> ToolResult:
        """
        发现并读取项目文档
        
        Args:
            repo_path: 仓库根目录
            include_changelog: 是否包含CHANGELOG
            max_doc_length: 单个文档最大长度
            
        Returns:
            ToolResult
        """
        try:
            # 使用工具上下文的 resolve_path，与 repo_map 等一致，保证 "." 解析为项目根（非进程 cwd）
            repo_path = self.resolve_path(repo_path)
            if not repo_path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"仓库路径不存在: {repo_path}"
                )
            
            docs = []
            
            # 1. 查找README（必读）；若有根 README 且存在 backend/README，一并纳入（更了解自己）
            readme = self._find_file(repo_path, self.README_PATTERNS)
            if readme:
                content = self._read_file(readme, max_doc_length)
                if content:
                    docs.append({
                        'type': 'README',
                        'path': str(readme.relative_to(repo_path)),
                        'content': content,
                        'summary': self._extract_readme_summary(content)
                    })
                    logger.info(f"✓ 找到README: {readme.name}")
            backend_readme = repo_path / "backend" / "README.md"
            if backend_readme.exists() and backend_readme.is_file() and (not readme or readme != backend_readme):
                content = self._read_file(backend_readme, max_doc_length)
                if content:
                    docs.append({
                        'type': 'README (backend)',
                        'path': str(backend_readme.relative_to(repo_path)),
                        'content': content,
                    })
                    logger.info("✓ 找到 backend/README，一并纳入")
            
            # 2. 查找架构文档
            arch_doc = self._find_file(repo_path, self.ARCHITECTURE_PATTERNS)
            if arch_doc:
                content = self._read_file(arch_doc, max_doc_length)
                if content:
                    docs.append({
                        'type': 'ARCHITECTURE',
                        'path': str(arch_doc.relative_to(repo_path)),
                        'content': content
                    })
                    logger.info(f"✓ 找到架构文档: {arch_doc.name}")
            
            # 3. 查找CHANGELOG（可选）
            if include_changelog:
                changelog = self._find_file(repo_path, self.CHANGELOG_PATTERNS)
                if changelog:
                    content = self._read_file(changelog, max_doc_length)
                    if content:
                        docs.append({
                            'type': 'CHANGELOG',
                            'path': str(changelog.relative_to(repo_path)),
                            'content': content
                        })
                        logger.info(f"✓ 找到CHANGELOG: {changelog.name}")
            
            # 4. 查找包信息
            package_info = self._find_file(repo_path, self.PACKAGE_INFO_PATTERNS)
            if package_info:
                metadata = self._extract_package_metadata(package_info)
                if metadata:
                    docs.append({
                        'type': 'PACKAGE_INFO',
                        'path': str(package_info.relative_to(repo_path)),
                        'content': metadata
                    })
                    logger.info(f"✓ 找到包信息: {package_info.name}")
            
            if not docs:
                return ToolResult(
                    success=True,
                    content="未找到项目文档",
                    metadata={'doc_count': 0}
                )
            
            # 格式化输出
            formatted = self._format_docs(docs)
            
            return ToolResult(
                success=True,
                content=formatted,
                metadata={
                    'doc_count': len(docs),
                    'doc_types': [d['type'] for d in docs],
                    'repo_path': str(repo_path)
                }
            )
            
        except Exception as e:
            logger.error(f"发现项目文档失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _find_file(self, repo_path: Path, patterns: List[str]) -> Optional[Path]:
        """查找文件（按优先级）"""
        for pattern in patterns:
            file_path = repo_path / pattern
            if file_path.exists() and file_path.is_file():
                return file_path
        return None
    
    def _read_file(self, file_path: Path, max_length: int) -> Optional[str]:
        """读取文件内容（限制长度）"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            if len(content) > max_length:
                # 截断，保留开头
                content = content[:max_length] + f"\n\n... (文档过长，已截断，总长度: {len(content)} 字符)"
            
            return content
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return None
    
    def _extract_readme_summary(self, content: str) -> Dict[str, Any]:
        """提取README关键信息"""
        summary = {}
        
        lines = content.split('\n')
        
        # 提取标题（第一个#）
        for line in lines:
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                summary['title'] = title
                break
        
        # 提取描述（第一段非标题文本）
        description_lines = []
        in_description = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_description:
                    break
                continue
            if stripped.startswith('#'):
                in_description = False
                continue
            if not in_description and not stripped.startswith('#'):
                in_description = True
            if in_description:
                description_lines.append(stripped)
                if len(description_lines) >= 3:  # 最多3行
                    break
        
        if description_lines:
            summary['description'] = ' '.join(description_lines)
        
        # 提取特性（Features、核心特性等）
        features = []
        in_features = False
        for line in lines:
            stripped = line.strip()
            if '特性' in stripped or 'feature' in stripped.lower() or 'highlights' in stripped.lower():
                in_features = True
                continue
            if in_features:
                if stripped.startswith('#'):
                    break
                if stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•'):
                    feature = stripped.lstrip('-*•').strip()
                    if feature:
                        features.append(feature)
                        if len(features) >= 5:  # 最多5个
                            break
        
        if features:
            summary['features'] = features
        
        return summary
    
    def _extract_package_metadata(self, file_path: Path) -> Optional[str]:
        """提取包元信息"""
        try:
            if file_path.name == 'package.json':
                return self._extract_package_json(file_path)
            elif file_path.name == 'pyproject.toml':
                return self._extract_pyproject_toml(file_path)
            elif file_path.name == 'setup.py':
                return self._extract_setup_py(file_path)
            elif file_path.name == 'Cargo.toml':
                return self._extract_cargo_toml(file_path)
            elif file_path.name == 'go.mod':
                return self._extract_go_mod(file_path)
        except Exception as e:
            logger.warning(f"提取包信息失败 {file_path}: {e}")
        
        return None
    
    def _extract_package_json(self, file_path: Path) -> str:
        """提取package.json信息"""
        data = json.loads(file_path.read_text(encoding='utf-8'))
        
        info = []
        info.append(f"名称: {data.get('name', 'N/A')}")
        info.append(f"版本: {data.get('version', 'N/A')}")
        
        if 'description' in data:
            info.append(f"描述: {data['description']}")
        
        if 'dependencies' in data:
            deps = list(data['dependencies'].keys())[:10]  # 最多10个
            info.append(f"依赖: {', '.join(deps)}")
        
        if 'scripts' in data:
            scripts = list(data['scripts'].keys())[:5]  # 最多5个
            info.append(f"脚本: {', '.join(scripts)}")
        
        return '\n'.join(info)
    
    def _extract_pyproject_toml(self, file_path: Path) -> str:
        """提取pyproject.toml信息"""
        try:
            import tomli
        except ImportError:
            # 简单解析
            content = file_path.read_text(encoding='utf-8')
            return self._simple_parse_toml(content)
        
        data = tomli.loads(file_path.read_text(encoding='utf-8'))
        
        info = []
        
        if 'project' in data:
            project = data['project']
            info.append(f"名称: {project.get('name', 'N/A')}")
            info.append(f"版本: {project.get('version', 'N/A')}")
            
            if 'description' in project:
                info.append(f"描述: {project['description']}")
            
            if 'dependencies' in project:
                deps = project['dependencies'][:10]  # 最多10个
                info.append(f"依赖: {', '.join(deps)}")
        
        return '\n'.join(info) if info else self._simple_parse_toml(file_path.read_text(encoding='utf-8'))
    
    def _simple_parse_toml(self, content: str) -> str:
        """简单解析TOML（不依赖tomli）"""
        lines = content.split('\n')[:20]  # 只看前20行
        info = []
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                if key in ['name', 'version', 'description']:
                    info.append(f"{key}: {value}")
        
        return '\n'.join(info) if info else "包信息（TOML格式）"
    
    def _extract_setup_py(self, file_path: Path) -> str:
        """提取setup.py信息（简单解析）"""
        content = file_path.read_text(encoding='utf-8')
        
        info = []
        
        # 简单正则提取
        import re
        
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            info.append(f"名称: {name_match.group(1)}")
        
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            info.append(f"版本: {version_match.group(1)}")
        
        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
        if desc_match:
            info.append(f"描述: {desc_match.group(1)}")
        
        return '\n'.join(info) if info else "包信息（setup.py）"
    
    def _extract_cargo_toml(self, file_path: Path) -> str:
        """提取Cargo.toml信息"""
        return self._simple_parse_toml(file_path.read_text(encoding='utf-8'))
    
    def _extract_go_mod(self, file_path: Path) -> str:
        """提取go.mod信息"""
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')[:10]  # 前10行
        
        info = []
        for line in lines:
            line = line.strip()
            if line.startswith('module '):
                info.append(f"模块: {line.replace('module ', '')}")
            elif line.startswith('go '):
                info.append(f"Go版本: {line.replace('go ', '')}")
        
        return '\n'.join(info) if info else "包信息（go.mod）"
    
    def _format_docs(self, docs: List[Dict[str, Any]]) -> str:
        """格式化文档输出"""
        output = ["# 项目文档\n"]
        
        for doc in docs:
            doc_type = doc['type']
            doc_path = doc['path']
            
            output.append(f"\n## {doc_type}")
            output.append(f"文件: {doc_path}\n")
            
            if doc_type == 'README' and 'summary' in doc:
                summary = doc['summary']
                if 'title' in summary:
                    output.append(f"**项目名称**: {summary['title']}")
                if 'description' in summary:
                    output.append(f"**描述**: {summary['description']}")
                if 'features' in summary:
                    output.append("\n**核心特性**:")
                    for i, feature in enumerate(summary['features'], 1):
                        output.append(f"{i}. {feature}")
                output.append("\n**完整内容**:")
            
            output.append(doc['content'])
            output.append("\n" + "-" * 60)
        
        return '\n'.join(output)
