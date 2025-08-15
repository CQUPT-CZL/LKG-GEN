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
data_manager = DataManager()
kg_builder = KnowledgeGraphBuilder()

# 数据模型定义
class GraphCreateRequest(BaseModel):
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
    build_mode: str = "standalone"  # standalone or append
    target_graph_id: Optional[str] = None
    description: Optional[str] = ""
    result: Optional[Dict[str, Any]] = None

class CreateTaskRequest(BaseModel):
    name: str
    type: TaskType = TaskType.KNOWLEDGE_GRAPH_BUILD
    build_mode: str = "standalone"
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
    """创建新的知识图谱"""
    try:
        name = request.get("name")
        description = request.get("description", "")
        domain = request.get("domain")
        
        if not name:
            raise HTTPException(status_code=400, detail="图谱名称不能为空")
        
        graph_data = data_manager.create_graph(name, description, domain)
        return graph_data
    except Exception as e:
        print(f"创建图谱失败: {e}")
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
    build_mode: str = Form("standalone"),  # standalone 或 append
    target_graph_id: Optional[str] = Form(None),  # 当build_mode为append时指定目标图谱ID
    graph_name: Optional[str] = Form(None),  # 图谱名称（独立构建模式）
    graph_description: Optional[str] = Form(None),  # 图谱描述（独立构建模式）
    domain: Optional[str] = Form(None)  # 领域信息（独立构建模式）
):
    """上传文档并开始知识图谱构建
    
    Args:
        file: 上传的文档文件
        build_mode: 构建模式，'standalone'(独立构建) 或 'append'(附加到现有图谱)
        target_graph_id: 当build_mode为'append'时，指定要附加到的图谱ID
        graph_name: 图谱名称（独立构建模式时使用）
        graph_description: 图谱描述（独立构建模式时使用）
        domain: 领域信息（独立构建模式时使用）
    """
    try:
        # 验证构建模式
        if build_mode not in ["standalone", "append"]:
            raise HTTPException(status_code=400, detail="构建模式必须是 'standalone' 或 'append'")
        
        # 如果是附加模式，验证目标图谱是否存在
        if build_mode == "append":
            if not target_graph_id:
                raise HTTPException(status_code=400, detail="附加模式下必须指定目标图谱ID")
            # 验证图谱是否存在
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
            message=f"文档上传成功，等待处理 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})",
            created_at=current_time,
            updated_at=current_time,
            files=[file.filename],
            build_mode=build_mode,
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
            message=f"文档上传成功，等待处理 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})"
        )
        
        # 添加后台任务
        background_tasks.add_task(
            process_document, 
            task_id, 
            str(file_path), 
            file.filename, 
            build_mode, 
            target_graph_id,
            graph_name,
            graph_description,
            domain
        )
        
        return {
            "task_id": task_id,
            "message": f"文档上传成功，开始处理 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})",
            "filename": file.filename,
            "build_mode": build_mode,
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
            build_mode=task_data.build_mode,
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

# 图谱可视化数据
@app.get("/api/graphs/{graph_id}/visualization")
async def get_graph_visualization(graph_id: str):
    """获取图谱可视化数据"""
    try:
        vis_data = data_manager.get_graph_visualization_data(graph_id)
        if not vis_data:
            raise HTTPException(status_code=404, detail="图谱不存在")
        return vis_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 后台任务函数
async def process_document(
    task_id: str, 
    file_path: str, 
    filename: str, 
    build_mode: str = "standalone", 
    target_graph_id: Optional[str] = None,
    graph_name: Optional[str] = None,
    graph_description: Optional[str] = None,
    domain: Optional[str] = None
):
    """后台处理文档的异步任务
    
    Args:
        task_id: 任务ID
        file_path: 文档文件路径
        filename: 文档文件名
        build_mode: 构建模式，'standalone' 或 'append'
        target_graph_id: 当build_mode为'append'时的目标图谱ID
        graph_name: 图谱名称（独立构建模式时使用）
        graph_description: 图谱描述（独立构建模式时使用）
        domain: 领域信息（独立构建模式时使用）
    """
    try:
        # 更新状态：开始处理
        task_status[task_id].status = "processing"
        task_status[task_id].progress = 10
        task_status[task_id].message = f"开始文档处理 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})"
        
        # 调用知识图谱构建器
        result = await kg_builder.process_document(
            file_path=file_path,
            filename=filename,
            build_mode=build_mode,
            target_graph_id=target_graph_id,
            graph_name=graph_name,
            graph_description=graph_description,
            domain=domain,
            progress_callback=lambda progress, message: update_task_progress(task_id, progress, message)
        )
        
        # 处理完成
        current_time = datetime.now().isoformat()
        task_status[task_id].status = "completed"
        task_status[task_id].progress = 100
        task_status[task_id].message = f"文档处理完成 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})"
        task_status[task_id].result = result
        
        # 同步更新tasks
        if task_id in tasks:
            tasks[task_id].status = TaskStatus.COMPLETED
            tasks[task_id].progress = 100
            tasks[task_id].message = f"文档处理完成 (模式: {'独立构建' if build_mode == 'standalone' else '附加到现有图谱'})"
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