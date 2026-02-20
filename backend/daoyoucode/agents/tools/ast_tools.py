"""
AST工具 - 基于ast-grep的AST级别代码搜索和替换

采用先进的AST分析技术
特点：
1. AST级别的精确匹配（不是文本匹配）
2. 支持25种语言
3. 元变量支持（$VAR, $$）
4. 智能提示和错误处理
5. 自动下载和管理ast-grep二进制

对比结论：
- DaoyouCode ✅ 独有：ast-grep集成，25种语言，智能提示
"""

import asyncio
import json
import os
import platform
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


# 支持的语言（25种）
SUPPORTED_LANGUAGES = [
    "bash", "c", "cpp", "csharp", "css", "elixir", "go", "haskell",
    "html", "java", "javascript", "json", "kotlin", "lua", "nix",
    "php", "python", "ruby", "rust", "scala", "solidity", "swift",
    "typescript", "tsx", "yaml"
]

# 默认配置
DEFAULT_TIMEOUT_MS = 300_000  # 5分钟
DEFAULT_MAX_OUTPUT_BYTES = 1 * 1024 * 1024  # 1MB
DEFAULT_MAX_MATCHES = 500


@dataclass
class Position:
    """位置信息"""
    line: int
    column: int


@dataclass
class Range:
    """范围信息"""
    start: Position
    end: Position


@dataclass
class Match:
    """匹配结果"""
    file: str
    text: str
    range: Range
    lines: str


@dataclass
class SearchResult:
    """搜索结果"""
    matches: List[Match]
    total_matches: int
    truncated: bool
    truncated_reason: Optional[str] = None
    error: Optional[str] = None


