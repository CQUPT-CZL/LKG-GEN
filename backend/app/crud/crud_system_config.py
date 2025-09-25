# app/crud/crud_system_config.py

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
from app.models.sqlite_models import SystemConfig
from app.schemas.system_config import SystemConfigCreate, SystemConfigUpdate

class CRUDSystemConfig:
    def get_config_by_key(self, db: Session, config_key: str) -> Optional[SystemConfig]:
        """根据配置键获取配置"""
        return db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    
    def create_config(self, db: Session, config: SystemConfigCreate) -> SystemConfig:
        """创建新配置"""
        db_config = SystemConfig(
            config_key=config.config_key,
            config_value=config.config_value,
            description=config.description
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config
    
    def update_config(self, db: Session, config_key: str, config_update: SystemConfigUpdate) -> Optional[SystemConfig]:
        """更新配置"""
        db_config = self.get_config_by_key(db, config_key)
        if not db_config:
            return None
        
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        db.commit()
        db.refresh(db_config)
        return db_config
    
    def upsert_config(self, db: Session, config_key: str, config_value: str, description: str = None) -> SystemConfig:
        """创建或更新配置"""
        db_config = self.get_config_by_key(db, config_key)
        if db_config:
            db_config.config_value = config_value
            if description is not None:
                db_config.description = description
        else:
            db_config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                description=description
            )
            db.add(db_config)
        
        db.commit()
        db.refresh(db_config)
        return db_config
    
    def get_chunk_strategy(self, db: Session) -> str:
        """获取当前分块策略"""
        config = self.get_config_by_key(db, "chunk_strategy")
        if config:
            try:
                config_data = json.loads(config.config_value)
                return config_data.get("strategy", "paragraph")
            except json.JSONDecodeError:
                return "paragraph"
        return "paragraph"  # 默认策略
    
    def set_chunk_strategy(self, db: Session, strategy: str) -> SystemConfig:
        """设置分块策略"""
        strategy_descriptions = {
            "full_document": "全部文档作为一个块",
            "paragraph": "按段落分块（默认）",
            "sentence": "按句子分块"
        }
        
        config_value = json.dumps({
            "strategy": strategy,
            "description": strategy_descriptions.get(strategy, "未知策略")
        }, ensure_ascii=False)
        
        return self.upsert_config(
            db=db,
            config_key="chunk_strategy",
            config_value=config_value,
            description="文档分块策略配置"
        )

crud_system_config = CRUDSystemConfig()