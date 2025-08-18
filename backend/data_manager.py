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
        self.entities_dir = self.data_dir / "entities"  # 全局实体目录，按图谱分组
        self.relations_dir = self.data_dir / "relations"  # 全局关系目录，按图谱分组
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
    
    def _get_graph_name(self, graph_id: str) -> str:
        """获取图谱名称（避免循环调用）"""
        file_path = self.graphs_dir / f"{graph_id}.json"
        graph_data = self._load_json(file_path)
        
        if not graph_data:
            raise ValueError(f"图谱 {graph_id} 不存在")
        
        graph_name = graph_data.get('name')
        if not graph_name:
            raise ValueError(f"图谱 {graph_id} 没有名称")
        
        return graph_name
    
    def _get_graph_entities_dir(self, graph_id: str) -> Path:
        """获取指定图谱的实体目录 - 使用ner_output目录"""
        graph_name = self._get_graph_name(graph_id)
        ner_output_dir = self.data_dir / "ner_output" / graph_name
        ner_output_dir.mkdir(parents=True, exist_ok=True)
        return ner_output_dir
    
    def _get_graph_relations_dir(self, graph_id: str) -> Path:
        """获取指定图谱的关系目录 - 使用re_output目录"""
        graph_name = self._get_graph_name(graph_id)
        re_output_dir = self.data_dir / "re_output" / graph_name
        re_output_dir.mkdir(parents=True, exist_ok=True)
        return re_output_dir
    
    def save_entity(self, entity_id: str, entity_data: Dict[str, Any], graph_id: str = None):
        """保存实体数据到指定图谱目录"""
        if graph_id:
            # 保存到图谱特定目录
            graph_entities_dir = self._get_graph_entities_dir(graph_id)
            file_path = graph_entities_dir / f"{entity_id}.json"
        else:
            # 兼容旧版本，保存到全局目录
            file_path = self.entities_dir / f"{entity_id}.json"
        self._save_json(entity_data, file_path)
    
    def save_relation(self, relation_id: str, relation_data: Dict[str, Any], graph_id: str = None):
        """保存关系数据到指定图谱目录"""
        if graph_id:
            # 保存到图谱特定目录
            graph_relations_dir = self._get_graph_relations_dir(graph_id)
            file_path = graph_relations_dir / f"{relation_id}.json"
        else:
            # 兼容旧版本，保存到全局目录
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
        
        # 删除分类下的所有图谱（不删除对应分类，避免循环调用）
        for graph_id in category.get("graph_ids", []):
            self.delete_graph(graph_id, delete_category=False)
        
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
    
    def _delete_category_only(self, category_id: str) -> bool:
        """仅删除分类本身，不递归删除子分类和图谱（用于避免循环调用）"""
        if category_id == "root":
            return False
        
        category = self.get_category(category_id)
        if not category:
            return False
        
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
    
    def delete_graph(self, graph_id: str, delete_category: bool = True) -> bool:
        """删除知识图谱及其相关数据
        
        Args:
            graph_id: 图谱ID
            delete_category: 是否同时删除对应的分类（默认True）
        """
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
                
                # 如果分类下没有其他图谱且不是根分类，则删除该分类
                if (delete_category and 
                    category_id != "root" and 
                    len(category.get("graph_ids", [])) == 0 and 
                    len(category.get("children_ids", [])) == 0):
                    self._delete_category_only(category_id)
            
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
        
        # 获取图谱的分类路径
        category_path = "/root"
        if graph_id:
            graph = self.get_graph(graph_id)
            if graph and graph.get("category_id"):
                category = self.get_category(graph["category_id"])
                if category:
                    category_path = category.get("path", "/root")
        
        entity_data = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "description": description,
            "graph_id": graph_id,
            "category_path": category_path,  # 添加分类路径属性
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "frequency": 1,
            "aliases": []
        }
        
        # 使用新的图谱特定存储逻辑
        self.save_entity(entity_id, entity_data, graph_id)
        return entity_data
    
    def get_entities(self, graph_id: str = None) -> List[Dict[str, Any]]:
        """获取实体列表"""
        if graph_id:
            # 从图谱特定目录读取
            graph_entities_dir = self._get_graph_entities_dir(graph_id)
            entities = []
            
            # 读取 ner_output 目录中的实体文件
            for json_file in graph_entities_dir.glob("*.json"):
                if json_file.name != "all_entities_disambiguated.json":  # 跳过消歧文件
                    entity_data = self._load_json(json_file)
                    if isinstance(entity_data, list):
                        # 转换 NER 输出格式为标准实体格式
                        for entity in entity_data:
                            entities.append({
                                "id": entity.get("entity_id", str(uuid.uuid4())),
                                "name": entity.get("entity_text", entity.get("name", "")),
                                "type": entity.get("entity_type", entity.get("type", "")),
                                "description": entity.get("entity_description", entity.get("description", "")),
                                "graph_id": graph_id,
                                "frequency": len(entity.get("chunk_id", [])) if entity.get("chunk_id") else 1,
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat(),
                                "aliases": entity.get("aliases", [])
                            })
                    elif isinstance(entity_data, dict):
                        # 单个实体文件
                        entities.append(entity_data)
            
            # 然后读取其他单独的实体文件（向后兼容）
            other_entities = self._get_all_files_data(graph_entities_dir)
            entities.extend(other_entities)
            
            # 同时也从全局目录中查找该图谱的实体（向后兼容）
            global_entities = self._get_all_files_data(self.entities_dir)
            global_entities = [e for e in global_entities if e.get("graph_id") == graph_id]
            entities.extend(global_entities)
        else:
            # 获取所有实体：全局目录 + 所有图谱目录
            entities = self._get_all_files_data(self.entities_dir)
            # 遍历所有图谱子目录
            for graph_dir in self.entities_dir.iterdir():
                if graph_dir.is_dir():
                    # 读取消歧文件
                    disambig_file = graph_dir / "all_entities_disambiguated.json"
                    if disambig_file.exists():
                        disambig_data = self._load_json(disambig_file)
                        if isinstance(disambig_data, list):
                            for entity in disambig_data:
                                entities.append({
                                    "id": entity.get("entity_id", str(uuid.uuid4())),
                                    "name": entity.get("entity_text", entity.get("name", "")),
                                    "type": entity.get("entity_type", entity.get("type", "")),
                                    "description": entity.get("entity_description", entity.get("description", "")),
                                    "graph_id": graph_dir.name,
                                    "frequency": len(entity.get("chunk_id", [])),
                                    "created_at": datetime.now().isoformat(),
                                    "updated_at": datetime.now().isoformat(),
                                    "aliases": entity.get("aliases", [])
                                })
                    # 读取其他单独文件
                    graph_entities = self._get_all_files_data(graph_dir)
                    entities.extend(graph_entities)
        
        # 过滤掉非字典对象，确保排序安全
        valid_entities = [e for e in entities if isinstance(e, dict)]
        return sorted(valid_entities, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_entity(self, entity_id: str, graph_id: str = None) -> Optional[Dict[str, Any]]:
        """获取指定实体"""
        if graph_id:
            # 先从图谱特定目录查找
            graph_entities_dir = self._get_graph_entities_dir(graph_id)
            file_path = graph_entities_dir / f"{entity_id}.json"
            if file_path.exists():
                return self._load_json(file_path)
        
        # 从全局目录查找（向后兼容）
        file_path = self.entities_dir / f"{entity_id}.json"
        if file_path.exists():
            return self._load_json(file_path)
        
        # 如果没有指定graph_id，遍历所有图谱目录查找
        if not graph_id:
            for graph_dir in self.entities_dir.iterdir():
                if graph_dir.is_dir():
                    file_path = graph_dir / f"{entity_id}.json"
                    if file_path.exists():
                        return self._load_json(file_path)
        
        return None
    
    def update_entity(self, entity_id: str, name: str, entity_type: str, description: str = "") -> Optional[Dict[str, Any]]:
        """更新实体"""
        # 首先尝试从全局目录查找
        file_path = self.entities_dir / f"{entity_id}.json"
        entity_data = self._load_json(file_path) if file_path.exists() else None
        
        # 如果全局目录没找到，遍历图谱子目录查找
        if not entity_data:
            for graph_dir in self.entities_dir.iterdir():
                if graph_dir.is_dir():
                    graph_file_path = graph_dir / f"{entity_id}.json"
                    if graph_file_path.exists():
                        entity_data = self._load_json(graph_file_path)
                        file_path = graph_file_path
                        break
        
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
        # 首先尝试从全局目录删除
        file_path = self.entities_dir / f"{entity_id}.json"
        found = False
        
        if file_path.exists():
            file_path.unlink()
            found = True
        
        # 遍历图谱子目录查找并删除
        for graph_dir in self.entities_dir.iterdir():
            if graph_dir.is_dir():
                graph_file_path = graph_dir / f"{entity_id}.json"
                if graph_file_path.exists():
                    graph_file_path.unlink()
                    found = True
        
        if found:
            # 删除相关关系
            relations = self.get_relations()
            for relation in relations:
                if relation["source_entity_id"] == entity_id or relation["target_entity_id"] == entity_id:
                    self.delete_relation(relation["id"])
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
        
        # 使用新的图谱特定存储逻辑
        self.save_relation(relation_id, relation_data, graph_id)
        return relation_data
    
    def get_relations(self, graph_id: str = None) -> List[Dict[str, Any]]:
        """获取关系列表"""
        if graph_id:
            # 从图谱特定目录读取
            graph_relations_dir = self._get_graph_relations_dir(graph_id)
            relations = []
            
            # 读取 re_output 目录中的关系文件
            for json_file in graph_relations_dir.glob("*.json"):
                if json_file.name != "all_relations_disambiguated.json":  # 跳过消歧文件
                    relation_data = self._load_json(json_file)
                    if isinstance(relation_data, list):
                        # 转换 RE 输出格式为标准关系格式
                        for relation in relation_data:
                            relations.append({
                                "id": relation.get("relation_id", str(uuid.uuid4())),
                                "relation_type": relation.get("relation", relation.get("type", "")),
                                "description": relation.get("relation_description", relation.get("description", "")),
                                "source_entity_id": relation.get("head", ""),
                                "target_entity_id": relation.get("tail", ""),
                                "graph_id": graph_id,
                                "confidence": 1.0,
                                "frequency": len(relation.get("source_chunk_id", [])) if relation.get("source_chunk_id") else 1,
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            })
                    elif isinstance(relation_data, dict):
                        # 单个关系文件
                        relations.append(relation_data)
            
            # 然后读取其他单独的关系文件（向后兼容）
            other_relations = self._get_all_files_data(graph_relations_dir)
            relations.extend(other_relations)
            
            # 同时也从全局目录中查找该图谱的关系（向后兼容）
            global_relations = self._get_all_files_data(self.relations_dir)
            global_relations = [r for r in global_relations if r.get("graph_id") == graph_id]
            relations.extend(global_relations)
        else:
            # 获取所有关系：全局目录 + 所有图谱目录
            relations = self._get_all_files_data(self.relations_dir)
            # 遍历所有图谱子目录
            for graph_dir in self.relations_dir.iterdir():
                if graph_dir.is_dir():
                    # 读取消歧文件
                    disambig_file = graph_dir / "all_relations_disambiguated.json"
                    if disambig_file.exists():
                        disambig_data = self._load_json(disambig_file)
                        if isinstance(disambig_data, list):
                            for relation in disambig_data:
                                relations.append({
                                    "id": relation.get("relation_id", str(uuid.uuid4())),
                                    "relation_type": relation.get("relation_type", relation.get("type", "")),
                                    "description": relation.get("relation_description", relation.get("description", "")),
                                    "source_entity_id": relation.get("source_entity_id", ""),
                                    "target_entity_id": relation.get("target_entity_id", ""),
                                    "graph_id": graph_dir.name,
                                    "confidence": 1.0,
                                    "frequency": len(relation.get("chunk_id", [])),
                                    "created_at": datetime.now().isoformat(),
                                    "updated_at": datetime.now().isoformat()
                                })
                    # 读取其他单独文件
                    graph_relations = self._get_all_files_data(graph_dir)
                    relations.extend(graph_relations)
        
        # 过滤掉非字典对象，确保处理安全
        valid_relations = [r for r in relations if isinstance(r, dict)]
        
        # 添加实体名称信息
        for relation in valid_relations:
            # 如果source_entity_id和target_entity_id存储的是实体名称，需要先找到对应的实体ID
            source_entity_name = relation["source_entity_id"]
            target_entity_name = relation["target_entity_id"]
            
            # 从当前图谱的实体中查找匹配的实体
            entities = self.get_entities(graph_id) if graph_id else self.get_entities()
            
            source_entity = None
            target_entity = None
            
            for entity in entities:
                if entity["name"] == source_entity_name:
                    source_entity = entity
                if entity["name"] == target_entity_name:
                    target_entity = entity
            
            relation["source_entity_name"] = source_entity["name"] if source_entity else source_entity_name
            relation["target_entity_name"] = target_entity["name"] if target_entity else target_entity_name
        
        return sorted(valid_relations, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        # 首先尝试从全局目录删除
        file_path = self.relations_dir / f"{relation_id}.json"
        found = False
        
        if file_path.exists():
            file_path.unlink()
            found = True
        
        # 遍历图谱子目录查找并删除
        for graph_dir in self.relations_dir.iterdir():
            if graph_dir.is_dir():
                graph_file_path = graph_dir / f"{relation_id}.json"
                if graph_file_path.exists():
                    graph_file_path.unlink()
                    found = True
        
        return found
    
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
        """获取分类的可视化数据（基于实体路径筛选）"""
        try:
            # 获取当前分类信息
            current_category = self.get_category(category_id)
            if not current_category:
                return None
            
            current_path = current_category.get("path", "/root")
            
            # 获取所有实体，根据路径筛选
            all_entities = self.get_entities()
            filtered_entities = []
            
            for entity in all_entities:
                entity_path = entity.get("category_path", "/root")
                # 检查实体路径是否匹配当前分类路径
                if entity_path.startswith(current_path):
                    filtered_entities.append(entity)
            
            if not filtered_entities:
                return None
            
            # 获取相关的关系（只包含筛选后实体之间的关系）
            entity_ids = {entity["id"] for entity in filtered_entities}
            all_relations = self.get_relations()
            filtered_relations = [
                relation for relation in all_relations
                if relation["source_entity_id"] in entity_ids and relation["target_entity_id"] in entity_ids
            ]
            
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
            nodes = []
            entity_name_count = {}  # 统计同名实体数量
            
            # 先统计同名实体
            for entity in filtered_entities:
                name = entity["name"]
                entity_name_count[name] = entity_name_count.get(name, 0) + 1
            
            # 去重：对于同名实体，只保留一个，但合并其属性
            unique_entities = {}
            for entity in filtered_entities:
                name = entity["name"]
                if name not in unique_entities:
                    # 获取图谱信息
                    graph = self.get_graph(entity["graph_id"]) if entity.get("graph_id") else None
                    graph_name = graph["name"] if graph else "未知图谱"
                    
                    entity_type = entity.get("type") or entity.get("entity_type", "未知")
                    entity_desc = entity.get("description", "无描述")
                    color = type_colors.get(entity_type, "#BDC3C7")
                    
                    unique_entities[name] = {
                        "id": entity["id"],
                        "label": name,
                        "title": f"类型: {entity_type}\n描述: {entity_desc}\n路径: {entity.get('category_path', '/root')}\n来源图谱: {graph_name}\n出现次数: {entity_name_count[name]}",
                        "color": color,
                        "size": min(20 + entity.get("frequency", 1) * 5 + entity_name_count[name] * 3, 60),
                        "font": {"size": 14},
                        "type": entity_type,
                        "category_path": entity.get("category_path", "/root"),
                        "occurrence_count": entity_name_count[name],
                        "source_graphs": [graph_name]
                    }
                else:
                    # 合并来源图谱信息
                    graph = self.get_graph(entity["graph_id"]) if entity.get("graph_id") else None
                    graph_name = graph["name"] if graph else "未知图谱"
                    if graph_name not in unique_entities[name]["source_graphs"]:
                        unique_entities[name]["source_graphs"].append(graph_name)
            
            nodes = list(unique_entities.values())
            
            # 构建边（需要更新实体ID映射）
            entity_id_mapping = {entity["id"]: unique_entities[entity["name"]]["id"] for entity in filtered_entities if entity["name"] in unique_entities}
            
            edges = []
            for relation in filtered_relations:
                source_id = entity_id_mapping.get(relation["source_entity_id"])
                target_id = entity_id_mapping.get(relation["target_entity_id"])
                
                if source_id and target_id and source_id != target_id:  # 避免自环
                    relation_desc = relation.get("description", "无描述")
                    edges.append({
                        "id": relation["id"],
                        "from": source_id,
                        "to": target_id,
                        "label": relation["relation_type"],
                        "title": f"关系: {relation['relation_type']}\n置信度: {relation['confidence']}\n描述: {relation_desc}",
                        "width": max(1, relation["confidence"] * 3),
                        "arrows": "to",
                        "color": {"color": "#848484", "highlight": "#FF6B6B"},
                        "font": {"size": 12}
                    })
            
            # 创建分类视图信息
            category_info = {
                "id": f"category_{category_id}",
                "name": f"分类视图 - {current_category['name']}",
                "description": f"路径: {current_path}，包含 {len(nodes)} 个去重实体",
                "category_id": category_id,
                "category_path": current_path,
                "created_at": datetime.now().isoformat(),
                "is_category_view": True,
                "entity_count": len(nodes),
                "relation_count": len(edges)
            }
            
            return {
                "nodes": nodes,
                "edges": edges,
                "graph_info": category_info
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
    
    def _clear_graph_data(self, graph_id: str):
        """清理指定图谱的所有数据"""
        print(f"🗑️ DataManager: 清理图谱 {graph_id} 的旧数据...")
        
        # 清理图谱特定目录中的实体
        graph_entities_dir = self._get_graph_entities_dir(graph_id)
        if graph_entities_dir.exists():
            for file_path in graph_entities_dir.glob("*.json"):
                file_path.unlink()
            print(f"✅ DataManager: 已清理图谱实体目录: {graph_entities_dir}")
        
        # 清理图谱特定目录中的关系
        graph_relations_dir = self._get_graph_relations_dir(graph_id)
        if graph_relations_dir.exists():
            for file_path in graph_relations_dir.glob("*.json"):
                file_path.unlink()
            print(f"✅ DataManager: 已清理图谱关系目录: {graph_relations_dir}")
        
        # 清理全局目录中属于该图谱的数据（向后兼容）
        entities_to_remove = []
        for file_path in self.entities_dir.glob("*.json"):
            if file_path.is_file():
                entity_data = self._load_json(file_path)
                if entity_data.get("graph_id") == graph_id:
                    entities_to_remove.append(file_path)
        
        for file_path in entities_to_remove:
            file_path.unlink()
            
        relations_to_remove = []
        for file_path in self.relations_dir.glob("*.json"):
            if file_path.is_file():
                relation_data = self._load_json(file_path)
                if relation_data.get("graph_id") == graph_id:
                    relations_to_remove.append(file_path)
        
        for file_path in relations_to_remove:
            file_path.unlink()
            
        print(f"🗑️ DataManager: 已清理全局目录中的 {len(entities_to_remove)} 个实体和 {len(relations_to_remove)} 个关系")
    
    # 批量导入数据
    def import_kg_data(self, graph_id: str, entities_data: List[Dict], relations_data: List[Dict]) -> Dict[str, Any]:
        """批量导入知识图谱数据（附加模式：先清理旧数据，再导入新数据）"""
        imported_entities = []
        imported_relations = []
        entity_id_mapping = {}  # 原始ID到新ID的映射
        
        print(f"🔄 DataManager: 开始导入数据到图谱 {graph_id}")
        print(f"📊 DataManager: 待导入实体数量: {len(entities_data)}")
        print(f"📊 DataManager: 待导入关系数量: {len(relations_data)}")
        
        # 附加模式：先清理旧数据
        self._clear_graph_data(graph_id)
        
        try:
            # 导入实体
            print(f"🔄 DataManager: 开始导入实体...")
            for i, entity_data in enumerate(entities_data):
                try:
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
                    
                    if (i + 1) % 10 == 0 or i == 0:
                        print(f"📝 DataManager: 已导入实体 {i + 1}/{len(entities_data)}")
                        
                except Exception as e:
                    print(f"❌ DataManager: 导入实体失败 {entity_data.get('name', 'Unknown')}: {e}")
                    continue
            
            print(f"✅ DataManager: 实体导入完成，成功导入 {len(imported_entities)} 个实体")
            
            # 导入关系
            print(f"🔄 DataManager: 开始导入关系...")
            for i, relation_data in enumerate(relations_data):
                try:
                    # 查找对应的实体ID
                    source_id = None
                    target_id = None
                    source_name = relation_data.get("source_entity", "Unknown")
                    target_name = relation_data.get("target_entity", "Unknown")
                    
                    # 尝试通过不同方式找到实体ID
                    if "source_entity_id" in relation_data:
                        source_id = entity_id_mapping.get(relation_data["source_entity_id"])
                        if not source_id:
                            print(f"⚠️ DataManager: 无法通过ID找到源实体: {relation_data['source_entity_id']}")
                    if "target_entity_id" in relation_data:
                        target_id = entity_id_mapping.get(relation_data["target_entity_id"])
                        if not target_id:
                            print(f"⚠️ DataManager: 无法通过ID找到目标实体: {relation_data['target_entity_id']}")
                    
                    # 如果通过ID找不到，尝试通过名称查找
                    if not source_id and "source_entity" in relation_data:
                        source_id = entity_id_mapping.get(relation_data["source_entity"])
                        if not source_id:
                            print(f"⚠️ DataManager: 无法通过名称找到源实体: {source_name}")
                    if not target_id and "target_entity" in relation_data:
                        target_id = entity_id_mapping.get(relation_data["target_entity"])
                        if not target_id:
                            print(f"⚠️ DataManager: 无法通过名称找到目标实体: {target_name}")
                    
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
                    else:
                        print(f"❌ DataManager: 无法创建关系，缺少源实体ID或目标实体ID: {source_name} -> {target_name}")
                    
                    if (i + 1) % 10 == 0 or i == 0:
                        print(f"📝 DataManager: 已处理关系 {i + 1}/{len(relations_data)}")
                        
                except Exception as e:
                    print(f"❌ DataManager: 导入关系失败: {e}")
                    continue
                    
            print(f"✅ DataManager: 关系导入完成，成功导入 {len(imported_relations)} 个关系")
            
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