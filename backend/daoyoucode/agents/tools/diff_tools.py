"""
Diff工具 - 智能替换策略

采用先进的 Diff 系统实现，支持：
- 9种智能替换策略
- Levenshtein距离算法
- BlockAnchorReplacer（首尾行锚定）
- 模糊匹配和容错
"""

from typing import Dict, Any, Generator, Optional, List, Tuple, AsyncGenerator
from pathlib import Path
import re
import asyncio
from .base import BaseTool, ToolResult, StreamingEditTool, EditEvent


# ========== Levenshtein距离算法 ==========

def levenshtein(a: str, b: str) -> int:
    """
    计算两个字符串的Levenshtein编辑距离
    
    用于衡量字符串相似度，距离越小越相似
    """
    if a == "" or b == "":
        return max(len(a), len(b))
    
    # 创建距离矩阵
    matrix = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    
    # 初始化第一行和第一列
    for i in range(len(a) + 1):
        matrix[i][0] = i
    for j in range(len(b) + 1):
        matrix[0][j] = j
    
    # 动态规划计算距离
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # 删除
                matrix[i][j - 1] + 1,      # 插入
                matrix[i - 1][j - 1] + cost  # 替换
            )
    
    return matrix[len(a)][len(b)]


# ========== 9种Replacer策略 ==========

class Replacer:
    """Replacer基类"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        """查找所有匹配项"""
        raise NotImplementedError()


class SimpleReplacer(Replacer):
    """策略1: 精确匹配"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        if find in content:
            yield find


