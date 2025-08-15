#!/usr/bin/env python3
"""
实体路径迁移脚本
为现有实体添加category_path属性
"""

import os
import json
from pathlib import Path
from data_manager import DataManager

def migrate_entity_paths():
    """为现有实体添加category_path属性"""
    print("🔄 开始实体路径迁移...")
    
    # 初始化数据管理器
    data_manager = DataManager()
    
    # 获取所有实体
    all_entities = data_manager.get_entities()
    print(f"📊 找到 {len(all_entities)} 个实体需要迁移")
    
    updated_count = 0
    
    for entity in all_entities:
        # 检查是否已有category_path属性
        if "category_path" in entity:
            continue
        
        # 获取实体的图谱信息
        graph_id = entity.get("graph_id")
        category_path = "/root"  # 默认路径
        
        if graph_id:
            graph = data_manager.get_graph(graph_id)
            if graph and graph.get("category_id"):
                category = data_manager.get_category(graph["category_id"])
                if category:
                    category_path = category.get("path", "/root")
        
        # 更新实体数据
        entity["category_path"] = category_path
        
        # 保存更新后的实体
        data_manager.save_entity(entity["id"], entity)
        updated_count += 1
        
        print(f"✅ 更新实体: {entity['name']} -> 路径: {category_path}")
    
    print(f"🎉 迁移完成！共更新了 {updated_count} 个实体")
    print(f"📈 统计信息:")
    
    # 统计路径分布
    path_distribution = {}
    all_entities = data_manager.get_entities()  # 重新获取更新后的数据
    
    for entity in all_entities:
        path = entity.get("category_path", "/root")
        path_distribution[path] = path_distribution.get(path, 0) + 1
    
    for path, count in sorted(path_distribution.items()):
        print(f"   📁 {path}: {count} 个实体")

if __name__ == "__main__":
    migrate_entity_paths()