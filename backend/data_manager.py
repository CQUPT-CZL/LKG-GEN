import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class DataManager:
    """数据管理器 - 使用JSON文件存储数据"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 创建各个数据目录
        self.graphs_dir = self.data_dir / "graphs"
        self.entities_dir = self.data_dir / "entities"
        self.relations_dir = self.data_dir / "relations"
        self.tasks_dir = self.data_dir / "tasks"
        self.categories_dir = self.data_dir / "categories"  # 新增：分类目录
        
        for dir_path in [self.graphs_dir, self.entities_dir, self.relations_dir, self.tasks_dir, self.categories_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # 初始化根分类
        self._ensure_root_category()
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_json(self, data: Dict[str, Any], file_path: Path):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_all_files_data(self, directory: Path) -> List[Dict[str, Any]]:
        """获取目录下所有JSON文件的数据"""
        data_list = []
        for file_path in directory.glob("*.json"):
            data = self._load_json(file_path)
            if data:
                data_list.append(data)
        return data_list
    
    def save_graph(self, graph_id: str, graph_data: Dict[str, Any]):
        """保存图谱数据"""
        file_path = self.graphs_dir / f"{graph_id}.json"
        self._save_json(graph_data, file_path)
    
    def save_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """保存实体数据"""
        file_path = self.entities_dir / f"{entity_id}.json"
        self._save_json(entity_data, file_path)
    
    def save_relation(self, relation_id: str, relation_data: Dict[str, Any]):
        """保存关系数据"""
        file_path = self.relations_dir / f"{relation_id}.json"
        self._save_json(relation_data, file_path)
    
    # 图谱管理
    def _ensure_root_category(self):
        """确保根分类存在"""
        root_category_path = self.categories_dir / "root.json"
        if not root_category_path.exists():
            root_category = {
                "id": "root",
                "name": "根目录",
                "description": "知识图谱根分类目录",
                "parent_id": None,
                "level": 0,
                "path": "/",
                "children_ids": [],
                "graph_ids": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self._save_json(root_category, root_category_path)
    
    def create_category(self, name: str, description: str = "", parent_id: str = "root") -> Dict[str, Any]:
        """创建新分类"""
        category_id = str(uuid.uuid4())
        
        # 获取父分类信息
        parent_category = self.get_category(parent_id)
        if not parent_category:
            raise ValueError(f"父分类 {parent_id} 不存在")
        
        # 计算分类层级和路径
        level = parent_category["level"] + 1
        if level > 3:  # 限制最大层级为3级
            raise ValueError("分类层级不能超过3级")
        
        parent_path = parent_category["path"]
        path = f"{parent_path}{name}/" if parent_path != "/" else f"/{name}/"
        
        category_data = {
            "id": category_id,
            "name": name,
            "description": description,
            "parent_id": parent_id,
            "level": level,
            "path": path,
            "children_ids": [],
            "graph_ids": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存分类
        self.save_category(category_id, category_data)
        
        # 更新父分类的子分类列表
        parent_category["children_ids"].append(category_id)
        parent_category["updated_at"] = datetime.now().isoformat()
        self.save_category(parent_id, parent_category)
        
        return category_data
    
    def save_category(self, category_id: str, category_data: Dict[str, Any]):
        """保存分类数据"""
        file_path = self.categories_dir / f"{category_id}.json"
        self._save_json(category_data, file_path)
    
    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """获取分类信息"""
        file_path = self.categories_dir / f"{category_id}.json"
        if file_path.exists():
            data = self._load_json(file_path)
            return data if data else None
        return None
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        return self._get_all_files_data(self.categories_dir)
    
    def get_category_tree(self) -> Dict[str, Any]:
        """获取分类树结构"""
        # 确保根分类存在
        self._ensure_root_category()
        
        def build_tree(category_id: str) -> Dict[str, Any]:
            category = self.get_category(category_id)
            if not category:
                # 如果是根分类不存在，抛出异常
                if category_id == "root":
                    raise Exception(f"根分类不存在: {category_id}")
                # 其他分类不存在则返回None
                return None
            
            # 构建子分类树
            children = []
            for child_id in category.get("children_ids", []):
                child_tree = build_tree(child_id)
                if child_tree:
                    children.append(child_tree)
            
            return {
                **category,
                "children": children
            }
        
        return build_tree("root")
    
    def update_category(self, category_id: str, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """更新分类信息"""
        category = self.get_category(category_id)
        if not category:
            return None
        
        # 更新基本信息
        category["name"] = name
        category["description"] = description
        category["updated_at"] = datetime.now().isoformat()
        
        # 如果名称改变，需要更新路径
        if category["name"] != name:
            old_path = category["path"]
            parent_category = self.get_category(category["parent_id"]) if category["parent_id"] else None
            if parent_category:
                parent_path = parent_category["path"]
                new_path = f"{parent_path}{name}/" if parent_path != "/" else f"/{name}/"
                category["path"] = new_path
                
                # 递归更新所有子分类的路径
                self._update_children_paths(category_id, old_path, new_path)
        
        self.save_category(category_id, category)
        return category
    
    def _update_children_paths(self, category_id: str, old_path: str, new_path: str):
        """递归更新子分类路径"""
        category = self.get_category(category_id)
        if not category:
            return
        
        for child_id in category.get("children_ids", []):
            child = self.get_category(child_id)
            if child:
                child["path"] = child["path"].replace(old_path, new_path, 1)
                child["updated_at"] = datetime.now().isoformat()
                self.save_category(child_id, child)
                self._update_children_paths(child_id, old_path, new_path)
    
    def delete_category(self, category_id: str) -> bool:
        """删除分类（递归删除子分类和图谱）"""
        if category_id == "root":
            raise ValueError("不能删除根分类")
        
        category = self.get_category(category_id)
        if not category:
            return False
        
        # 递归删除所有子分类
        for child_id in category.get("children_ids", []):
            self.delete_category(child_id)
        
        # 删除分类下的所有图谱
        for graph_id in category.get("graph_ids", []):
            self.delete_graph(graph_id)
        
        # 从父分类中移除
        if category["parent_id"]:
            parent_category = self.get_category(category["parent_id"])
            if parent_category and category_id in parent_category.get("children_ids", []):
                parent_category["children_ids"].remove(category_id)
                parent_category["updated_at"] = datetime.now().isoformat()
                self.save_category(category["parent_id"], parent_category)
        
        # 删除分类文件
        file_path = self.categories_dir / f"{category_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return True
    
    def create_graph(self, name: str, description: str = "", domain: str = None, category_id: str = "root") -> Dict[str, Any]:
        """创建新的知识图谱"""
        graph_id = str(uuid.uuid4())
        
        # 验证分类是否存在
        category = self.get_category(category_id)
        if not category:
            raise ValueError(f"分类 {category_id} 不存在")
        
        graph_data = {
            "id": graph_id,
            "name": name,
            "description": description,
            "domain": domain or "通用",
            "category_id": category_id,  # 新增：所属分类
            "category_path": category["path"],  # 新增：分类路径
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "entity_count": 0,
            "relation_count": 0,
            "status": "active"
        }
        
        # 保存图谱
        file_path = self.graphs_dir / f"{graph_id}.json"
        self._save_json(graph_data, file_path)
        
        # 更新分类的图谱列表
        category["graph_ids"].append(graph_id)
        category["updated_at"] = datetime.now().isoformat()
        self.save_category(category_id, category)
        
        return graph_data
    
    def get_all_graphs(self) -> List[Dict[str, Any]]:
        """获取所有知识图谱"""
        graphs = self._get_all_files_data(self.graphs_dir)
        
        # 更新实体和关系计数
        for graph in graphs:
            graph_id = graph["id"]
            entities = self.get_entities(graph_id)
            relations = self.get_relations(graph_id)
            entity_count = len(entities)
            relation_count = len(relations)
            
            # 安全更新计数，处理缺少字段的情况
            current_entity_count = graph.get("entity_count", 0)
            current_relation_count = graph.get("relation_count", 0)
            
            # 更新计数
            graph["entity_count"] = entity_count
            graph["relation_count"] = relation_count
            
            # 确保有分类信息（兼容旧数据）
            if "category_id" not in graph:
                graph["category_id"] = "root"
                graph["category_path"] = "/"
            
            # 获取分类名称
            category = self.get_category(graph.get("category_id", "root"))
            graph["category_name"] = category["name"] if category else "根目录"
            
            # 只有当计数发生变化时才保存文件
            if current_entity_count != entity_count or current_relation_count != relation_count:
                graph["updated_at"] = datetime.now().isoformat()
                file_path = self.graphs_dir / f"{graph_id}.json"
                self._save_json(graph, file_path)
        
        return sorted(graphs, key=lambda x: x["created_at"], reverse=True)
    
    def get_graphs_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """获取指定分类下的图谱"""
        all_graphs = self.get_all_graphs()
        
        if category_id == "root":
            # 如果是根分类，返回所有图谱（包括所有子分类的图谱）
            return all_graphs
        else:
            # 如果是具体分类，只返回该分类下的图谱
            return [graph for graph in all_graphs if graph.get("category_id") == category_id]
    
    def get_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """获取指定知识图谱"""
        file_path = self.graphs_dir / f"{graph_id}.json"
        graph_data = self._load_json(file_path)
        
        if graph_data:
            # 更新实体和关系计数
            entities = self.get_entities(graph_id)
            relations = self.get_relations(graph_id)
            entity_count = len(entities)
            relation_count = len(relations)
            
            # 安全更新计数，处理缺少字段的情况
            current_entity_count = graph_data.get("entity_count", 0)
            current_relation_count = graph_data.get("relation_count", 0)
            
            # 更新计数
            graph_data["entity_count"] = entity_count
            graph_data["relation_count"] = relation_count
            
            # 只有当计数发生变化时才保存文件
            if current_entity_count != entity_count or current_relation_count != relation_count:
                graph_data["updated_at"] = datetime.now().isoformat()
                self._save_json(graph_data, file_path)
        
        return graph_data if graph_data else None
    
    def update_graph(self, graph_id: str, name: str, description: str = "", domain: str = None) -> Optional[Dict[str, Any]]:
        """更新知识图谱"""
        file_path = self.graphs_dir / f"{graph_id}.json"
        graph_data = self._load_json(file_path)
        
        if graph_data:
            graph_data["name"] = name
            graph_data["description"] = description
            if domain is not None:
                graph_data["domain"] = domain
            graph_data["updated_at"] = datetime.now().isoformat()
            self._save_json(graph_data, file_path)
            return graph_data
        
        return None
    
    def delete_graph(self, graph_id: str) -> bool:
        """删除知识图谱及其相关数据"""
        file_path = self.graphs_dir / f"{graph_id}.json"
        
        if file_path.exists():
            # 获取图谱信息以便从分类中移除
            graph_data = self._load_json(file_path)
            category_id = graph_data.get("category_id", "root")
            
            # 从分类中移除图谱
            category = self.get_category(category_id)
            if category and graph_id in category.get("graph_ids", []):
                category["graph_ids"].remove(graph_id)
                category["updated_at"] = datetime.now().isoformat()
                self.save_category(category_id, category)
            
            # 删除图谱文件
            file_path.unlink()
            
            # 删除相关实体
            entities = self.get_entities(graph_id)
            for entity in entities:
                self.delete_entity(entity["id"])
            
            # 删除相关关系
            relations = self.get_relations(graph_id)
            for relation in relations:
                self.delete_relation(relation["id"])
            
            return True
        
        return False
    
    # 实体管理
    def create_entity(self, name: str, entity_type: str, description: str = "", graph_id: str = "") -> Dict[str, Any]:
        """创建新实体"""
        entity_id = str(uuid.uuid4())
        entity_data = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "description": description,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "frequency": 1,
            "aliases": []
        }
        
        file_path = self.entities_dir / f"{entity_id}.json"
        self._save_json(entity_data, file_path)
        return entity_data
    
    def get_entities(self, graph_id: str = None) -> List[Dict[str, Any]]:
        """获取实体列表"""
        entities = self._get_all_files_data(self.entities_dir)
        
        if graph_id:
            entities = [e for e in entities if e.get("graph_id") == graph_id]
        
        return sorted(entities, key=lambda x: x["created_at"], reverse=True)
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取指定实体"""
        file_path = self.entities_dir / f"{entity_id}.json"
        return self._load_json(file_path) if file_path.exists() else None
    
    def update_entity(self, entity_id: str, name: str, entity_type: str, description: str = "") -> Optional[Dict[str, Any]]:
        """更新实体"""
        file_path = self.entities_dir / f"{entity_id}.json"
        entity_data = self._load_json(file_path)
        
        if entity_data:
            entity_data["name"] = name
            entity_data["type"] = entity_type
            entity_data["description"] = description
            entity_data["updated_at"] = datetime.now().isoformat()
            self._save_json(entity_data, file_path)
            return entity_data
        
        return None
    
    def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        file_path = self.entities_dir / f"{entity_id}.json"
        
        if file_path.exists():
            # 删除相关关系
            relations = self.get_relations()
            for relation in relations:
                if relation["source_entity_id"] == entity_id or relation["target_entity_id"] == entity_id:
                    self.delete_relation(relation["id"])
            
            # 删除实体文件
            file_path.unlink()
            return True
        
        return False
    
    # 关系管理
    def create_relation(self, source_entity_id: str, target_entity_id: str, 
                       relation_type: str, confidence: float = 1.0, 
                       description: str = "", graph_id: str = "") -> Dict[str, Any]:
        """创建新关系"""
        relation_id = str(uuid.uuid4())
        relation_data = {
            "id": relation_id,
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "relation_type": relation_type,
            "confidence": confidence,
            "description": description,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        file_path = self.relations_dir / f"{relation_id}.json"
        self._save_json(relation_data, file_path)
        return relation_data
    
    def get_relations(self, graph_id: str = None) -> List[Dict[str, Any]]:
        """获取关系列表"""
        relations = self._get_all_files_data(self.relations_dir)
        
        if graph_id:
            relations = [r for r in relations if r.get("graph_id") == graph_id]
        
        # 添加实体名称信息
        for relation in relations:
            source_entity = self.get_entity(relation["source_entity_id"])
            target_entity = self.get_entity(relation["target_entity_id"])
            
            relation["source_entity_name"] = source_entity["name"] if source_entity else "未知实体"
            relation["target_entity_name"] = target_entity["name"] if target_entity else "未知实体"
        
        return sorted(relations, key=lambda x: x["created_at"], reverse=True)
    
    def delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        file_path = self.relations_dir / f"{relation_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    # 可视化数据
    def get_graph_visualization_data(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """获取图谱可视化数据"""
        try:
            graph = self.get_graph(graph_id)
            if not graph:
                return None
            
            entities = self.get_entities(graph_id)
            relations = self.get_relations(graph_id)
            
            # 构建vis-network格式的数据
            nodes = []
            edges = []
            
            # 实体类型颜色映射
            type_colors = {
                "钢铁材料": "#FF6B6B",
                "生产工艺": "#4ECDC4",
                "性能指标": "#45B7D1",
                "应用领域": "#96CEB4",
                "设备": "#FFEAA7",
                "缺陷": "#DDA0DD",
                "化学成分": "#98D8C8",
                "热处理工艺": "#F7DC6F",
                "机械性能": "#BB8FCE",
                "表面处理": "#85C1E9",
                "检测方法": "#F8C471"
            }
            
            # 构建节点
            for entity in entities:
                entity_type = entity.get("type") or entity.get("entity_type", "未知")
                entity_desc = entity.get("description", "无描述")
                color = type_colors.get(entity_type, "#BDC3C7")
                nodes.append({
                    "id": entity["id"],
                    "label": entity["name"],
                    "title": f"类型: {entity_type}\n描述: {entity_desc}",
                    "color": color,
                    "size": min(20 + entity.get("frequency", 1) * 5, 50),
                    "font": {"size": 14},
                    "type": entity_type
                })
            
            # 构建边
            for relation in relations:
                relation_desc = relation.get("description", "无描述")
                edges.append({
                    "id": relation["id"],
                    "from": relation["source_entity_id"],
                    "to": relation["target_entity_id"],
                    "label": relation["relation_type"],
                    "title": f"关系: {relation['relation_type']}\n置信度: {relation['confidence']}\n描述: {relation_desc}",
                    "width": max(1, relation["confidence"] * 3),
                    "arrows": "to",
                    "color": {"color": "#848484", "highlight": "#FF6B6B"},
                    "font": {"size": 12}
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "graph_info": graph
            }
            
        except Exception as e:
            raise e
    
    def get_category_visualization_data(self, category_id: str) -> Optional[Dict[str, Any]]:
        """获取分类的合并可视化数据"""
        try:
            graphs = self.get_graphs_by_category(category_id)
            if not graphs:
                return None
            
            # 如果只有一个图谱，直接返回该图谱的可视化数据
            if len(graphs) == 1:
                return self.get_graph_visualization_data(graphs[0]['id'])
            
            # 合并多个图谱的数据
            all_nodes = []
            all_edges = []
            all_graph_info = []
            
            # 实体类型颜色映射
            type_colors = {
                "钢铁材料": "#FF6B6B",
                "生产工艺": "#4ECDC4",
                "性能指标": "#45B7D1",
                "应用领域": "#96CEB4",
                "设备": "#FFEAA7",
                "缺陷": "#DDA0DD",
                "化学成分": "#98D8C8",
                "热处理工艺": "#F7DC6F",
                "机械性能": "#BB8FCE",
                "表面处理": "#85C1E9",
                "检测方法": "#F8C471"
            }
            
            for graph in graphs:
                graph_id = graph['id']
                entities = self.get_entities(graph_id)
                relations = self.get_relations(graph_id)
                all_graph_info.append(graph)
                
                # 构建节点
                for entity in entities:
                    entity_type = entity.get("type") or entity.get("entity_type", "未知")
                    entity_desc = entity.get("description", "无描述")
                    color = type_colors.get(entity_type, "#BDC3C7")
                    all_nodes.append({
                        "id": entity["id"],
                        "label": entity["name"],
                        "title": f"类型: {entity_type}\n描述: {entity_desc}\n来源图谱: {graph['name']}",
                        "color": color,
                        "size": min(20 + entity.get("frequency", 1) * 5, 50),
                        "font": {"size": 14},
                        "type": entity_type,
                        "graph_id": graph_id,
                        "graph_name": graph['name']
                    })
                
                # 构建边
                for relation in relations:
                    relation_desc = relation.get("description", "无描述")
                    all_edges.append({
                        "id": relation["id"],
                        "from": relation["source_entity_id"],
                        "to": relation["target_entity_id"],
                        "label": relation["relation_type"],
                        "title": f"关系: {relation['relation_type']}\n置信度: {relation['confidence']}\n描述: {relation_desc}\n来源图谱: {graph['name']}",
                        "width": max(1, relation["confidence"] * 3),
                        "arrows": "to",
                        "color": {"color": "#848484", "highlight": "#FF6B6B"},
                        "font": {"size": 12},
                        "graph_id": graph_id,
                        "graph_name": graph['name']
                    })
            
            # 创建合并后的图谱信息
            merged_graph_info = {
                "id": f"merged_{category_id}",
                "name": f"合并视图 - {self.get_category(category_id)['name'] if self.get_category(category_id) else '根分类'}",
                "description": f"包含 {len(graphs)} 个图谱的合并视图",
                "category_id": category_id,
                "merged_graphs": [g['name'] for g in graphs],
                "created_at": datetime.now().isoformat(),
                "is_merged": True
            }
            
            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "graph_info": merged_graph_info,
                "source_graphs": all_graph_info
            }
            
        except Exception as e:
            raise e
    
    # 统计信息
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        graphs = self.get_all_graphs()
        entities = self.get_entities()
        relations = self.get_relations()
        
        # 实体类型统计
        entity_type_stats = {}
        for entity in entities:
            entity_type = entity.get("type", "未知类型")
            entity_type_stats[entity_type] = entity_type_stats.get(entity_type, 0) + 1
        
        # 关系类型统计
        relation_type_stats = {}
        for relation in relations:
            relation_type = relation.get("relation_type", "未知关系")
            relation_type_stats[relation_type] = relation_type_stats.get(relation_type, 0) + 1
        
        return {
            "total_graphs": len(graphs),
            "total_entities": len(entities),
            "total_relations": len(relations),
            "entity_type_distribution": entity_type_stats,
            "relation_type_distribution": relation_type_stats,
            "recent_graphs": graphs[:5],  # 最近5个图谱
            "system_health": "healthy",
            "last_updated": datetime.now().isoformat()
        }
    
    # 批量导入数据
    def import_kg_data(self, graph_id: str, entities_data: List[Dict], relations_data: List[Dict]) -> Dict[str, Any]:
        """批量导入知识图谱数据"""
        imported_entities = []
        imported_relations = []
        entity_id_mapping = {}  # 原始ID到新ID的映射
        
        try:
            # 导入实体
            for entity_data in entities_data:
                new_entity = self.create_entity(
                    name=entity_data["name"],
                    entity_type=entity_data["type"],
                    description=entity_data.get("description", ""),
                    graph_id=graph_id
                )
                imported_entities.append(new_entity)
                
                # 记录ID映射（如果原始数据有ID）
                if "id" in entity_data:
                    entity_id_mapping[entity_data["id"]] = new_entity["id"]
                # 也可以通过名称映射
                entity_id_mapping[entity_data["name"]] = new_entity["id"]
            
            # 导入关系
            for relation_data in relations_data:
                # 查找对应的实体ID
                source_id = None
                target_id = None
                
                # 尝试通过不同方式找到实体ID
                if "source_entity_id" in relation_data:
                    source_id = entity_id_mapping.get(relation_data["source_entity_id"])
                if "target_entity_id" in relation_data:
                    target_id = entity_id_mapping.get(relation_data["target_entity_id"])
                
                # 如果通过ID找不到，尝试通过名称查找
                if not source_id and "source_entity" in relation_data:
                    source_id = entity_id_mapping.get(relation_data["source_entity"])
                if not target_id and "target_entity" in relation_data:
                    target_id = entity_id_mapping.get(relation_data["target_entity"])
                
                if source_id and target_id:
                    new_relation = self.create_relation(
                        source_entity_id=source_id,
                        target_entity_id=target_id,
                        relation_type=relation_data["relation_type"],
                        confidence=relation_data.get("confidence", 1.0),
                        description=relation_data.get("description", ""),
                        graph_id=graph_id
                    )
                    imported_relations.append(new_relation)
            
            return {
                "success": True,
                "imported_entities": len(imported_entities),
                "imported_relations": len(imported_relations),
                "entity_details": imported_entities,
                "relation_details": imported_relations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "imported_entities": len(imported_entities),
                "imported_relations": len(imported_relations)
            }