class LineTrimmedReplacer(Replacer):
    """策略2: 忽略行首尾空白"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        original_lines = content.split("\n")
        search_lines = find.split("\n")
        
        # 移除末尾空行
        if search_lines and search_lines[-1] == "":
            search_lines.pop()
        
        # 滑动窗口匹配
        for i in range(len(original_lines) - len(search_lines) + 1):
            matches = True
            
            for j in range(len(search_lines)):
                if original_lines[i + j].strip() != search_lines[j].strip():
                    matches = False
                    break
            
            if matches:
                # 计算匹配的起止位置
                match_start = sum(len(original_lines[k]) + 1 for k in range(i))
                match_end = match_start + sum(
                    len(original_lines[i + k]) + (1 if k < len(search_lines) - 1 else 0)
                    for k in range(len(search_lines))
                )
                yield content[match_start:match_end]


class BlockAnchorReplacer(Replacer):
    """
    策略3: 首尾行锚定 + Levenshtein相似度
    
    这是最强大的策略：
    - 使用首尾行作为锚点
    - 计算中间行的Levenshtein相似度
    - 单候选阈值0.0，多候选阈值0.3
    """
    
    SINGLE_CANDIDATE_THRESHOLD = 0.0
    MULTIPLE_CANDIDATES_THRESHOLD = 0.3
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        original_lines = content.split("\n")
        search_lines = find.split("\n")
        
        if len(search_lines) < 3:
            return
        
        if search_lines and search_lines[-1] == "":
            search_lines.pop()
        
        first_line = search_lines[0].strip()
        last_line = search_lines[-1].strip()
        search_block_size = len(search_lines)
        
        # 收集所有候选位置
        candidates: List[Tuple[int, int]] = []
        for i in range(len(original_lines)):
            if original_lines[i].strip() != first_line:
                continue
            
            # 查找匹配的末尾行
            for j in range(i + 2, len(original_lines)):
                if original_lines[j].strip() == last_line:
                    candidates.append((i, j))
                    break
        
        if not candidates:
            return
        
        # 单候选情况（使用宽松阈值）
        if len(candidates) == 1:
            start_line, end_line = candidates[0]
            actual_block_size = end_line - start_line + 1
            
            similarity = 0.0
            lines_to_check = min(search_block_size - 2, actual_block_size - 2)
            
            if lines_to_check > 0:
                for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                    original_line = original_lines[start_line + j].strip()
                    search_line = search_lines[j].strip()
                    max_len = max(len(original_line), len(search_line))
                    
                    if max_len == 0:
                        continue
                    
                    distance = levenshtein(original_line, search_line)
                    similarity += (1 - distance / max_len) / lines_to_check
                    
                    if similarity >= BlockAnchorReplacer.SINGLE_CANDIDATE_THRESHOLD:
                        break
            else:
                similarity = 1.0
            
            if similarity >= BlockAnchorReplacer.SINGLE_CANDIDATE_THRESHOLD:
                match_start = sum(len(original_lines[k]) + 1 for k in range(start_line))
                match_end = match_start + sum(
                    len(original_lines[k]) + (1 if k < end_line else 0)
                    for k in range(start_line, end_line + 1)
                )
                yield content[match_start:match_end]
            return
        
        # 多候选情况（计算最佳匹配）
        best_match: Optional[Tuple[int, int]] = None
        max_similarity = -1.0
        
        for start_line, end_line in candidates:
            actual_block_size = end_line - start_line + 1
            
            similarity = 0.0
            lines_to_check = min(search_block_size - 2, actual_block_size - 2)
            
            if lines_to_check > 0:
                for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                    original_line = original_lines[start_line + j].strip()
                    search_line = search_lines[j].strip()
                    max_len = max(len(original_line), len(search_line))
                    
                    if max_len == 0:
                        continue
                    
                    distance = levenshtein(original_line, search_line)
                    similarity += 1 - distance / max_len
                
                similarity /= lines_to_check
            else:
                similarity = 1.0
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = (start_line, end_line)
        
        if max_similarity >= BlockAnchorReplacer.MULTIPLE_CANDIDATES_THRESHOLD and best_match:
            start_line, end_line = best_match
            match_start = sum(len(original_lines[k]) + 1 for k in range(start_line))
            match_end = match_start + sum(
                len(original_lines[k]) + (1 if k < end_line else 0)
                for k in range(start_line, end_line + 1)
            )
            yield content[match_start:match_end]


class WhitespaceNormalizedReplacer(Replacer):
    """策略4: 空白归一化"""
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        normalized_find = WhitespaceNormalizedReplacer.normalize_whitespace(find)
        
        # 单行匹配
        lines = content.split("\n")
        for line in lines:
            if WhitespaceNormalizedReplacer.normalize_whitespace(line) == normalized_find:
                yield line
        
        # 多行匹配
        find_lines = find.split("\n")
        if len(find_lines) > 1:
            for i in range(len(lines) - len(find_lines) + 1):
                block = "\n".join(lines[i:i + len(find_lines)])
                if WhitespaceNormalizedReplacer.normalize_whitespace(block) == normalized_find:
                    yield block


class IndentationFlexibleReplacer(Replacer):
    """策略5: 缩进灵活匹配"""
    
    @staticmethod
    def remove_indentation(text: str) -> str:
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        
        if not non_empty_lines:
            return text
        
        min_indent = min(
            len(line) - len(line.lstrip())
            for line in non_empty_lines
        )
        
        return "\n".join(
            line[min_indent:] if line.strip() else line
            for line in lines
        )
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        normalized_find = IndentationFlexibleReplacer.remove_indentation(find)
        content_lines = content.split("\n")
        find_lines = find.split("\n")
        
        for i in range(len(content_lines) - len(find_lines) + 1):
            block = "\n".join(content_lines[i:i + len(find_lines)])
            if IndentationFlexibleReplacer.remove_indentation(block) == normalized_find:
                yield block


class EscapeNormalizedReplacer(Replacer):
    """策略6: 转义字符处理"""
    
    @staticmethod
    def unescape_string(s: str) -> str:
        replacements = {
            r'\n': '\n',
            r'\t': '\t',
            r'\r': '\r',
            r"\'": "'",
            r'\"': '"',
            r'\`': '`',
            r'\\': '\\',
            r'\$': '$',
        }
        result = s
        for escaped, unescaped in replacements.items():
            result = result.replace(escaped, unescaped)
        return result
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        unescaped_find = EscapeNormalizedReplacer.unescape_string(find)
        
        if unescaped_find in content:
            yield unescaped_find
        
        # 尝试查找转义版本
        lines = content.split("\n")
        find_lines = unescaped_find.split("\n")
        
        for i in range(len(lines) - len(find_lines) + 1):
            block = "\n".join(lines[i:i + len(find_lines)])
            if EscapeNormalizedReplacer.unescape_string(block) == unescaped_find:
                yield block


class TrimmedBoundaryReplacer(Replacer):
    """策略7: 边界trim"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        trimmed_find = find.strip()
        
        if trimmed_find == find:
            return
        
        if trimmed_find in content:
            yield trimmed_find
        
        lines = content.split("\n")
        find_lines = find.split("\n")
        
        for i in range(len(lines) - len(find_lines) + 1):
            block = "\n".join(lines[i:i + len(find_lines)])
            if block.strip() == trimmed_find:
                yield block


