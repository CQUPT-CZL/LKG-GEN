# app/services/ai_config_service.py

from typing import Optional, Any
from sqlalchemy.orm import Session
from openai import OpenAI
import json
import re
from app.crud import crud_ai_config
from app.models.sqlite_models import AIConfig, AIProviderEnum
from app.db.sqlite_session import SessionLocal


def get_default_ai_config(db: Session = None) -> Optional[AIConfig]:
    """
    获取默认AI配置
    
    Args:
        db: 数据库会话，如果不提供则创建新会话
    
    Returns:
        默认AI配置实例，如果未找到则返回None
    """
    # 如果没有提供数据库会话，创建新的会话
    if db is None:
        db = SessionLocal()
        try:
            return crud_ai_config.get_default_ai_config(db)
        finally:
            db.close()
    else:
        return crud_ai_config.get_default_ai_config(db)


def call_llm_with_config(
    prompt: str, 
    ai_config: Optional[AIConfig] = None,
    db: Session = None
) -> Optional[Any]:
    """
    使用指定的AI配置调用LLM
    
    Args:
        prompt: 输入的prompt
        ai_config: AI配置实例，如果不提供则使用默认配置
        db: 数据库会话
    
    Returns:
        LLM的响应结果，通常是解析后的JSON对象
    """
    if not prompt:
        return None
    
    # 如果没有提供AI配置，获取默认配置
    if ai_config is None:
        ai_config = get_default_ai_config(db)
        if ai_config is None:
            print("❌ 未找到可用的AI配置")
            return None
    
    try:
        # 根据提供商类型创建客户端
        client = _create_ai_client(ai_config)
        if client is None:
            return None
        
        # 解析温度和最大token参数
        temperature = float(ai_config.temperature) if ai_config.temperature else 0.1
        max_tokens = int(ai_config.max_tokens) if ai_config.max_tokens else 4000
        
        # 调用LLM
        response = client.chat.completions.create(
            model=ai_config.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 获取响应内容
        content = response.choices[0].message.content.strip()
        
        # 尝试解析为JSON
        return _parse_llm_response(content)
        
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ 调用LLM失败 [{error_type}]: {str(e)}")
        print(f"🔍 详细信息: 配置={ai_config.name}, 模型={ai_config.model_name}, 温度={temperature}")
        print(f"📝 Prompt长度: {len(prompt)} 字符")
        if hasattr(e, 'response'):
            print(f"📡 HTTP状态码: {getattr(e.response, 'status_code', 'N/A')}")
        return None


def _create_ai_client(ai_config: AIConfig) -> Optional[OpenAI]:
    """
    根据AI配置创建对应的客户端
    
    Args:
        ai_config: AI配置实例
    
    Returns:
        OpenAI客户端实例或None
    """
    try:
        if ai_config.provider == AIProviderEnum.openai:
            # OpenAI官方API
            return OpenAI(
                api_key=ai_config.api_key,
                base_url=ai_config.base_url or "https://api.openai.com/v1"
            )
        
        elif ai_config.provider == AIProviderEnum.azure:
            # Azure OpenAI
            return OpenAI(
                api_key=ai_config.api_key,
                base_url=ai_config.base_url
            )
        
        elif ai_config.provider == AIProviderEnum.anthropic:
            # Anthropic Claude (使用OpenAI兼容接口)
            return OpenAI(
                api_key=ai_config.api_key,
                base_url=ai_config.base_url or "https://api.anthropic.com/v1"
            )
        
        elif ai_config.provider == AIProviderEnum.google:
            # Google Gemini (使用OpenAI兼容接口)
            return OpenAI(
                api_key=ai_config.api_key,
                base_url=ai_config.base_url or "https://generativelanguage.googleapis.com/v1"
            )
        
        elif ai_config.provider == AIProviderEnum.ollama:
            # Ollama本地模型
            return OpenAI(
                api_key=ai_config.api_key or "ollama",  # Ollama通常不需要API key
                base_url=ai_config.base_url or "http://localhost:11434/v1"
            )
        
        elif ai_config.provider == AIProviderEnum.custom:
            # 自定义提供商
            return OpenAI(
                api_key=ai_config.api_key,
                base_url=ai_config.base_url
            )
        
        else:
            print(f"❌ 不支持的AI提供商: {ai_config.provider}")
            return None
            
    except Exception as e:
        print(f"❌ 创建AI客户端失败: {e}")
        return None


def _parse_llm_response(content: str) -> Any:
    """
    解析LLM响应内容
    
    Args:
        content: LLM响应的原始内容
    
    Returns:
        解析后的数据
    """
    try:
        # 先尝试直接解析
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ 直接JSON解析失败: {e}")
        print(f"📍 错误位置: 第{e.lineno}行, 第{e.colno}列")
        print(f"📝 错误消息: {e.msg}")
        
        # 如果直接解析失败，尝试提取JSON部分
        try:
            # 查找JSON代码块（支持数组和对象）
            json_match = re.search(r'```json\s*([\[{].*?[\]}])\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print(f"🔍 尝试解析JSON代码块: {json_str[:100]}...")
                return json.loads(json_str)
            
            # 查找数组格式的JSON
            array_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if array_match:
                json_str = array_match.group(0)
                print(f"🔍 尝试解析数组格式: {json_str[:100]}...")
                return json.loads(json_str)
            
            # 查找花括号包围的内容
            brace_match = re.search(r'{.*}', content, re.DOTALL)
            if brace_match:
                json_str = brace_match.group(0)
                print(f"🔍 尝试解析对象格式: {json_str[:100]}...")
                return json.loads(json_str)
                
        except json.JSONDecodeError as e2:
            print(f"❌ 提取JSON部分解析也失败: {e2}")
            print(f"📍 提取部分错误位置: 第{e2.lineno}行, 第{e2.colno}列")
        
        # 如果都失败了，返回原始文本并显示详细信息
        print(f"⚠️ LLM响应不是有效的JSON格式")
        print(f"📏 响应长度: {len(content)} 字符")
        print(f"📄 完整响应内容:")
        print(f"{'='*50}")
        print(content)
        print(f"{'='*50}")
        print(f"🔤 响应前200字符: {content[:200]}...")
        print(f"🔤 响应后200字符: ...{content[-200:]}")
        return content


def call_llm(prompt: str, model_name: str = None, temperature: float = 0.1) -> Optional[Any]:
    """
    兼容性函数：使用默认AI配置调用LLM
    保持与原有代码的兼容性
    
    Args:
        prompt: 输入的prompt
        model_name: 模型名称（已弃用，将使用数据库配置）
        temperature: 温度参数（已弃用，将使用数据库配置）
    
    Returns:
        LLM的响应结果
    """
    return call_llm_with_config(prompt)