class AstGrepManager:
    """
    ast-grep二进制管理器
    
    职责：
    1. 查找已安装的ast-grep
    2. 自动下载ast-grep二进制
    3. 管理缓存目录
    4. 检查NAPI可用性（环境诊断）
    
    注意：只使用CLI模式，不使用NAPI
    """
    
    # GitHub仓库
    REPO = "ast-grep/ast-grep"
    DEFAULT_VERSION = "0.40.0"
    
    # NAPI支持的语言（5种）
    NAPI_LANGUAGES = ["html", "javascript", "tsx", "css", "typescript"]
    
    # 平台映射
    PLATFORM_MAP = {
        "Darwin-arm64": {"arch": "aarch64", "os": "apple-darwin"},
        "Darwin-x86_64": {"arch": "x86_64", "os": "apple-darwin"},
        "Linux-aarch64": {"arch": "aarch64", "os": "unknown-linux-gnu"},
        "Linux-x86_64": {"arch": "x86_64", "os": "unknown-linux-gnu"},
        "Windows-AMD64": {"arch": "x86_64", "os": "pc-windows-msvc"},
        "Windows-ARM64": {"arch": "aarch64", "os": "pc-windows-msvc"},
    }
    
    def __init__(self):
        self._binary_path: Optional[str] = None
        self._cache_dir = self._get_cache_dir()
        self._napi_available: Optional[bool] = None
    
    def _get_cache_dir(self) -> Path:
        """获取缓存目录"""
        if platform.system() == "Windows":
            base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            if not base:
                base = Path.home() / "AppData" / "Local"
            else:
                base = Path(base)
            return base / "daoyoucode" / "bin"
        else:
            base = os.environ.get("XDG_CACHE_HOME")
            if not base:
                base = Path.home() / ".cache"
            else:
                base = Path(base)
            return base / "daoyoucode" / "bin"
    
    def _get_binary_name(self) -> str:
        """获取二进制文件名"""
        return "sg.exe" if platform.system() == "Windows" else "sg"
    
    def _get_cached_binary_path(self) -> Optional[Path]:
        """获取缓存的二进制路径"""
        binary_path = self._cache_dir / self._get_binary_name()
        return binary_path if binary_path.exists() else None
    
    def _find_system_binary(self) -> Optional[str]:
        """查找系统中已安装的ast-grep"""
        # 1. 检查PATH中的sg命令
        sg_path = shutil.which("sg")
        if sg_path:
            return sg_path
        
        # 2. 检查常见安装位置（macOS Homebrew）
        if platform.system() == "Darwin":
            homebrew_paths = [
                "/opt/homebrew/bin/sg",
                "/usr/local/bin/sg"
            ]
            for path in homebrew_paths:
                if Path(path).exists():
                    return path
        
        return None
    
    async def get_binary_path(self) -> Optional[str]:
        """
        获取ast-grep二进制路径
        
        优先级：
        1. 缓存的路径
        2. 系统安装的sg命令
        3. 自动下载
        
        Returns:
            二进制路径，如果失败返回None
        """
        # 1. 检查缓存
        if self._binary_path and Path(self._binary_path).exists():
            return self._binary_path
        
        # 2. 检查缓存目录
        cached_path = self._get_cached_binary_path()
        if cached_path:
            self._binary_path = str(cached_path)
            return self._binary_path
        
        # 3. 检查系统安装
        system_path = self._find_system_binary()
        if system_path:
            self._binary_path = system_path
            logger.info(f"使用系统安装的ast-grep: {system_path}")
            return self._binary_path
        
        # 4. 自动下载
        logger.info("ast-grep未安装，开始自动下载...")
        downloaded_path = await self._download_binary()
        if downloaded_path:
            self._binary_path = str(downloaded_path)
            return self._binary_path
        
        return None
    
    async def _download_binary(self, version: str = DEFAULT_VERSION) -> Optional[Path]:
        """
        下载ast-grep二进制
        
        Args:
            version: 版本号
        
        Returns:
            下载的二进制路径，如果失败返回None
        """
        # 获取平台信息
        system = platform.system()
        machine = platform.machine()
        platform_key = f"{system}-{machine}"
        
        platform_info = self.PLATFORM_MAP.get(platform_key)
        if not platform_info:
            logger.error(f"不支持的平台: {platform_key}")
            return None
        
        # 构建下载URL
        arch = platform_info["arch"]
        os_name = platform_info["os"]
        asset_name = f"app-{arch}-{os_name}.zip"
        download_url = f"https://github.com/{self.REPO}/releases/download/{version}/{asset_name}"
        
        logger.info(f"下载URL: {download_url}")
        
        try:
            # 创建缓存目录
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            import urllib.request
            archive_path = self._cache_dir / asset_name
            
            logger.info(f"正在下载到: {archive_path}")
            urllib.request.urlretrieve(download_url, archive_path)
            
            # 解压
            logger.info("正在解压...")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self._cache_dir)
            
            # 删除压缩包
            archive_path.unlink()
            
            # 设置执行权限（Unix系统）
            binary_path = self._cache_dir / self._get_binary_name()
            if platform.system() != "Windows":
                os.chmod(binary_path, 0o755)
            
            logger.info(f"ast-grep下载完成: {binary_path}")
            return binary_path
            
        except Exception as e:
            logger.error(f"下载ast-grep失败: {e}", exc_info=True)
            return None
    
    def is_available(self) -> bool:
        """检查ast-grep是否可用"""
        return self._binary_path is not None or self._find_system_binary() is not None


# 全局管理器实例
_ast_grep_manager = AstGrepManager()


