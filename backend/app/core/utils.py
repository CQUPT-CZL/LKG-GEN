# app/core/utils.py

import os
import json
from typing import Dict, List, Any, Optional
from app.services.ai_config_service import call_llm_with_config


def load_prompt(prompt_path: str) -> str:
    """
    加载 prompt 模板文件
    
    Args:
        prompt_path: prompt 文件路径
    
    Returns:
        prompt 模板内容
    """
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Prompt 文件不存在: {prompt_path}")
        return ""
    except Exception as e:
        print(f"❌ 读取 prompt 文件失败: {e}")
        return ""


def call_llm(prompt: str, model_name: str = None, temperature: float = 0.1) -> Optional[Any]:
    """
    调用 LLM API 进行推理
    现在使用数据库中的AI配置而不是环境变量
    
    Args:
        prompt: 输入的 prompt
        model_name: 模型名称（已弃用，将使用数据库配置）
        temperature: 温度参数（已弃用，将使用数据库配置）
    
    Returns:
        LLM 的响应结果，通常是解析后的 JSON 对象
    """
    return call_llm_with_config(prompt)


def save_json(data: Any, filepath: str) -> bool:
    """
    保存数据为 JSON 文件
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
    
    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 保存 JSON 文件失败: {e}")
        return False


def load_json(filepath: str) -> Optional[Any]:
    """
    加载 JSON 文件
    
    Args:
        filepath: 文件路径
    
    Returns:
        加载的数据，失败时返回 None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ JSON 文件不存在: {filepath}")
        return None
    except Exception as e:
        print(f"❌ 加载 JSON 文件失败: {e}")
        return None