class ContextAwareReplacer(Replacer):
    """策略8: 上下文感知"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        find_lines = find.split("\n")
        if len(find_lines) < 3:
            return
        
        if find_lines and find_lines[-1] == "":
            find_lines.pop()
        
        content_lines = content.split("\n")
        first_line = find_lines[0].strip()
        last_line = find_lines[-1].strip()
        
        for i in range(len(content_lines)):
            if content_lines[i].strip() != first_line:
                continue
            
            for j in range(i + 2, len(content_lines)):
                if content_lines[j].strip() == last_line:
                    block_lines = content_lines[i:j + 1]
                    
                    if len(block_lines) == len(find_lines):
                        # 检查中间行相似度（至少50%匹配）
                        matching_lines = 0
                        total_non_empty = 0
                        
                        for k in range(1, len(block_lines) - 1):
                            block_line = block_lines[k].strip()
                            find_line = find_lines[k].strip()
                            
                            if block_line or find_line:
                                total_non_empty += 1
                                if block_line == find_line:
                                    matching_lines += 1
                        
                        if total_non_empty == 0 or matching_lines / total_non_empty >= 0.5:
                            yield "\n".join(block_lines)
                            break
                    break


class MultiOccurrenceReplacer(Replacer):
    """策略9: 多次出现处理"""
    
    @staticmethod
    def find_matches(content: str, find: str) -> Generator[str, None, None]:
        start_index = 0
        while True:
            index = content.find(find, start_index)
            if index == -1:
                break
            yield find
            start_index = index + len(find)


# ========== 核心替换函数 ==========

def replace(content: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    使用9种策略进行智能替换
    
    Args:
        content: 原始内容
        old_string: 要替换的字符串
        new_string: 替换后的字符串
        replace_all: 是否替换所有出现
    
    Returns:
        替换后的内容
    
    Raises:
        ValueError: 如果找不到匹配或有多个匹配
    """
    if old_string == new_string:
        raise ValueError("old_string and new_string must be different")
    
    not_found = True
    
    # 按优先级尝试9种策略
    replacers = [
        SimpleReplacer,
        LineTrimmedReplacer,
        BlockAnchorReplacer,
        WhitespaceNormalizedReplacer,
        IndentationFlexibleReplacer,
        EscapeNormalizedReplacer,
        TrimmedBoundaryReplacer,
        ContextAwareReplacer,
        MultiOccurrenceReplacer,
    ]
    
    for replacer_class in replacers:
        for search in replacer_class.find_matches(content, old_string):
            index = content.find(search)
            if index == -1:
                continue
            
            not_found = False
            
            if replace_all:
                return content.replace(search, new_string)
            
            # 检查是否唯一
            last_index = content.rfind(search)
            if index != last_index:
                continue
            
            # 执行替换
            return content[:index] + new_string + content[index + len(search):]
    
    if not_found:
        raise ValueError("old_string not found in content")
    
    raise ValueError(
        "Found multiple matches for old_string. "
        "Provide more surrounding lines to identify the correct match."
    )


# ========== 工具封装 ==========

