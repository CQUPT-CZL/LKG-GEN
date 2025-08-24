# app/core/chunker.py

from typing import List

def chunk_document_by_lines(content: str) -> List[str]:
    """
    基于换行符对文档内容进行分块
    
    Args:
        content: 文档内容
        max_lines_per_chunk: 每个分块的最大行数，默认10行
    
    Returns:
        分块后的文本列表
    """
    if not content or not content.strip():
        return []
    
    # 按换行符分割文档内容
    lines = content.split('\n')
    
    chunks = []
    
    for line in lines:
        if line.strip():
            chunks.append(line.strip())

    return chunks
