from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import uuid
import shutil
from datetime import datetime
import asyncio
from pathlib import Path
import psutil
from enum import Enum

# 导入知识图谱构建模块
from kg_builder import KnowledgeGraphBuilder
from data_manager import DataManager

app = FastAPI(title="知识图谱生成系统 API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据管理器
# 使用项目根目录下的data文件夹
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, "data")
print(data_dir)
data_manager = DataManager(data_dir)
kg_builder = KnowledgeGraphBuilder(data_manager)

# 数据模型定义
class GraphCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    category_id: Optional[str] = "root"

class CategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    parent_id: Optional[str] = "root"

class CategoryUpdateRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class EntityCreateRequest(BaseModel): 
    name: str
    type: str
    description: Optional[str] = ""
    graph_id: str

class RelationCreateRequest(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    confidence: Optional[float] = 1.0
    description: Optional[str] = ""
    graph_id: str

class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None

class SystemPerformance(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    timestamp: str

class TaskType(str, Enum):
    KNOWLEDGE_GRAPH_BUILD = "knowledge_graph_build"
    ENTITY_EXTRACTION = "entity_extraction"
    RELATION_EXTRACTION = "relation_extraction"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    id: str
    name: str
    type: TaskType
    status: TaskStatus
    progress: int = 0
    message: str = ""
    created_at: str
    updated_at: str
    files: List[str] = []
    target_graph_id: Optional[str] = None
    description: Optional[str] = ""
    result: Optional[Dict[str, Any]] = None

class CreateTaskRequest(BaseModel):
    name: str
    type: TaskType = TaskType.KNOWLEDGE_GRAPH_BUILD
    target_graph_id: Optional[str] = None
    description: Optional[str] = ""
    files: List[str] = []

# 全局任务状态存储
task_status: Dict[str, ProcessingStatus] = {}
# 全局任务存储
tasks: Dict[str, Task] = {}

# API路由

@app.get("/")
async def root():
    return {"message": "知识图谱生成系统 API 服务正在运行"}

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/system/performance")
async def get_system_performance() -> SystemPerformance:
    """获取实时系统性能数据"""
    try:
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 获取内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 获取磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # 获取网络I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": float(network.bytes_sent),
            "bytes_recv": float(network.bytes_recv),
            "packets_sent": float(network.packets_sent),
            "packets_recv": float(network.packets_recv)
        }
        
        return SystemPerformance(
            cpu_usage=round(cpu_percent, 2),
            memory_usage=round(memory_percent, 2),
            disk_usage=round(disk_percent, 2),
            network_io=network_io,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统性能数据失败: {str(e)}")

# 统计信息
@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        stats = data_manager.get_system_stats()
        return stats
    except Exception as e:
        import traceback
        print(f"Error in get_stats: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# 图谱管理
@app.get("/api/graphs")
async def get_graphs():
    """获取所有知识图谱"""
    try:
        graphs = data_manager.get_all_graphs()
        return graphs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graphs")
async def create_graph(request: dict):
    """创建新的知识图谱（纯附加模式：一级分类即图谱）"""
    try:
        name = request.get("name")
        description = request.get("description", "")
        domain = request.get("domain")
        
        if not name:
            raise HTTPException(status_code=400, detail="图谱名称不能为空")
        
        # 在纯附加模式下，创建图谱时同时创建对应的一级分类
        print("*" * 50)
        print(f"DEBUG - 开始创建分类: {name}")
        
        try:
            category_data = data_manager.create_category(name, description, "root")
            category_id = category_data["id"]
            print(f"DEBUG - 分类创建成功: {category_id}")
            print(f"DEBUG - 分类数据: {category_data}")
            
            # 检查分类文件是否存在
            import os
            category_file = os.path.join(data_manager.categories_dir, f"{category_id}.json")
            print(f"DEBUG - 分类文件路径: {category_file}")
            print(f"DEBUG - 分类文件是否存在: {os.path.exists(category_file)}")
            
            # 创建图谱并关联到新创建的分类
            graph_data = data_manager.create_graph(name, description, domain, category_id)
            print(f"DEBUG - 图谱创建成功: {graph_data['id']}")
            
            # 🆕 为新创建的图谱创建专用数据目录
            import config
            config.create_graph_directories(graph_data['id'])
            print(f"📁 已为图谱 '{graph_data['id']}' 创建专用数据目录")
            
            print("*" * 50)
            return graph_data
        except Exception as inner_e:
            print(f"DEBUG - 创建分类或图谱时出错: {inner_e}")
            raise inner_e
    except ValueError as e:
        print(f"DEBUG - 值错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG - 创建图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建图谱失败: {str(e)}")

@app.get("/api/graphs/{graph_id}")
async def get_graph(graph_id: str):
    """获取指定知识图谱的详细信息"""
    try:
        graph = data_manager.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/graphs/{graph_id}")
async def update_graph(graph_id: str, request: dict):
    """更新知识图谱信息"""
    try:
        name = request.get("name")
        description = request.get("description", "")
        domain = request.get("domain")
        
        if not name:
            raise HTTPException(status_code=400, detail="图谱名称不能为空")
        
        graph = data_manager.update_graph(
            graph_id=graph_id,
            name=name,
            description=description,
            domain=domain
        )
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        return graph
    except Exception as e:
        print(f"更新图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新图谱失败: {str(e)}")

@app.delete("/api/graphs/{graph_id}")
async def delete_graph(graph_id: str):
    """删除知识图谱"""
    try:
        success = data_manager.delete_graph(graph_id)
        if not success:
            raise HTTPException(status_code=404, detail="图谱不存在")
        return {"message": "图谱删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 文档上传和处理
from fastapi import Form

@app.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    target_graph_id: str = Form(...)  # 目标图谱ID（必填）
):
    """上传文档并附加到现有知识图谱
    
    Args:
        file: 上传的文档文件
        target_graph_id: 要附加到的图谱ID
    """
    try:
        # 验证目标图谱是否存在
        if not target_graph_id:
            raise HTTPException(status_code=400, detail="必须指定目标图谱ID")
        target_graph = data_manager.get_graph(target_graph_id)
        if not target_graph:
            raise HTTPException(status_code=404, detail="目标图谱不存在")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"{task_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 创建任务对象
        current_time = datetime.now().isoformat()
        task = Task(
            id=task_id,
            name=f"知识图谱构建 - {file.filename}",
            type=TaskType.KNOWLEDGE_GRAPH_BUILD,
            status=TaskStatus.PENDING,
            progress=0,
            message="文档上传成功，等待处理（附加到现有图谱）",
            created_at=current_time,
            updated_at=current_time,
            files=[file.filename],
            build_mode="append",
            target_graph_id=target_graph_id,
            description=f"通过文档上传创建的知识图谱构建任务"
        )
        
        # 存储任务
        tasks[task_id] = task
        
        # 初始化任务状态（兼容现有代码）
        task_status[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="文档上传成功，等待处理（附加到现有图谱）"
        )
        
        # 添加后台任务
        background_tasks.add_task(
            process_document, 
            task_id, 
            str(file_path), 
            file.filename, 
            target_graph_id
        )
        
        return {
            "task_id": task_id,
            "message": "文档上传成功，开始处理（附加到现有图谱）",
            "filename": file.filename,
            "target_graph_id": target_graph_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务处理状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_status[task_id]

# 任务管理API
@app.get("/api/tasks")
async def get_tasks():
    """获取所有任务列表"""
    try:
        return list(tasks.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取特定任务信息"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks[task_id]

@app.post("/api/tasks")
async def create_task(background_tasks: BackgroundTasks, task_data: CreateTaskRequest):
    """创建新任务"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        # 创建任务对象
        task = Task(
            id=task_id,
            name=task_data.name,
            type=task_data.type,
            status=TaskStatus.PENDING,
            progress=0,
            message="任务已创建，等待处理",
            created_at=current_time,
            updated_at=current_time,
            files=task_data.files,
            target_graph_id=task_data.target_graph_id,
            description=task_data.description
        )
        
        # 存储任务
        tasks[task_id] = task
        
        # 初始化任务状态（兼容现有代码）
        task_status[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="任务已创建，等待处理"
        )
        
        # 如果是知识图谱构建任务，启动后台处理
        if task_data.type == TaskType.KNOWLEDGE_GRAPH_BUILD:
            # 这里需要根据files列表处理文档
            # 暂时返回任务信息，实际文档处理需要通过文件上传接口
            pass
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    try:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 如果任务正在处理中，先取消任务
        if tasks[task_id].status == TaskStatus.PROCESSING:
            tasks[task_id].status = TaskStatus.CANCELLED
            tasks[task_id].message = "任务已取消"
            tasks[task_id].updated_at = datetime.now().isoformat()
        
        # 删除任务
        del tasks[task_id]
        if task_id in task_status:
            del task_status[task_id]
        
        return {"message": "任务删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = tasks[task_id]
        if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            raise HTTPException(status_code=400, detail="任务无法取消")
        
        # 更新任务状态
        task.status = TaskStatus.CANCELLED
        task.message = "任务已取消"
        task.updated_at = datetime.now().isoformat()
        
        # 同步更新task_status
        if task_id in task_status:
            task_status[task_id].status = "cancelled"
            task_status[task_id].message = "任务已取消"
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 实体管理
@app.get("/api/graphs/{graph_id}/entities")
async def get_entities(graph_id: str):
    """获取图谱中的所有实体"""
    try:
        entities = data_manager.get_entities(graph_id)
        print(entities)
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/entities")
async def create_entity(entity_data: EntityCreateRequest):
    """创建新实体"""
    try:
        entity = data_manager.create_entity(
            name=entity_data.name,
            entity_type=entity_data.type,
            description=entity_data.description,
            graph_id=entity_data.graph_id
        )
        return entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/entities/{entity_id}")
async def update_entity(entity_id: str, entity_data: EntityCreateRequest):
    """更新实体信息"""
    try:
        entity = data_manager.update_entity(
            entity_id=entity_id,
            name=entity_data.name,
            entity_type=entity_data.type,
            description=entity_data.description
        )
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        return entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/entities/{entity_id}")
async def delete_entity(entity_id: str):
    """删除实体"""
    try:
        success = data_manager.delete_entity(entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="实体不存在")
        return {"message": "实体删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 关系管理
@app.get("/api/graphs/{graph_id}/relations")
async def get_relations(graph_id: str):
    """获取图谱中的所有关系"""
    try:
        relations = data_manager.get_relations(graph_id)
        return relations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/relations")
async def create_relation(relation_data: RelationCreateRequest):
    """创建新关系"""
    try:
        relation = data_manager.create_relation(
            source_entity_id=relation_data.source_entity_id,
            target_entity_id=relation_data.target_entity_id,
            relation_type=relation_data.relation_type,
            confidence=relation_data.confidence,
            description=relation_data.description,
            graph_id=relation_data.graph_id
        )
        return relation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/relations/{relation_id}")
async def delete_relation(relation_id: str):
    """删除关系"""
    try:
        success = data_manager.delete_relation(relation_id)
        if not success:
            raise HTTPException(status_code=404, detail="关系不存在")
        return {"message": "关系删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 分类管理
@app.get("/api/categories")
async def get_categories():
    """获取所有分类"""
    try:
        categories = data_manager.get_all_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories")
async def create_category(request: CategoryCreateRequest):
    """创建新分类"""
    try:
        category = data_manager.create_category(
            name=request.name,
            description=request.description,
            parent_id=request.parent_id
        )
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/tree")
async def get_category_tree():
    """获取分类树结构"""
    try:
        # 确保根分类存在
        data_manager._ensure_root_category()
        tree = data_manager.get_category_tree()
        return tree
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/{category_id}")
async def get_category(category_id: str):
    """获取指定分类信息"""
    try:
        category = data_manager.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/categories/{category_id}")
async def update_category(category_id: str, request: CategoryUpdateRequest):
    """更新分类信息"""
    try:
        category = data_manager.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description
        )
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: str):
    """删除分类"""
    try:
        success = data_manager.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="分类不存在")
        return {"message": "分类删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/{category_id}/graphs")
async def get_category_graphs(category_id: str):
    """获取分类下的所有图谱"""
    try:
        graphs = data_manager.get_graphs_by_category(category_id)
        return graphs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/{category_id}/visualization")
async def get_category_visualization(category_id: str):
    """获取分类的合并可视化数据"""
    try:
        vis_data = data_manager.get_category_visualization_data(category_id)
        if not vis_data:
            raise HTTPException(status_code=404, detail="分类不存在或无图谱数据")
        return vis_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 图谱可视化数据
@app.get("/api/graphs/{graph_id}/visualization")
async def get_graph_visualization(graph_id: str):
    """获取图谱可视化数据"""
    try:
        visualization_data = data_manager.get_graph_visualization_data(graph_id)
        if not visualization_data:
            raise HTTPException(status_code=404, detail="图谱不存在")
        return visualization_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graphs/{graph_id}/import-data")
async def import_graph_data(graph_id: str):
    """将现有的实体和关系数据导入到指定图谱"""
    try:
        # 检查图谱是否存在
        graph = data_manager.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        
        # 🆕 根据图谱ID获取对应的数据目录
        import os
        from core.utils import load_json
        import config
        from config import get_graph_data_dirs
        
        graph_name = graph.get('name')
        print(f"📊 图谱名称: {graph_name}")
        
        # 获取图谱特定的数据目录 - 使用图谱ID而不是图谱名称
        graph_dirs = get_graph_data_dirs(graph_id)
        
        # 读取消歧后的实体数据
        disambig_file_path = os.path.join(graph_dirs["NER_PRO_OUTPUT_DIR"], "all_entities_disambiguated.json")
        if not os.path.exists(disambig_file_path):
            raise HTTPException(status_code=404, detail=f"未找到图谱 '{graph_id}' 的实体数据文件，请先运行知识图谱构建流程")
        
        entities_raw_data = load_json(disambig_file_path)
        
        # 读取关系数据
        relations_file_path = os.path.join(graph_dirs["RE_OUTPUT_DIR"], "all_relations.json")
        if not os.path.exists(relations_file_path):
            raise HTTPException(status_code=404, detail=f"未找到图谱 '{graph_name}' 的关系数据文件，请先运行知识图谱构建流程")
        
        relations_raw_data = load_json(relations_file_path)
        
        # 转换实体数据格式
        entities_data = []
        for entity in entities_raw_data:
            entities_data.append({
                "name": entity["entity_text"],
                "type": entity["entity_type"],
                "description": entity.get("entity_description", ""),
                "frequency": len(entity.get("chunk_id", [])),
                "source_chunks": entity.get("chunk_id", [])
            })
        
        # 转换关系数据格式
        relations_data = []
        for relation in relations_raw_data:
            relations_data.append({
                "source_entity": relation["head"],
                "target_entity": relation["tail"],
                "relation_type": relation["relation"],
                "confidence": 0.8,
                "description": f"从文档中抽取的关系: {relation['head']} {relation['relation']} {relation['tail']}",
                "source_chunk_id": relation.get("source_chunk_id", "")
            })
        
        # 导入数据
        import_result = data_manager.import_kg_data(
            graph_id=graph_id,
            entities_data=entities_data,
            relations_data=relations_data
        )
        
        return {
            "success": True,
            "message": f"成功导入 {import_result['imported_entities']} 个实体和 {import_result['imported_relations']} 个关系",
            "imported_entities": import_result["imported_entities"],
            "imported_relations": import_result["imported_relations"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG - 导入数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入数据失败: {str(e)}")

# 后台任务函数
async def process_document(
    task_id: str, 
    file_path: str, 
    filename: str, 
    target_graph_id: str
):
    """后台处理文档的异步任务
    
    Args:
        task_id: 任务ID
        file_path: 文档文件路径
        filename: 文档文件名
        target_graph_id: 目标图谱ID
    """
    try:
        # 更新状态：开始处理
        task_status[task_id].status = "processing"
        task_status[task_id].progress = 10
        task_status[task_id].message = "开始文档处理（附加到现有图谱）"
        
        # 调用知识图谱构建器
        result = await kg_builder.process_document(
            file_path=file_path,
            filename=filename,
            target_graph_id=target_graph_id,
            progress_callback=lambda progress, message: update_task_progress(task_id, progress, message)
        )
        
        # 处理完成
        current_time = datetime.now().isoformat()
        task_status[task_id].status = "completed"
        task_status[task_id].progress = 100
        task_status[task_id].message = "文档处理完成（附加到现有图谱）"
        task_status[task_id].result = result
        
        # 同步更新tasks
        if task_id in tasks:
            tasks[task_id].status = TaskStatus.COMPLETED
            tasks[task_id].progress = 100
            tasks[task_id].message = "文档处理完成（附加到现有图谱）"
            tasks[task_id].result = result
            tasks[task_id].updated_at = current_time
        
    except Exception as e:
        # 处理失败
        current_time = datetime.now().isoformat()
        task_status[task_id].status = "failed"
        task_status[task_id].message = f"处理失败: {str(e)}"
        
        # 同步更新tasks
        if task_id in tasks:
            tasks[task_id].status = TaskStatus.FAILED
            tasks[task_id].message = f"处理失败: {str(e)}"
            tasks[task_id].updated_at = current_time
        
        print(f"任务 {task_id} 处理失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")

def update_task_progress(task_id: str, progress: int, message: str):
    """更新任务进度"""
    current_time = datetime.now().isoformat()
    
    # 更新task_status（兼容现有代码）
    if task_id in task_status:
        task_status[task_id].progress = progress
        task_status[task_id].message = message
    
    # 更新tasks
    if task_id in tasks:
        tasks[task_id].progress = progress
        tasks[task_id].message = message
        tasks[task_id].updated_at = current_time
        
        # 根据进度更新状态
        if progress == 0:
            tasks[task_id].status = TaskStatus.PENDING
        elif 0 < progress < 100:
            tasks[task_id].status = TaskStatus.PROCESSING
        elif progress == 100:
            tasks[task_id].status = TaskStatus.COMPLETED

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)