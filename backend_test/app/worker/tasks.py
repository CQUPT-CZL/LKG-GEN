# app/worker/tasks.py

from typing import List
from app.crud import crud_sqlite
from app.db.sqlite_session import SessionLocal
from app.db.neo4j_session import get_neo4j_driver

def _run_single_document_extraction(document_id: int, db_session, neo4j_driver):
    """
    这是一个内部辅助函数，负责处理单个文档的完整流程。
    (这就是我们之前写的 run_knowledge_extraction 函数的主体内容)
    """
    try:
        print(f"  - 开始处理子任务：文档 ID: {document_id}")
        crud_sqlite.update_document_status(db_session, doc_id=document_id, status="processing")
        
        document = crud_sqlite.get_document(db_session, doc_id=document_id)
        # ... 文档分块 ...
        # ... 遍历分块，提取实体和关系 ...
        # ... 实体链接与消岐 (这里就可以查到之前文件处理完的结果了) ...
        # ... 图谱入库 ...
        
        crud_sqlite.update_document_status(db_session, doc_id=document_id, status="completed")
        print(f"  - 子任务成功：文档 ID: {document_id} 处理完毕。")
    except Exception as e:
        crud_sqlite.update_document_status(db_session, doc_id=document_id, status="failed")
        print(f"  - 子任务失败：处理文档 ID: {document_id} 时发生错误: {e}")
        # 可以选择在这里抛出异常来中断整个批处理，或者继续处理下一个
        # raise e 

def run_batch_knowledge_extraction(document_ids: List[int]):
    """
    这是新的、在后台运行的【批量】知识提取主函数。
    它会按顺序串行处理列表中的每一个文档。
    """
    print(f"批量后台任务启动：准备处理 {len(document_ids)} 个文档。")
    
    db_session = SessionLocal()
    neo4j_driver_instance = get_neo4j_driver.get_neo4j_driver()

    try:
        # 在一个任务中，按顺序循环处理每个文档
        for doc_id in document_ids:
            _run_single_document_extraction(
                document_id=doc_id,
                db_session=db_session,
                neo4j_driver=neo4j_driver_instance
            )
        
        print(f"批量后台任务成功：所有文档处理完毕。")

    except Exception as e:
        print(f"批量后台任务因某个子任务失败而中断: {e}")
    finally:
        db_session.close()