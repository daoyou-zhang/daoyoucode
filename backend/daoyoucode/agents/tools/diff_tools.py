"""
Diff工具 - 基于opencode的9种Replacer策略

采用opencode最先进的Diff系统实现，支持：
- 9种智能替换策略
- Levenshtein距离算法
- BlockAnchorReplacer（首尾行锚定）
- 模糊匹配和容错
"""

from typing import Dict, Any, Generator, Optional, List, Tuple
from pathlib import Path
import re
from .base import BaseTool, ToolResult


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
    
    这是opencode最强大的策略：
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
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content=None,
                    error=f"File not found: {file_path}"
                )
            
            # 读取文件
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            # 执行替换（使用模块级函数）
            from . import diff_tools
            new_content = diff_tools.replace(content, search, replace, replace_all)
            
            # 写入文件
            path.write_text(new_content, encoding='utf-8')
            
            return ToolResult(
                success=True,
                content=f"Successfully replaced in {file_path}",
                metadata={
                    'file_path': str(path),
                    'old_size': len(content),
                    'new_size': len(new_content),
                    'replace_all': replace_all
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
