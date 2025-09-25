# scripts/import_xlsx_triplets.py

import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.db.neo4j_session import get_neo4j_driver
from app.crud import crud_graph
from app.schemas.entity import EntityCreate
from app.schemas.relation import RelationCreate

def parse_xlsx_triplets(file_path: str) -> List[Dict[str, Any]]:
    """
    解析xlsx文件中的三元组数据
    
    Args:
        file_path: xlsx文件路径
        
    Returns:
        三元组数据列表
    """
    print(f"📖 正在读取文件: {file_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 获取缺陷类型（第一行第一列）
        defect_type = df.iloc[0, 0] if not pd.isna(df.iloc[0, 0]) else "未知缺陷"
        print(f"🔍 检测到缺陷类型: {defect_type}")
        
        triplets = []
        
        # 从第3行开始解析（跳过标题行和示例行）
        for index, row in df.iterrows():
            if index < 2:  # 跳过前两行（标题行）
                continue
                
            # 获取主语节点信息
            subject_type = row.iloc[0] if not pd.isna(row.iloc[0]) else None
            subject_name = row.iloc[1] if not pd.isna(row.iloc[1]) else None
            subject_desc = row.iloc[2] if not pd.isna(row.iloc[2]) else None
            
            # 获取宾语节点信息
            object_type = row.iloc[3] if not pd.isna(row.iloc[3]) else None
            object_name = row.iloc[4] if not pd.isna(row.iloc[4]) else None
            object_desc = row.iloc[5] if not pd.isna(row.iloc[5]) else None
            
            # 跳过空行或示例行
            if not subject_name or subject_name == "测试缺陷":
                continue
                
            # 如果主语节点信息完整，创建三元组
            if subject_type and subject_name:
                # 创建主语实体
                subject_entity = {
                    "type": subject_type,
                    "name": subject_name,
                    "description": subject_desc or "",
                    "defect_category": defect_type
                }
                
                # 如果有宾语节点信息，创建关系
                if object_type and object_name:
                    object_entity = {
                        "type": object_type,
                        "name": object_name,
                        "description": object_desc or "",
                        "defect_category": defect_type
                    }
                    
                    # 根据节点类型确定关系类型
                    relation_type = determine_relation_type(subject_type, object_type)
                    
                    triplet = {
                        "subject": subject_entity,
                        "predicate": relation_type,
                        "object": object_entity,
                        "source_file": os.path.basename(file_path)
                    }
                    triplets.append(triplet)
                    
                    print(f"  ✅ 解析三元组: {subject_name} -[{relation_type}]-> {object_name}")
                else:
                    # 只有主语实体的情况，作为独立实体添加
                    triplet = {
                        "subject": subject_entity,
                        "predicate": None,
                        "object": None,
                        "source_file": os.path.basename(file_path)
                    }
                    triplets.append(triplet)
                    print(f"  ✅ 解析实体: {subject_name}")
        
        print(f"📊 共解析出 {len(triplets)} 个三元组/实体")
        return triplets
        
    except Exception as e:
        print(f"❌ 解析文件失败: {e}")
        return []

def determine_relation_type(subject_type: str, object_type: str) -> str:
    """
    根据主语和宾语的类型确定关系类型
    """
    # 定义关系映射规则
    relation_mapping = {
        ("缺陷", "粗轧原因"): "由原因引起",
        ("缺陷", "连铸阶段原因"): "由原因引起", 
        ("粗轧原因", "粗轧原因"): "包含子原因",
        ("氧化铁皮", "粗轧原因"): "由原因引起",
    }
    
    # 查找匹配的关系类型
    key = (subject_type, object_type)
    if key in relation_mapping:
        return relation_mapping[key]
    
    # 默认关系类型
    return "相关联"

def create_or_get_entity(driver, entity_data: Dict[str, Any], graph_id: str) -> str:
    """
    创建或获取实体，如果实体已存在则返回现有实体ID
    """
    entity_name = entity_data["name"]
    entity_type = entity_data["type"]
    
    # 检查实体是否已存在
    with driver.session() as session:
        query = """
        MATCH (e:Entity {name: $name, entity_type: $entity_type, graph_id: $graph_id})
        RETURN e.id as id
        """
        result = session.run(query, name=entity_name, entity_type=entity_type, graph_id=graph_id)
        record = result.single()
        
        if record:
            print(f"  🔄 实体已存在: {entity_name}")
            return record["id"]
    
    # 创建新实体
    entity_create = EntityCreate(
        name=entity_name,
        entity_type=entity_type,
        description=entity_data.get("description", ""),
        graph_id=graph_id,
        frequency=1,
        chunk_ids=[],
        document_ids=[]
    )
    
    try:
        created_entity = crud_graph.create_entity(driver, entity_create)
        print(f"  ✅ 创建实体: {entity_name} ({entity_type})")
        return created_entity["id"]
    except Exception as e:
        print(f"  ❌ 创建实体失败: {entity_name} - {e}")
        return None

def import_triplets_to_neo4j_with_stats(driver, triplets: List[Dict[str, Any]], graph_id: str, document_id: int = None) -> Dict[str, Any]:
    """
    导入三元组到Neo4j并返回统计信息
    """
    print(f"🚀 开始导入 {len(triplets)} 个三元组到图数据库...")
    
    entity_cache = {}  # 缓存已创建的实体ID
    created_entities = 0
    created_relations = 0
    cached_entities = 0
    errors = []
    
    for i, triplet in enumerate(triplets, 1):
        print(f"📝 处理第 {i}/{len(triplets)} 个三元组...")
        
        try:
            # 处理主语实体
            subject_data = triplet["subject"]
            subject_key = f"{subject_data['name']}_{subject_data['type']}"
            
            if subject_key not in entity_cache:
                subject_id = create_or_get_entity(driver, subject_data, graph_id)
                if subject_id:
                    entity_cache[subject_key] = subject_id
                    created_entities += 1
            else:
                subject_id = entity_cache[subject_key]
                cached_entities += 1
            
            # 如果有宾语实体，处理宾语和关系
            if triplet["object"] and triplet["predicate"]:
                object_data = triplet["object"]
                object_key = f"{object_data['name']}_{object_data['type']}"
                
                if object_key not in entity_cache:
                    object_id = create_or_get_entity(driver, object_data, graph_id)
                    if object_id:
                        entity_cache[object_key] = object_id
                        created_entities += 1
                else:
                    object_id = entity_cache[object_key]
                    cached_entities += 1
                
                # 创建关系
                if subject_id and object_id:
                    relation_create = RelationCreate(
                        source_entity_id=subject_id,
                        target_entity_id=object_id,
                        relation_type=triplet["predicate"],
                        description=f"来源文件: {triplet['source_file']}",
                        graph_id=graph_id,
                        confidence=1.0
                    )
                    
                    try:
                        created_relation = crud_graph.create_relation(driver, relation_create)
                        if created_relation:
                            created_relations += 1
                            print(f"  ✅ 创建关系: {subject_data['name']} -[{triplet['predicate']}]-> {object_data['name']}")
                    except Exception as e:
                        error_msg = f"创建关系失败: {e}"
                        print(f"  ❌ {error_msg}")
                        errors.append(error_msg)
                        
        except Exception as e:
            error_msg = f"处理三元组失败: {e}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)
            continue
    
    print(f"🎉 导入完成！")
    print(f"📊 统计信息:")
    print(f"  - 创建实体: {created_entities} 个")
    print(f"  - 创建关系: {created_relations} 个")
    print(f"  - 缓存实体: {cached_entities} 个")
    
    return {
        "created_entities": created_entities,
        "created_relations": created_relations,
        "cached_entities": cached_entities,
        "errors": errors
    }




def find_xlsx_files(directory: str) -> List[str]:
    """
    递归查找指定目录及其子目录中的所有xlsx文件
    
    Args:
        directory: 要搜索的根目录路径
        
    Returns:
        List[str]: 找到的所有xlsx文件路径列表
    """
    xlsx_files = []
    directory_path = Path(directory)
    
    if directory_path.is_dir():
        # 递归查找所有xlsx文件（包括子目录）
        xlsx_files.extend(directory_path.rglob("*.xlsx"))
        xlsx_files.extend(directory_path.rglob("*.xls"))
        
        print(f"🔍 递归搜索目录: {directory}")
        if xlsx_files:
            print(f"📂 在以下位置找到Excel文件:")
            for file in xlsx_files:
                relative_path = file.relative_to(directory_path)
                print(f"   📄 {relative_path}")
    
    return [str(f) for f in xlsx_files]


def process_xlsx_files(directory: str, graph_id: str, file_id: str = None) -> Dict[str, Any]:
    """
    处理目录下的所有xlsx文件，导入三元组到Neo4j
    
    Args:
        directory: 包含xlsx文件的目录路径
        graph_id: 图谱ID
        file_id: 文件ID（已废弃，保留参数兼容性）
    
    Returns:
        Dict: 包含处理统计信息的字典
    """
    xlsx_files = find_xlsx_files(directory)
    
    if not xlsx_files:
        print(f"❌ 在目录 {directory} 及其子目录中未找到xlsx文件")
        return {
            "total_files": 0,
            "processed_files": 0,
            "total_triplets": 0,
            "created_entities": 0,
            "created_relations": 0,
            "cached_entities": 0,
            "errors": ["未找到xlsx文件"]
        }
    
    print(f"📁 总共找到 {len(xlsx_files)} 个xlsx文件")
    
    # 获取Neo4j驱动
    driver = get_neo4j_driver()
    
    total_stats = {
        "total_files": len(xlsx_files),
        "processed_files": 0,
        "total_triplets": 0,
        "created_entities": 0,
        "created_relations": 0,
        "cached_entities": 0,
        "errors": []
    }
    
    try:
        for xlsx_file in xlsx_files:
            print(f"\n📊 处理文件: {xlsx_file}")
            
            # 处理三元组
            try:
                filename = Path(xlsx_file).name
                triplets = parse_xlsx_triplets(xlsx_file)
                if not triplets:
                    print(f"⚠️ 文件 {xlsx_file} 中未找到有效的三元组")
                    continue
                
                print(f"📋 解析到 {len(triplets)} 个三元组")
                total_stats["total_triplets"] += len(triplets)
                
                # 导入三元组到图数据库（不需要document_id）
                stats = import_triplets_to_neo4j_with_stats(driver, triplets, graph_id)
                
                # 累计统计
                total_stats["created_entities"] += stats["created_entities"]
                total_stats["created_relations"] += stats["created_relations"]
                total_stats["cached_entities"] += stats["cached_entities"]
                total_stats["errors"].extend(stats["errors"])
                total_stats["processed_files"] += 1
                
                print(f"✅ 文件 {filename} 处理完成")
                
            except Exception as e:
                error_msg = f"处理文件 {xlsx_file} 时出错: {e}"
                print(f"❌ {error_msg}")
                total_stats["errors"].append(error_msg)
    
    finally:
        driver.close()
    
    return total_stats


def main(directory: str = None, graph_id: str = "651fa83d-2841-47c3-b4cf-7394a546f28e", file_id: str = "999"):
    """
    主函数：处理指定目录下的所有xlsx文件并导入到图数据库
    """
    print("🚀 开始Excel三元组导入程序")
    print(f"📂 将数据导入到图谱ID: {graph_id}")
    
    if not directory:
        print("❌ 请提供目录路径")
        return
    
    # 处理所有xlsx文件
    stats = process_xlsx_files(directory, graph_id, file_id)
    
    # 输出最终统计
    print(f"\n{'='*60}")
    print(f"📊 最终统计结果")
    print(f"{'='*60}")
    print(f"📁 总文件数: {stats['total_files']}")
    print(f"✅ 处理成功: {stats['processed_files']}")
    print(f"📋 总三元组: {stats['total_triplets']}")
    print(f"🏷️ 创建实体: {stats['created_entities']}")
    print(f"🔗 创建关系: {stats['created_relations']}")
    print(f"💾 缓存实体: {stats['cached_entities']}")
    
    if stats['errors']:
        print(f"❌ 错误数量: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"   - {error}")
    
    if stats['processed_files'] > 0:
        print("🎉 程序执行成功！")
    else:
        print("❌ 程序执行失败，没有成功处理任何文件")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory_path = "/Users/cuiziliang/Documents/赛迪信息/已有知识整理-20250912"
        graph_id = sys.argv[2] if len(sys.argv) > 2 else "651fa83d-2841-47c3-b4cf-7394a546f28e"
        file_id = sys.argv[3] if len(sys.argv) > 3 else "999"
        main(directory_path, graph_id, file_id)
    else:
        print("使用方法: python import_xlsx_triplets.py <目录路径> [图谱ID] [文件ID]")
        print("示例: python import_xlsx_triplets.py /path/to/xlsx/files c2ffc1e2-3acd-4e68-9e45-911b9ad94d30 999")