# app/core/chunker.py

from typing import List
from enum import Enum

class ChunkStrategy(Enum):
    """文档分块策略枚举"""
    FULL_DOCUMENT = "full_document"  # 全部文档一个块
    PARAGRAPH = "paragraph"          # 一段一个块
    SENTENCE = "sentence"            # 一句话一个块

def chunk_document_by_strategy(content: str, strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH) -> List[str]:
    """
    根据指定策略对文档内容进行分块
    
    Args:
        content: 文档内容
        strategy: 分块策略
    
    Returns:
        分块后的文本列表
    """
    if not content or not content.strip():
        return []
    
    chunks = []
    
    if strategy == ChunkStrategy.FULL_DOCUMENT:
        # 全部文档作为一个块
        chunks.append(content.strip())
    
    elif strategy == ChunkStrategy.PARAGRAPH:
        # 按段落分块（使用三个换行符作为段落分隔符）
        lines = content.split('\n\n\n')
        for line in lines:
            if line.strip():
                chunks.append(line.strip())
    
    elif strategy == ChunkStrategy.SENTENCE:
        # 按句子分块（使用句号、问号、感叹号作为句子分隔符）
        import re
        # 匹配中英文句子结束符
        sentences = re.split(r'[。！？.!?]+', content)
        for sentence in sentences:
            if sentence.strip():
                chunks.append(sentence.strip())
    
    return chunks

def chunk_document_by_lines(content: str) -> List[str]:
    """
    基于换行符对文档内容进行分块（保持向后兼容）
    
    Args:
        content: 文档内容
    
    Returns:
        分块后的文本列表
    """
    return chunk_document_by_strategy(content, ChunkStrategy.PARAGRAPH)