class SearchReplaceTool(BaseTool):
    """SEARCH/REPLACE编辑工具"""
    
    def __init__(self):
        super().__init__(
            name="search_replace",
            description="使用SEARCH/REPLACE模式编辑文件（支持9种智能匹配策略）"
        )
    
    async def execute(
        self,
        file_path: str,
        search: str,
        replace: str,
        replace_all: bool = False
    ) -> ToolResult:
        """
        执行SEARCH/REPLACE
        
        Args:
            file_path: 文件路径
            search: 要搜索的内容
            replace: 替换后的内容
            replace_all: 是否替换所有出现
        """
        try:
            # 使用 resolve_path 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path} (resolved to {path})"
                )
            
            # 读取原始文件内容
            old_content = path.read_text(encoding='utf-8', errors='ignore')
            
            # 执行替换（使用模块级函数）
            from . import diff_tools
            new_content = diff_tools.replace(old_content, search, replace, replace_all)
            
            # 生成 diff
            import difflib
            diff_lines = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=''
            ))
            
            diff_text = ''.join(diff_lines) if diff_lines else "No changes"
            
            # 写入文件
            path.write_text(new_content, encoding='utf-8')
            
            # 构建结果消息
            result_message = f"✅ Successfully modified {file_path}\n\n"
            result_message += "📝 Changes:\n"
            result_message += "```diff\n"
            result_message += diff_text
            result_message += "\n```"
            
            return ToolResult(
                success=True,
                content=result_message,
                metadata={
                    'file_path': str(path),
                    'old_size': len(old_content),
                    'new_size': len(new_content),
                    'replace_all': replace_all,
                    'diff': diff_text,
                    'changes_count': len([line for line in diff_lines if line.startswith('+') or line.startswith('-')])
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "search": {
                        "type": "string",
                        "description": "要搜索的内容"
                    },
                    "replace": {
                        "type": "string",
                        "description": "替换后的内容"
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "是否替换所有出现",
                        "default": False
                    }
                },
                "required": ["file_path", "search", "replace"]
            }
        }


# ========== Unified Diff (editblock/udiff 式细粒度编辑) ==========