class AstGrepSearchTool(BaseTool):
    """
    AST级别的代码搜索工具
    
    功能：
    1. 使用AST模式匹配代码
    2. 支持元变量（$VAR, $$）
    3. 支持25种语言
    4. 智能提示和错误处理
    
    示例：
    - 搜索所有console.log: pattern='console.log($MSG)'
    - 搜索所有函数定义: pattern='def $FUNC($$):'
    - 搜索所有async函数: pattern='async function $NAME($$) { $$ }'
    """
    
    def __init__(self):
        super().__init__(
            name="ast_grep_search",
            description="""Search code patterns using AST-aware matching. Supports 25 languages.

Use meta-variables:
- $VAR: matches single node
- $$: matches multiple nodes

IMPORTANT: Patterns must be complete AST nodes (valid code).
For functions, include params and body.

Examples:
- console.log($MSG)
- def $FUNC($$):
- async function $NAME($$) { $$ }

Supported languages: bash, c, cpp, csharp, css, elixir, go, haskell, html, java, javascript, json, kotlin, lua, nix, php, python, ruby, rust, scala, solidity, swift, typescript, tsx, yaml"""
        )
        self.parameters = {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "AST pattern with meta-variables ($VAR, $$). Must be complete AST node."
                },
                "lang": {
                    "type": "string",
                    "enum": SUPPORTED_LANGUAGES,
                    "description": "Target language"
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to search (default: ['.'])",
                    "default": ["."]
                },
                "globs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Include/exclude globs (prefix ! to exclude)",
                    "default": []
                },
                "context": {
                    "type": "integer",
                    "description": "Context lines around match",
                    "default": 0
                }
            },
            "required": ["pattern", "lang"]
        }
    
    async def execute(
        self,
        pattern: str,
        lang: str,
        paths: Optional[List[str]] = None,
        globs: Optional[List[str]] = None,
        context: int = 0
    ) -> ToolResult:
        """
        执行AST搜索
        
        Args:
            pattern: AST模式
            lang: 目标语言
            paths: 搜索路径
            globs: 包含/排除模式
            context: 上下文行数
        
        Returns:
            搜索结果
        """
        try:
            # 获取ast-grep二进制
            binary_path = await _ast_grep_manager.get_binary_path()
            if not binary_path:
                return ToolResult(
                    success=False,
                    content="",
                    error="ast-grep not available. Install: pip install ast-grep-cli or cargo install ast-grep"
                )
            
            # 构建命令
            args = [
                binary_path,
                "run",
                "-p", pattern,
                "--lang", lang,
                "--json=compact"
            ]
            
            if context > 0:
                args.extend(["-C", str(context)])
            
            if globs:
                for glob in globs:
                    args.extend(["--globs", glob])
            
            if not paths:
                paths = ["."]
            args.extend(paths)
            
            # 执行命令
            logger.debug(f"执行命令: {' '.join(args)}")
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=DEFAULT_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Search timeout after {DEFAULT_TIMEOUT_MS}ms"
                )
            
            # 解析结果
            result = self._parse_result(stdout, stderr, process.returncode)
            
            # 格式化输出
            output = self._format_result(result, pattern, lang)
            
            return ToolResult(
                success=not result.error,
                content=output,
                error=result.error,
                metadata={
                    "total_matches": result.total_matches,
                    "truncated": result.truncated,
                    "truncated_reason": result.truncated_reason
                }
            )
            
        except Exception as e:
            logger.error(f"AST搜索失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content="",
                error=f"AST search failed: {str(e)}"
            )
    
    def _parse_result(
        self,
        stdout: bytes,
        stderr: bytes,
        returncode: int
    ) -> SearchResult:
        """解析命令输出"""
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        # 检查错误
        if returncode != 0 and not stdout_str.strip():
            if "No files found" in stderr_str:
                return SearchResult(matches=[], total_matches=0, truncated=False)
            if stderr_str.strip():
                return SearchResult(
                    matches=[],
                    total_matches=0,
                    truncated=False,
                    error=stderr_str.strip()
                )
            return SearchResult(matches=[], total_matches=0, truncated=False)
        
        # 空结果
        if not stdout_str.strip():
            return SearchResult(matches=[], total_matches=0, truncated=False)
        
        # 检查输出是否被截断
        output_truncated = len(stdout) >= DEFAULT_MAX_OUTPUT_BYTES
        output_to_process = stdout_str[:DEFAULT_MAX_OUTPUT_BYTES] if output_truncated else stdout_str
        
        # 解析JSON
        try:
            raw_matches = json.loads(output_to_process)
        except json.JSONDecodeError:
            # 如果被截断，尝试修复JSON
            if output_truncated:
                try:
                    last_valid = output_to_process.rfind("}")
                    if last_valid > 0:
                        bracket_index = output_to_process.rfind("},", last_valid)
                        if bracket_index > 0:
                            truncated_json = output_to_process[:bracket_index + 1] + "]"
                            raw_matches = json.loads(truncated_json)
                        else:
                            return SearchResult(
                                matches=[],
                                total_matches=0,
                                truncated=True,
                                truncated_reason="max_output_bytes",
                                error="Output too large and could not be parsed"
                            )
                    else:
                        return SearchResult(
                            matches=[],
                            total_matches=0,
                            truncated=True,
                            truncated_reason="max_output_bytes",
                            error="Output too large and could not be parsed"
                        )
                except json.JSONDecodeError:
                    return SearchResult(
                        matches=[],
                        total_matches=0,
                        truncated=True,
                        truncated_reason="max_output_bytes",
                        error="Output too large and could not be parsed"
                    )
            else:
                return SearchResult(matches=[], total_matches=0, truncated=False)
        
        # 转换为Match对象
        matches = []
        for raw_match in raw_matches:
            try:
                match = Match(
                    file=raw_match["file"],
                    text=raw_match["text"],
                    range=Range(
                        start=Position(
                            line=raw_match["range"]["start"]["line"],
                            column=raw_match["range"]["start"]["column"]
                        ),
                        end=Position(
                            line=raw_match["range"]["end"]["line"],
                            column=raw_match["range"]["end"]["column"]
                        )
                    ),
                    lines=raw_match.get("lines", "")
                )
                matches.append(match)
            except (KeyError, TypeError) as e:
                logger.warning(f"解析匹配失败: {e}")
                continue
        
        # 检查是否超过最大匹配数
        total_matches = len(matches)
        matches_truncated = total_matches > DEFAULT_MAX_MATCHES
        final_matches = matches[:DEFAULT_MAX_MATCHES] if matches_truncated else matches
        
        return SearchResult(
            matches=final_matches,
            total_matches=total_matches,
            truncated=output_truncated or matches_truncated,
            truncated_reason="max_output_bytes" if output_truncated else "max_matches" if matches_truncated else None
        )
    
    def _format_result(
        self,
        result: SearchResult,
        pattern: str,
        lang: str
    ) -> str:
        """格式化搜索结果"""
        if result.error:
            return f"Error: {result.error}"
        
        if not result.matches:
            # 提供智能提示
            hint = self._get_empty_result_hint(pattern, lang)
            output = "No matches found"
            if hint:
                output += f"\n\n{hint}"
            return output
        
        lines = []
        
        # 截断警告
        if result.truncated:
            reason = {
                "max_matches": f"showing first {len(result.matches)} of {result.total_matches}",
                "max_output_bytes": "output exceeded 1MB limit",
                "timeout": "search timed out"
            }.get(result.truncated_reason, "unknown reason")
            lines.append(f"⚠️ Results truncated ({reason})\n")
        
        # 匹配数量
        truncated_info = f" (truncated from {result.total_matches})" if result.truncated else ""
        lines.append(f"Found {len(result.matches)} match(es){truncated_info}:\n")
        
        # 每个匹配
        for match in result.matches:
            loc = f"{match.file}:{match.range.start.line + 1}:{match.range.start.column + 1}"
            lines.append(f"{loc}")
            lines.append(f"  {match.lines.strip()}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_empty_result_hint(self, pattern: str, lang: str) -> Optional[str]:
        """为空结果提供智能提示"""
        src = pattern.strip()
        
        # Python提示
        if lang == "python":
            if src.startswith("class ") and src.endswith(":"):
                return f"💡 Hint: Remove trailing colon. Try: \"{src[:-1]}\""
            if (src.startswith("def ") or src.startswith("async def ")) and src.endswith(":"):
                return f"💡 Hint: Remove trailing colon. Try: \"{src[:-1]}\""
        
        # JavaScript/TypeScript提示
        if lang in ["javascript", "typescript", "tsx"]:
            import re
            if re.match(r"^(export\s+)?(async\s+)?function\s+\$[A-Z_]+\s*$", src, re.IGNORECASE):
                return "💡 Hint: Function patterns need params and body. Try \"function $NAME($$) { $$ }\""
        
        return None


class AstGrepReplaceTool(BaseTool):
    """
    AST级别的代码替换工具
    
    功能：
    1. 使用AST模式匹配和替换代码
    2. 支持元变量在替换中使用
    3. 默认dry-run模式（预览）
    4. 支持25种语言
    
    示例：
    - 替换console.log为logger.info:
      pattern='console.log($MSG)'
      rewrite='logger.info($MSG)'
    """
    
    def __init__(self):
        super().__init__(
            name="ast_grep_replace",
            description="""Replace code patterns using AST-aware rewriting.

Dry-run by default (preview changes without applying).
Use meta-variables in rewrite to preserve matched content.

Example:
  pattern='console.log($MSG)'
  rewrite='logger.info($MSG)'

Supported languages: bash, c, cpp, csharp, css, elixir, go, haskell, html, java, javascript, json, kotlin, lua, nix, php, python, ruby, rust, scala, solidity, swift, typescript, tsx, yaml"""
        )
        self.parameters = {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "AST pattern to match"
                },
                "rewrite": {
                    "type": "string",
                    "description": "Replacement pattern (can use $VAR from pattern)"
                },
                "lang": {
                    "type": "string",
                    "enum": SUPPORTED_LANGUAGES,
                    "description": "Target language"
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to search",
                    "default": ["."]
                },
                "globs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Include/exclude globs",
                    "default": []
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without applying (default: true)",
                    "default": True
                }
            },
            "required": ["pattern", "rewrite", "lang"]
        }
    
    async def execute(
        self,
        pattern: str,
        rewrite: str,
        lang: str,
        paths: Optional[List[str]] = None,
        globs: Optional[List[str]] = None,
        dry_run: bool = True
    ) -> ToolResult:
        """
        执行AST替换
        
        Args:
            pattern: AST模式
            rewrite: 替换模式
            lang: 目标语言
            paths: 搜索路径
            globs: 包含/排除模式
            dry_run: 是否预览（不实际修改）
        
        Returns:
            替换结果
        """
        try:
            # 获取ast-grep二进制
            binary_path = await _ast_grep_manager.get_binary_path()
            if not binary_path:
                return ToolResult(
                    success=False,
                    content="",
                    error="ast-grep not available. Install: pip install ast-grep-cli or cargo install ast-grep"
                )
            
            # 构建命令
            args = [
                binary_path,
                "run",
                "-p", pattern,
                "-r", rewrite,
                "--lang", lang,
                "--json=compact"
            ]
            
            # 如果不是dry-run，添加--update-all
            if not dry_run:
                args.append("--update-all")
            
            if globs:
                for glob in globs:
                    args.extend(["--globs", glob])
            
            if not paths:
                paths = ["."]
            args.extend(paths)
            
            # 执行命令
            logger.debug(f"执行命令: {' '.join(args)}")
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=DEFAULT_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Replace timeout after {DEFAULT_TIMEOUT_MS}ms"
                )
            
            # 解析结果（使用搜索工具的解析逻辑）
            search_tool = AstGrepSearchTool()
            result = search_tool._parse_result(stdout, stderr, process.returncode)
            
            # 格式化输出
            output = self._format_result(result, dry_run)
            
            return ToolResult(
                success=not result.error,
                content=output,
                error=result.error,
                metadata={
                    "total_replacements": result.total_matches,
                    "truncated": result.truncated,
                    "dry_run": dry_run
                }
            )
            
        except Exception as e:
            logger.error(f"AST替换失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                content="",
                error=f"AST replace failed: {str(e)}"
            )
    
    def _format_result(self, result: SearchResult, dry_run: bool) -> str:
        """格式化替换结果"""
        if result.error:
            return f"Error: {result.error}"
        
        if not result.matches:
            return "No matches found to replace"
        
        prefix = "[DRY RUN] " if dry_run else ""
        lines = []
        
        # 截断警告
        if result.truncated:
            reason = {
                "max_matches": f"showing first {len(result.matches)} of {result.total_matches}",
                "max_output_bytes": "output exceeded 1MB limit",
                "timeout": "search timed out"
            }.get(result.truncated_reason, "unknown reason")
            lines.append(f"⚠️ Results truncated ({reason})\n")
        
        # 替换数量
        lines.append(f"{prefix}{len(result.matches)} replacement(s):\n")
        
        # 每个替换
        for match in result.matches:
            loc = f"{match.file}:{match.range.start.line + 1}:{match.range.start.column + 1}"
            lines.append(f"{loc}")
            lines.append(f"  {match.text}")
            lines.append("")
        
        # 提示
        if dry_run:
            lines.append("Use dry_run=false to apply changes")
        
        return "\n".join(lines)
