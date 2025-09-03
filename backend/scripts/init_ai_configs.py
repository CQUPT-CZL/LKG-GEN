#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置数据库初始化脚本
创建默认的AI配置，方便用户快速开始使用
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(project_root))

from sqlalchemy.orm import Session
from app.db.sqlite_session import SessionLocal, engine
from app.models.sqlite_models import Base, AIConfig, AIProviderEnum
from app.schemas.ai_config import AIConfigCreate
from app.crud import crud_ai_config


def init_default_ai_configs(db: Session):
    """
    初始化默认AI配置
    """
    print("🤖 开始初始化默认AI配置...")
    
    # 检查是否已有配置
    existing_configs = crud_ai_config.get_ai_configs(db, skip=0, limit=1)
    if existing_configs:
        print("⚠️  数据库中已存在AI配置，跳过初始化")
        return
    
    # 默认AI配置列表
    default_configs = [
        {
            "name": "OpenAI GPT-4",
            "provider": AIProviderEnum.openai,
            "model_name": "gpt-4",
            "api_key": "your-openai-api-key-here",
            "base_url": None,
            "temperature": "0.7",
            "max_tokens": "4000",
            "description": "OpenAI GPT-4 模型配置，适用于复杂推理任务",
            "is_default": True,
            "is_active": True
        },
        {
            "name": "OpenAI GPT-3.5 Turbo",
            "provider": AIProviderEnum.openai,
            "model_name": "gpt-3.5-turbo",
            "api_key": "your-openai-api-key-here",
            "base_url": None,
            "temperature": "0.7",
            "max_tokens": "4000",
            "description": "OpenAI GPT-3.5 Turbo 模型配置，性价比高",
            "is_default": False,
            "is_active": True
        },
        {
            "name": "Anthropic Claude-3",
            "provider": AIProviderEnum.anthropic,
            "model_name": "claude-3-sonnet-20240229",
            "api_key": "your-anthropic-api-key-here",
            "base_url": None,
            "temperature": "0.7",
            "max_tokens": "4000",
            "description": "Anthropic Claude-3 模型配置，擅长分析和推理",
            "is_default": False,
            "is_active": True
        },
        {
            "name": "本地 Ollama",
            "provider": AIProviderEnum.ollama,
            "model_name": "llama2",
            "api_key": "not-required",
            "base_url": "http://localhost:11434",
            "temperature": "0.7",
            "max_tokens": "4000",
            "description": "本地部署的 Ollama 模型配置，数据隐私性好",
            "is_default": False,
            "is_active": False  # 默认不激活，需要用户手动启用
        }
    ]
    
    created_count = 0
    for config_data in default_configs:
        try:
            config_create = AIConfigCreate(**config_data)
            created_config = crud_ai_config.create_ai_config(db, config_create)
            print(f"✅ 创建AI配置: {created_config.name} ({created_config.provider.value})")
            created_count += 1
        except Exception as e:
            print(f"❌ 创建AI配置失败: {config_data['name']} - {e}")
    
    print(f"🎯 成功创建 {created_count} 个默认AI配置")


def main():
    """主函数"""
    print("=" * 50)
    print("🤖 AI配置数据库初始化脚本")
    print("=" * 50)
    
    # 确保数据库表存在
    print("🔧 检查数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化AI配置数据
        init_default_ai_configs(db)
        
        # 提交事务
        db.commit()
        print("💾 数据已成功保存到数据库")
        
    except Exception as e:
        print(f"❌ 初始化过程中发生错误: {e}")
        db.rollback()
        return 1
        
    finally:
        db.close()
    
    print("\n🎯 初始化完成！现在可以通过API管理AI配置了。")
    print("💡 提示：请记得在设置页面中更新API密钥！")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)