def _parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    解析 unified diff，返回 [{"path": str, "hunks": [(old_start, old_count, new_start, new_count, lines)]}, ...]
    path 为相对路径（已去掉 a/ b/ 前缀）
    """
    files = []
    current_file: Optional[Dict[str, Any]] = None
    current_hunk: Optional[Tuple] = None
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("--- "):
            # 旧文件路径：--- a/foo.py 或 --- foo.py
            raw = line[4:].rstrip()
            path = raw.split("\t")[0].strip()
            if path.startswith("a/"):
                path = path[2:]
            if current_file and current_hunk is not None:
                current_file["hunks"].append(current_hunk)
            current_file = {"path": path, "hunks": []}
            current_hunk = None
        elif line.startswith("+++ "):
            # 新文件路径（可选使用）
            raw = line[4:].rstrip()
            path = raw.split("\t")[0].strip()
            if path.startswith("b/"):
                path = path[2:]
            if current_file:
                current_file["path"] = path
            current_hunk = None
        elif line.startswith("@@ "):
            if current_file is None:
                continue
            if current_hunk is not None:
                current_file["hunks"].append(current_hunk)
            # @@ -old_start,old_count +new_start,new_count @@
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line.strip())
            if m:
                old_s, old_c, new_s, new_c = m.groups()
                current_hunk = (
                    int(old_s),
                    int(old_c) if old_c else 1,
                    int(new_s),
                    int(new_c) if new_c else 1,
                    [],
                )
        elif current_hunk is not None:
            # 行内容：空格=上下文，-=删除，+=添加
            current_hunk[4].append(line)
    if current_file and current_hunk is not None:
        current_file["hunks"].append(current_hunk)
    if current_file:
        files.append(current_file)
    return files


def _apply_hunk(old_lines: List[str], old_start: int, old_count: int, new_start: int, new_count: int, hunk_lines: List[str]) -> List[str]:
    """应用单个 hunk。old_lines 为带换行符的行列表；unified diff：空格=上下文，-=删除，+=添加。"""
    if old_start <= 0:
        result = []
        old_pos = 0
    else:
        result = old_lines[: old_start - 1]
        old_pos = old_start - 1
    for hunk_line in hunk_lines:
        if len(hunk_line) < 1:
            continue
        if hunk_line[0] == " ":
            result.append(hunk_line[1:] if hunk_line.endswith("\n") else hunk_line[1:] + "\n")
            old_pos += 1
        elif hunk_line[0] == "-":
            old_pos += 1
        elif hunk_line[0] == "+":
            result.append(hunk_line[1:] if hunk_line.endswith("\n") else hunk_line[1:] + "\n")
    result.extend(old_lines[old_pos:])
    return result


class ApplyPatchTool(BaseTool):
    """
    应用 Unified Diff（editblock/udiff 式细粒度编辑）
    
    接受模型输出的标准 unified diff 文本，按 hunk 精确应用，便于审计和回滚。
    采用标准 unified diff 编辑范式。
    """

    def __init__(self):
        super().__init__(
            name="apply_patch",
            description="应用 unified diff 到文件。输入为标准 diff 文本（---/+++ 文件路径，@@ hunk，- 删除行，+ 添加行）。路径为相对项目根。"
        )

    async def execute(
        self,
        diff: str,
        base_path: Optional[str] = None
    ) -> ToolResult:
        """
        应用 diff。
        
        Args:
            diff: unified diff 字符串（可含多个文件）
            base_path: 相对路径的基准目录，默认使用当前仓库根
        """
        try:
            base = self.context.repo_path
            if base_path:
                base = self.resolve_path(base_path)
            parsed = _parse_unified_diff(diff)
            applied = []
            errors = []
            for file_info in parsed:
                rel_path = file_info["path"]
                full_path = base / rel_path
                if not full_path.exists() and not any(h[4] for h in file_info["hunks"] if any(l.startswith("+") for l in h[4])):
                    errors.append(f"文件不存在且无新增内容: {rel_path}")
                    continue
                try:
                    if full_path.exists():
                        content = full_path.read_text(encoding="utf-8", errors="ignore")
                        old_lines = content.splitlines(keepends=True)
                        if not content.endswith("\n") and old_lines:
                            old_lines[-1] = old_lines[-1].rstrip("\n") + "\n"
                    else:
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        old_lines = []
                    for (old_start, old_count, new_start, new_count, hunk_lines) in file_info["hunks"]:
                        old_lines = _apply_hunk(old_lines, old_start, old_count, new_start, new_count, hunk_lines)
                    full_path.write_text("".join(old_lines), encoding="utf-8")
                    applied.append(rel_path)
                except Exception as e:
                    errors.append(f"{rel_path}: {e}")
            if errors and not applied:
                return ToolResult(success=False, content=None, error="; ".join(errors))
            return ToolResult(
                success=True,
                content=f"已应用 diff 到: {', '.join(applied)}" + ("; 错误: " + "; ".join(errors) if errors else ""),
                metadata={"applied": applied, "errors": errors if errors else None}
            )
        except Exception as e:
            return ToolResult(success=False, content=None, error=str(e))

    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "diff": {
                        "type": "string",
                        "description": "Unified diff 全文（包含 ---/+++ 路径和 @@ hunk）"
                    },
                    "base_path": {
                        "type": "string",
                        "description": "相对路径基准，默认当前仓库根。使用 '.' 表示仓库根"
                    }
                },
                "required": ["diff"]
            }
        }



# ========== 智能 Diff 编辑工具（流式） ==========

class IntelligentDiffEditTool(StreamingEditTool):
    """
    智能 Diff 编辑工具（支持流式显示）
    
    功能：
    1. 精确匹配 - 直接查找替换
    2. 模糊匹配 - 使用 Levenshtein 距离
    3. 智能回退 - 验证失败时自动回滚
    4. 流式显示 - 实时显示编辑过程
    
    优势：
    - 精确到行，不需要完整文件内容
    - 自动处理空白差异
    - 支持模糊匹配（相似度阈值）
    - LSP 验证集成
    """
    
    def __init__(self):
        super().__init__(
            name="intelligent_diff_edit",
            description="使用智能 Diff 编辑文件（精确到行，支持模糊匹配和自动回退）"
        )
    
    async def execute(
        self,
        file_path: str,
        search_block: str,
        replace_block: str,
        fuzzy_match: bool = True,
        similarity_threshold: float = 0.8,
        verify: bool = True
    ) -> ToolResult:
        """
        执行智能 Diff 编辑
        
        Args:
            file_path: 文件路径
            search_block: 要查找的代码块
            replace_block: 替换的代码块
            fuzzy_match: 是否启用模糊匹配
            similarity_threshold: 相似度阈值（0.0-1.0）
            verify: 是否使用 LSP 验证
        
        Returns:
            ToolResult
        """
        try:
            # 解析路径
            path = self.resolve_path(file_path)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"文件不存在: {file_path}"
                )
            
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找最佳匹配
            match_result = self._find_best_match(
                content,
                search_block,
                fuzzy_match,
                similarity_threshold
            )
            
            if not match_result:
                return ToolResult(
                    success=False,
                    content=None,
                    error="未找到匹配的代码块"
                )
            
            match_start, match_end, similarity = match_result
            matched_text = content[match_start:match_end]
            
            # 应用替换
            new_content = (
                content[:match_start] +
                replace_block +
                content[match_end:]
            )
            
            # 生成 Diff
            import difflib
            diff_lines = list(difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=''
            ))
            
            diff_text = ''.join(diff_lines) if diff_lines else "No changes"
            
            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # LSP 验证
            diagnostics = []
            if verify and self._should_verify(path):
                diagnostics = await self._verify_with_lsp(path)
                
                if diagnostics:
                    error_count = len([d for d in diagnostics if d.get('severity') == 1])
                    
                    if error_count > 0:
                        # 有错误，回退
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        error_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown')}"
                            for d in diagnostics if d.get('severity') == 1
                        ]
                        
                        return ToolResult(
                            success=False,
                            content=None,
                            error=f"验证失败，已回退。{error_count} 个错误:\n" + "\n".join(error_messages[:5])
                        )
            
            # 构建结果消息
            result_message = f"✅ 成功编辑 {file_path}\n\n"
            result_message += f"📊 匹配信息:\n"
            result_message += f"  • 相似度: {similarity:.1%}\n"
            result_message += f"  • 匹配位置: {match_start}-{match_end}\n"
            result_message += f"  • 匹配内容:\n```\n{matched_text[:200]}{'...' if len(matched_text) > 200 else ''}\n```\n\n"
            result_message += f"📝 变更:\n```diff\n{diff_text}\n```"
            
            if diagnostics:
                warning_count = len([d for d in diagnostics if d.get('severity') == 2])
                if warning_count > 0:
                    result_message += f"\n\n⚠️  {warning_count} 个警告（已忽略）"
            
            return ToolResult(
                success=True,
                content=result_message,
                metadata={
                    'file_path': str(path),
                    'similarity': similarity,
                    'match_start': match_start,
                    'match_end': match_end,
                    'diff': diff_text,
                    'verified': verify and self._should_verify(path),
                    'diagnostics': diagnostics
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    async def execute_streaming(
        self,
        file_path: str,
        search_block: str,
        replace_block: str,
        fuzzy_match: bool = True,
        similarity_threshold: float = 0.8,
        verify: bool = True
    ) -> AsyncGenerator[EditEvent, None]:
        """
        流式执行智能 Diff 编辑
        
        实时显示编辑过程：
        1. 分析文件
        2. 查找匹配
        3. 应用修改
        4. 验证代码
        
        Yields:
            EditEvent - 编辑事件
        """
        try:
            # 解析路径
            path = self.resolve_path(file_path)
            
            # 事件1: 开始编辑
            yield EditEvent(
                type=EditEvent.EDIT_START,
                data={
                    'file_path': file_path,
                    'action': 'intelligent_diff_edit'
                }
            )
            
            await asyncio.sleep(0.01)
            
            if not path.exists():
                yield EditEvent(
                    type=EditEvent.EDIT_ERROR,
                    data={
                        'error': f"文件不存在: {file_path}"
                    }
                )
                return
            
            # 事件2: 分析文件
            yield EditEvent(
                type=EditEvent.EDIT_ANALYZING,
                data={
                    'file_path': file_path,
                    'status': '读取文件内容'
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_size = len(content)
            line_count = content.count('\n') + 1
            
            yield EditEvent(
                type=EditEvent.EDIT_ANALYZING,
                data={
                    'file_path': file_path,
                    'status': '分析完成',
                    'size': file_size,
                    'lines': line_count
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 事件3: 查找匹配
            yield EditEvent(
                type=EditEvent.EDIT_PLANNING,
                data={
                    'status': '查找匹配的代码块',
                    'fuzzy_match': fuzzy_match,
                    'similarity_threshold': similarity_threshold
                }
            )
            
            await asyncio.sleep(0.02)
            
            # 查找最佳匹配
            match_result = self._find_best_match(
                content,
                search_block,
                fuzzy_match,
                similarity_threshold
            )
            
            if not match_result:
                yield EditEvent(
                    type=EditEvent.EDIT_ERROR,
                    data={
                        'error': "未找到匹配的代码块"
                    }
                )
                return
            
            match_start, match_end, similarity = match_result
            matched_text = content[match_start:match_end]
            
            # 计算匹配的行号
            match_start_line = content[:match_start].count('\n') + 1
            match_end_line = content[:match_end].count('\n') + 1
            
            yield EditEvent(
                type=EditEvent.EDIT_PLANNING,
                data={
                    'status': '找到匹配',
                    'similarity': similarity,
                    'match_start_line': match_start_line,
                    'match_end_line': match_end_line,
                    'matched_lines': match_end_line - match_start_line + 1
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 事件4: 应用修改
            yield EditEvent(
                type=EditEvent.EDIT_APPLYING,
                data={
                    'status': '应用修改',
                    'old_size': len(matched_text),
                    'new_size': len(replace_block)
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 应用替换
            new_content = (
                content[:match_start] +
                replace_block +
                content[match_end:]
            )
            
            # 生成 Diff
            import difflib
            diff_lines = list(difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=''
            ))
            
            diff_text = ''.join(diff_lines) if diff_lines else "No changes"
            
            # 统计变更
            added_lines = len([l for l in diff_lines if l.startswith('+')])
            removed_lines = len([l for l in diff_lines if l.startswith('-')])
            
            yield EditEvent(
                type=EditEvent.EDIT_BLOCK,
                data={
                    'status': '生成 Diff',
                    'added_lines': added_lines,
                    'removed_lines': removed_lines,
                    'diff_preview': diff_text[:500]  # 只显示前500字符
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            yield EditEvent(
                type=EditEvent.EDIT_APPLYING,
                data={
                    'status': '文件已写入'
                }
            )
            
            await asyncio.sleep(0.01)
            
            # 事件5: LSP 验证
            if verify and self._should_verify(path):
                yield EditEvent(
                    type=EditEvent.EDIT_VERIFYING,
                    data={
                        'status': '使用 LSP 验证代码'
                    }
                )
                
                await asyncio.sleep(0.02)
                
                diagnostics = await self._verify_with_lsp(path)
                
                if diagnostics:
                    error_count = len([d for d in diagnostics if d.get('severity') == 1])
                    warning_count = len([d for d in diagnostics if d.get('severity') == 2])
                    
                    yield EditEvent(
                        type=EditEvent.EDIT_VERIFYING,
                        data={
                            'status': '验证完成',
                            'errors': error_count,
                            'warnings': warning_count
                        }
                    )
                    
                    await asyncio.sleep(0.01)
                    
                    if error_count > 0:
                        # 有错误，回退
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        error_messages = [
                            f"Line {d.get('range', {}).get('start', {}).get('line', '?') + 1}: {d.get('message', 'Unknown')}"
                            for d in diagnostics if d.get('severity') == 1
                        ]
                        
                        yield EditEvent(
                            type=EditEvent.EDIT_ERROR,
                            data={
                                'error': f"验证失败，已回退。{error_count} 个错误",
                                'error_messages': error_messages[:5]
                            }
                        )
                        return
                else:
                    yield EditEvent(
                        type=EditEvent.EDIT_VERIFYING,
                        data={
                            'status': '验证通过，无错误'
                        }
                    )
                    
                    await asyncio.sleep(0.01)
            
            # 事件6: 编辑完成
            yield EditEvent(
                type=EditEvent.EDIT_COMPLETE,
                data={
                    'file_path': file_path,
                    'similarity': similarity,
                    'match_start_line': match_start_line,
                    'match_end_line': match_end_line,
                    'added_lines': added_lines,
                    'removed_lines': removed_lines,
                    'verified': verify and self._should_verify(path)
                }
            )
            
        except Exception as e:
            yield EditEvent(
                type=EditEvent.EDIT_ERROR,
                data={
                    'error': str(e)
                }
            )
    
    def _find_best_match(
        self,
        content: str,
        search_block: str,
        fuzzy_match: bool,
        similarity_threshold: float
    ) -> Optional[Tuple[int, int, float]]:
        """
        查找最佳匹配
        
        Returns:
            (match_start, match_end, similarity) 或 None
        """
        
        # 1. 精确匹配
        if search_block in content:
            start = content.index(search_block)
            end = start + len(search_block)
            return (start, end, 1.0)
        
        if not fuzzy_match:
            return None
        
        # 2. 模糊匹配
        content_lines = content.split('\n')
        search_lines = search_block.split('\n')
        
        best_match = None
        best_similarity = 0.0
        
        # 滑动窗口
        for i in range(len(content_lines) - len(search_lines) + 1):
            window = content_lines[i:i + len(search_lines)]
            
            # 计算相似度
            similarity = self._calculate_similarity(
                window,
                search_lines
            )
            
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                
                # 计算字符位置
                start = sum(len(content_lines[j]) + 1 for j in range(i))
                end = start + sum(len(window[j]) + 1 for j in range(len(window))) - 1
                
                best_match = (start, end, similarity)
        
        return best_match
    
    def _calculate_similarity(
        self,
        lines1: List[str],
        lines2: List[str]
    ) -> float:
        """
        计算两组行的相似度
        
        使用 Levenshtein 距离
        """
        if len(lines1) != len(lines2):
            return 0.0
        
        total_similarity = 0.0
        
        for line1, line2 in zip(lines1, lines2):
            # 归一化空白
            line1_norm = ' '.join(line1.split())
            line2_norm = ' '.join(line2.split())
            
            if line1_norm == line2_norm:
                total_similarity += 1.0
            else:
                # Levenshtein 距离
                max_len = max(len(line1_norm), len(line2_norm))
                if max_len == 0:
                    total_similarity += 1.0
                else:
                    distance = levenshtein(line1_norm, line2_norm)
                    total_similarity += 1.0 - (distance / max_len)
        
        return total_similarity / len(lines1)
    
    def _should_verify(self, path: Path) -> bool:
        """判断是否应该验证文件"""
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
        return path.suffix in code_extensions
    
    async def _verify_with_lsp(self, file_path: Path) -> List[Dict]:
        """
        使用 LSP 验证代码
        
        Returns:
            诊断信息列表（错误和警告）
        """
        try:
            from .lsp_tools import with_lsp_client
            import logging
            
            logger = logging.getLogger(__name__)
            
            result = await with_lsp_client(
                str(file_path),
                lambda client: client.diagnostics(str(file_path), wait_time=3.0)
            )
            
            diagnostics = result.get('items', [])
            logger.debug(f"LSP返回{len(diagnostics)}个诊断信息")
            
            # 只返回错误和警告
            filtered = [
                d for d in diagnostics 
                if d.get('severity') in [1, 2]  # 1=Error, 2=Warning
            ]
            
            logger.debug(f"过滤后{len(filtered)}个错误/警告")
            return filtered
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"LSP验证失败: {e}")
            return []
    
    def get_function_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径（相对于项目根目录）"
                    },
                    "search_block": {
                        "type": "string",
                        "description": "要查找的代码块"
                    },
                    "replace_block": {
                        "type": "string",
                        "description": "替换的代码块"
                    },
                    "fuzzy_match": {
                        "type": "boolean",
                        "description": "是否启用模糊匹配（默认True）",
                        "default": True
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "相似度阈值（0.0-1.0，默认0.8）",
                        "default": 0.8
                    },
                    "verify": {
                        "type": "boolean",
                        "description": "是否使用LSP验证代码（默认True）",
                        "default": True
                    }
                },
                "required": ["file_path", "search_block", "replace_block"]
            }
        }
