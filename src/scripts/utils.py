import os
import json
from openai import OpenAI
import config

# 初始化大模型客户端
client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_API_BASE,
)

def call_llm(prompt: str, model_name="qwen-max"):
    """封装大模型调用接口"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的材料学知识抽取专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # 低温确保结果稳定
            response_format={"type": "json_object"} # 使用JSON模式确保输出格式
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"调用API时发生错误: {e}")
        return None

def save_json(data, filepath):
    """将数据保存为JSON文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_json(filepath):
    """从JSON文件加载数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_text(filepath):
    """从文本文件加载数据"""
    # 检查文件扩展名
    if not filepath.endswith('.md'):
        raise ValueError("文件必须是 .md 格式")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def load_prompt(filepath):
    """加载Prompt模板"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()