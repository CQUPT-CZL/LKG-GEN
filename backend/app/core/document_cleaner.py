# app/core/document_cleaner.py

from typing import Optional
from .utils import call_llm


def clean_document_content(content: str) -> str:
    """
    使用大模型净化文档内容，去除无用的markdown语法、表格、图片等
    
    Args:
        content: 原始文档内容
    
    Returns:
        净化后的文档内容
    """
    if not content or not content.strip():
        return content
    
    print(f"🧹 开始净化文档内容，原始长度: {len(content)} 字符")
    
    # 构建净化prompt
    prompt = _build_cleaning_prompt(content)
    
    try:
        # 调用LLM进行内容净化
        cleaned_content = call_llm(prompt)
        
        if cleaned_content and isinstance(cleaned_content, str):
            print(f"✅ 文档内容净化完成，净化后长度: {len(cleaned_content)} 字符")
            return cleaned_content.strip()
        else:
            print("⚠️ LLM返回的净化内容格式不正确，使用原始内容")
            return content
            
    except Exception as e:
        print(f"❌ 文档内容净化失败: {e}")
        print("⚠️ 使用原始内容继续处理")
        return content


def _build_cleaning_prompt(content: str) -> str:
    prompt = f"""
    角色设定：
请你扮演一名资深技术分析师。

任务目标：
将以下技术文章浓缩成一段内容丰富、逻辑清晰、且完全专注于“归因分析”的摘要。该摘要的最终目的是为了清晰地展示问题、方案与成果之间的因果链条，用于构建知识图谱。

处理要求：

识别核心问题： 精准定位文章要解决的最核心的技术瓶颈或生产问题。

阐述连锁影响： 详细描述这个核心问题导致了哪些具体的、连锁的负面效应。如果原文有提及，请深入解释其在物理层面（如设备表现）和系统层面（如控制模型）的具体影响。

归纳解决方案及逻辑： 总结所有为解决该问题而实施的关键措施。关键在于，不仅要列出措施，还要简要阐明每项措施背后的目的或原理（例如：“为了缩短等待时间”、“为了避免直接降温”等）。

描述最终成果： 清晰说明解决方案带来了哪些具体的、积极的成果。请使用描述性的词语，并结合文章中的关键数据（如平均值、百分比等），来丰富成果的展现力，使其更具说服力。

输出格式：

所有内容必须整合到一个单一、流畅的自然段落中。

必须删除所有与核心因果链无关的内容，如：泛泛的背景介绍、概念定义、作者信息、参考文献以及纯粹的原始数据罗列。
请处理以下文章：
{content}"""

    return prompt