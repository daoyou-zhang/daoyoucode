"""
工具后处理器

在工具执行后，基于用户意图智能优化结果
"""

from typing import Dict, Any, List, Optional
import re
import logging
from .base import ToolResult

logger = logging.getLogger(__name__)


class ToolPostProcessor:
    """
    工具后处理器基类
    
    职责：
    - 根据用户问题优化工具结果
    - 减少无关信息
    - 提升相关性
    """
    
    def __init__(self):
        self.processors = {
            'repo_map': RepoMapPostProcessor(),
            'text_search': SearchPostProcessor(),
            'regex_search': SearchPostProcessor(),
            'read_file': ReadFilePostProcessor(),
            'get_repo_structure': StructurePostProcessor(),
        }
    
    async def process(
        self,
        tool_name: str,
        result: ToolResult,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        处理工具结果
        
        Args:
            tool_name: 工具名称
            result: 原始工具结果
            user_query: 用户问题
            context: 上下文信息
        
        Returns:
            优化后的工具结果
        """
        if not result.success:
            return result
        
        processor = self.processors.get(tool_name)
        if not processor:
            return result  # 没有专门的处理器，返回原结果
        
        try:
            processed = await processor.process(result, user_query, context or {})
            logger.info(f"工具 {tool_name} 后处理完成")
            return processed
        except Exception as e:
            logger.error(f"工具 {tool_name} 后处理失败: {e}", exc_info=True)
            return result  # 失败时返回原结果


class BasePostProcessor:
    """后处理器基类"""
    
    async def process(
        self,
        result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """处理结果（子类实现）"""
        raise NotImplementedError
    
    def extract_keywords(self, query: str, max_keywords: int = 5) -> List[str]:
        """
        提取关键词
        
        策略：
        1. 分词（支持中英文）
        2. 移除停用词
        3. 移除短词（<2字符）
        4. 返回前N个
        """
        # 停用词
        stop_words = {
            # 中文
            '的', '是', '在', '有', '和', '了', '吗', '呢', '啊', '这', '那',
            '我', '你', '他', '她', '它', '们', '个', '中', '为', '与', '及',
            '或', '但', '而', '等', '如', '从', '到', '对', '于', '给', '把',
            '怎么', '如何', '什么', '哪里', '哪个', '为什么', '多少', '怎样',
            # 英文
            'the', 'is', 'in', 'at', 'of', 'and', 'a', 'an', 'to', 'for',
            'with', 'on', 'by', 'from', 'as', 'or', 'but', 'if', 'this',
            'that', 'what', 'which', 'who', 'where', 'when', 'how', 'why',
        }
        
        # 分词（支持中英文混合）
        # 1. 先提取英文单词
        words = []
        
        # 提取英文单词和数字
        import re
        english_words = re.findall(r'[a-zA-Z]+', query)
        words.extend([w.lower() for w in english_words if len(w) >= 2])
        
        # 提取中文词（简单按字符分割，实际应该用分词库）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', query)
        for chars in chinese_chars:
            # 简单的中文分词：提取2-4字的词
            for i in range(len(chars)):
                for length in [4, 3, 2]:  # 优先提取长词
                    if i + length <= len(chars):
                        word = chars[i:i+length]
                        if word not in stop_words:
                            words.append(word)
        
        # 去重并过滤
        seen = set()
        keywords = []
        for w in words:
            if w not in stop_words and w not in seen and len(w) >= 2:
                keywords.append(w)
                seen.add(w)
                if len(keywords) >= max_keywords:
                    break
        
        return keywords
    
    def calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """
        计算文本与关键词的相关性
        
        Returns:
            0.0 - 1.0 的相关性分数
        """
        if not keywords:
            return 1.0
        
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        
        return matches / len(keywords)


class RepoMapPostProcessor(BasePostProcessor):
    """
    RepoMap后处理器
    
    策略：
    1. 提取关键词
    2. 只保留相关的文件
    3. 限制文件数量
    """
    
    async def process(
        self,
        result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """处理RepoMap结果"""
        if not isinstance(result.content, str):
            return result
        
        # 提取关键词
        keywords = self.extract_keywords(user_query)
        
        if not keywords:
            return result  # 没有关键词，返回原结果
        
        # 解析RepoMap（按文件分组）
        files = self._parse_repo_map(result.content)
        
        # 计算每个文件的相关性
        scored_files = []
        for file_header, file_content in files:
            relevance = self.calculate_relevance(
                file_header + '\n' + file_content,
                keywords
            )
            scored_files.append((file_header, file_content, relevance))
        
        # 过滤低相关性的文件
        threshold = 0.2  # 至少匹配20%的关键词
        relevant_files = [
            (header, content) for header, content, score in scored_files
            if score >= threshold
        ]
        
        # 如果过滤后太少，保留原结果
        if len(relevant_files) < 3:
            return result
        
        # 限制数量（最多20个文件）
        relevant_files = relevant_files[:20]
        
        # 重新格式化
        filtered_content = self._format_repo_map(relevant_files)
        
        # 更新结果
        result.content = filtered_content
        result.metadata['post_processed'] = True
        result.metadata['keywords'] = keywords
        result.metadata['original_files'] = len(files)
        result.metadata['filtered_files'] = len(relevant_files)
        
        logger.info(
            f"RepoMap过滤: {len(files)} -> {len(relevant_files)} 文件 "
            f"(关键词: {', '.join(keywords)})"
        )
        
        return result
    
    def _parse_repo_map(self, content: str) -> List[tuple]:
        """
        解析RepoMap内容
        
        Returns:
            [(file_header, file_content), ...]
        """
        files = []
        lines = content.splitlines()
        
        current_file = None
        current_content = []
        
        for line in lines:
            # 文件头（包含冒号）
            if ':' in line and not line.startswith('  '):
                if current_file:
                    files.append((current_file, '\n'.join(current_content)))
                current_file = line
                current_content = []
            else:
                current_content.append(line)
        
        # 添加最后一个文件
        if current_file:
            files.append((current_file, '\n'.join(current_content)))
        
        return files
    
    def _format_repo_map(self, files: List[tuple]) -> str:
        """格式化RepoMap"""
        lines = [f"# 代码地图 (Top {len(files)} 相关文件)\n"]
        
        for file_header, file_content in files:
            lines.append(file_header)
            lines.append(file_content)
        
        return '\n'.join(lines)


class SearchPostProcessor(BasePostProcessor):
    """
    搜索结果后处理器
    
    策略：
    1. 去重（相似的结果）
    2. 按相关性排序
    3. 限制数量
    """
    
    async def process(
        self,
        result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """处理搜索结果"""
        if not isinstance(result.content, str):
            return result
        
        # 提取关键词
        keywords = self.extract_keywords(user_query)
        
        # 解析搜索结果
        matches = self._parse_search_results(result.content)
        
        if len(matches) <= 10:
            return result  # 结果不多，不需要过滤
        
        # 计算相关性
        scored_matches = []
        for match in matches:
            relevance = self.calculate_relevance(match, keywords)
            scored_matches.append((match, relevance))
        
        # 排序
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        
        # 取前10个
        top_matches = [match for match, _ in scored_matches[:10]]
        
        # 重新格式化
        filtered_content = '\n\n'.join(top_matches)
        
        # 更新结果
        result.content = filtered_content
        result.metadata['post_processed'] = True
        result.metadata['keywords'] = keywords
        result.metadata['original_matches'] = len(matches)
        result.metadata['filtered_matches'] = len(top_matches)
        
        logger.info(
            f"搜索结果过滤: {len(matches)} -> {len(top_matches)} 个匹配"
        )
        
        return result
    
    def _parse_search_results(self, content: str) -> List[str]:
        """
        解析搜索结果
        
        假设格式：
        file1.py:10: match content
        file1.py:20: match content
        
        或者按空行分隔的块
        """
        # 尝试按空行分隔
        blocks = content.split('\n\n')
        if len(blocks) > 1:
            return blocks
        
        # 否则按行分隔
        return content.splitlines()


class ReadFilePostProcessor(BasePostProcessor):
    """
    文件内容后处理器
    
    策略：
    1. 提取相关的函数/类
    2. 折叠无关代码
    """
    
    async def process(
        self,
        result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """处理文件内容"""
        if not isinstance(result.content, str):
            return result
        
        # 提取关键词
        keywords = self.extract_keywords(user_query)
        
        if not keywords:
            return result
        
        # 按函数/类分割（简单实现）
        sections = self._split_into_sections(result.content)
        
        if len(sections) <= 1:
            return result  # 无法分割，返回原结果
        
        # 计算每个section的相关性
        scored_sections = []
        for section in sections:
            relevance = self.calculate_relevance(section, keywords)
            scored_sections.append((section, relevance))
        
        # 过滤低相关性的section
        threshold = 0.2
        relevant_sections = [
            section for section, score in scored_sections
            if score >= threshold
        ]
        
        if not relevant_sections:
            return result  # 没有相关section，返回原结果
        
        # 重新组合
        filtered_content = '\n\n'.join(relevant_sections)
        
        # 如果过滤后太短，返回原结果
        if len(filtered_content) < len(result.content) * 0.3:
            return result
        
        # 更新结果
        result.content = filtered_content
        result.metadata['post_processed'] = True
        result.metadata['keywords'] = keywords
        result.metadata['original_sections'] = len(sections)
        result.metadata['filtered_sections'] = len(relevant_sections)
        
        logger.info(
            f"文件内容过滤: {len(sections)} -> {len(relevant_sections)} 个section"
        )
        
        return result
    
    def _split_into_sections(self, content: str) -> List[str]:
        """
        将文件内容分割成sections
        
        简单策略：按函数/类定义分割
        """
        lines = content.splitlines()
        sections = []
        current_section = []
        
        for line in lines:
            # 检测函数/类定义
            if (line.startswith('def ') or 
                line.startswith('class ') or
                line.startswith('function ') or
                line.startswith('const ') or
                line.startswith('export ')):
                
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # 添加最后一个section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections


class StructurePostProcessor(BasePostProcessor):
    """
    目录结构后处理器
    
    策略：
    1. 只保留相关的目录
    2. 折叠深层目录
    """
    
    async def process(
        self,
        result: ToolResult,
        user_query: str,
        context: Dict[str, Any]
    ) -> ToolResult:
        """处理目录结构"""
        if not isinstance(result.content, str):
            return result
        
        # 提取关键词
        keywords = self.extract_keywords(user_query)
        
        if not keywords:
            return result
        
        # 按行过滤
        lines = result.content.splitlines()
        filtered_lines = []
        
        for line in lines:
            # 计算相关性
            relevance = self.calculate_relevance(line, keywords)
            
            # 保留相关的行，或者是目录结构的必要部分
            if relevance > 0 or line.strip().endswith('/'):
                filtered_lines.append(line)
        
        if len(filtered_lines) < len(lines) * 0.5:
            # 过滤太多，返回原结果
            return result
        
        # 更新结果
        result.content = '\n'.join(filtered_lines)
        result.metadata['post_processed'] = True
        result.metadata['keywords'] = keywords
        result.metadata['original_lines'] = len(lines)
        result.metadata['filtered_lines'] = len(filtered_lines)
        
        logger.info(
            f"目录结构过滤: {len(lines)} -> {len(filtered_lines)} 行"
        )
        
        return result


# 全局单例
_postprocessor = None


def get_tool_postprocessor() -> ToolPostProcessor:
    """获取工具后处理器（单例）"""
    global _postprocessor
    if _postprocessor is None:
        _postprocessor = ToolPostProcessor()
    return _postprocessor
