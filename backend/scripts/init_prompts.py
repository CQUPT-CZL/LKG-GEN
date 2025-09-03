#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库Prompt初始化脚本
将现有的prompt文件导入到数据库中
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
from app.models.sqlite_models import Base, Prompt, PromptTypeEnum
from app.schemas.prompt import PromptCreate
from app.crud import crud_prompt


def read_prompt_file(file_path: str) -> str:
    """读取prompt文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"❌ 读取文件 {file_path} 失败: {e}")
        return ""


def init_default_prompts(db: Session):
    """初始化默认的prompt数据"""
    
    # 定义prompt文件路径
    prompts_dir = project_root / "app" / "prompts"
    
    # 定义要导入的prompt配置
    prompt_configs = [
        {
            "name": "默认NER提取模板",
            "prompt_type": PromptTypeEnum.ner,
            "file_path": prompts_dir / "ner_prompt.txt",
            "description": "用于从钢铁行业设备故障文本中提取命名实体的默认模板",
            "version": "1.0.0",
            "is_default": True,
            "is_active": True
        },
        {
            "name": "默认关系抽取模板",
            "prompt_type": PromptTypeEnum.re,
            "file_path": prompts_dir / "re_prompt.txt",
            "description": "用于从钢铁行业设备故障文本中提取实体关系的默认模板",
            "version": "1.0.0",
            "is_default": True,
            "is_active": True
        },
        {
            "name": "默认实体验证模板",
            "prompt_type": PromptTypeEnum.entity_validation,
            "file_path": prompts_dir / "entity_validation_prompt.txt",
            "description": "用于验证提取实体准确性的默认模板",
            "version": "1.0.0",
            "is_default": True,
            "is_active": True
        }
    ]
    
    print("🚀 开始初始化Prompt数据...")
    
    for config in prompt_configs:
        try:
            # 检查是否已存在相同类型的默认prompt
            existing_prompt = crud_prompt.get_default_prompt(db, config["prompt_type"])
            if existing_prompt:
                print(f"⚠️  {config['prompt_type'].value} 类型的默认prompt已存在，跳过创建")
                continue
            
            # 读取prompt文件内容
            content = read_prompt_file(config["file_path"])
            if not content:
                print(f"❌ 跳过 {config['name']}，文件内容为空")
                continue
            
            # 创建prompt记录
            prompt_data = PromptCreate(
                name=config["name"],
                prompt_type=config["prompt_type"],
                content=content,
                description=config["description"],
                version=config["version"],
                is_default=config["is_default"],
                is_active=config["is_active"]
            )
            
            prompt = crud_prompt.create_prompt(db, prompt_data)
            print(f"✅ 成功创建prompt: {prompt.name} (ID: {prompt.id})")
            
        except Exception as e:
            print(f"❌ 创建prompt {config['name']} 失败: {e}")
            continue
    
    print("🎉 Prompt数据初始化完成！")


def main():
    """主函数"""
    print("=" * 50)
    print("📚 Prompt数据库初始化脚本")
    print("=" * 50)
    
    # 创建数据库表（如果不存在）
    print("🔧 检查数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化prompt数据
        init_default_prompts(db)
        
        # 提交事务
        db.commit()
        print("💾 数据已成功保存到数据库")
        
    except Exception as e:
        print(f"❌ 初始化过程中发生错误: {e}")
        db.rollback()
        return 1
        
    finally:
        db.close()
    
    print("\n🎯 初始化完成！现在可以通过API管理Prompt模板了。")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)