# app/core/utils.py

import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from app.core.config import settings


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
    
    Args:
        prompt: 输入的 prompt
        model_name: 模型名称，默认使用配置中的模型
        temperature: 温度参数，控制输出的随机性
    
    Returns:
        LLM 的响应结果，通常是解析后的 JSON 对象
    """
    if not prompt:
        return None
    
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 使用阿里云的兼容接口
        )
        
        # 使用配置中的模型或传入的模型名称
        model = "qwen-max"
        
        # 调用 LLM
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        # 获取响应内容
        content = response.choices[0].message.content.strip()
        
        # 尝试解析为 JSON
        try:
            # 先尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取 JSON 部分
            try:
                import re
                # 查找 JSON 代码块（支持数组和对象）
                json_match = re.search(r'```json\s*([\[{].*?[\]}])\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    return json.loads(json_str)
                
                # 查找数组格式的JSON
                array_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if array_match:
                    json_str = array_match.group(0)
                    return json.loads(json_str)
                
                # 查找花括号包围的内容
                brace_match = re.search(r'{.*}', content, re.DOTALL)
                if brace_match:
                    json_str = brace_match.group(0)
                    return json.loads(json_str)
                    
            except json.JSONDecodeError:
                pass
            
            # 如果都失败了，返回原始文本
            print(f"⚠️ LLM 响应不是有效的 JSON 格式: {content[:200]}...")
            return content
            
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ 调用 LLM 失败 [{error_type}]: {str(e)}")
        print(f"🔍 详细信息: 模型={model}, 温度={temperature}")
        print(f"📝 Prompt长度: {len(prompt)} 字符")
        if hasattr(e, 'response'):
            print(f"📡 HTTP状态码: {getattr(e.response, 'status_code', 'N/A')}")
        return None


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