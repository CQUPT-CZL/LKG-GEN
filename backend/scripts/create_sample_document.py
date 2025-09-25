# scripts/create_sample_document.py

import sys
from pathlib import Path
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.deps import get_db
from app.crud import crud_sqlite

def create_sample_document_999():
    """
    创建ID为999的示例文档记录
    """
    # 示例文档内容
    sample_content = """
# 999号技术文档 - 知识图谱构建指南

## 概述
本文档介绍了基于Excel表格的知识图谱构建方法，包含实体识别、关系抽取和图数据库存储等关键技术。

## 核心概念

### 实体类型
- **设备类实体**: 包括各种工业设备、机械装置等
- **材料类实体**: 涵盖金属材料、复合材料、化学物质等  
- **工艺类实体**: 描述生产工艺、处理方法、技术流程等
- **属性类实体**: 表示物理属性、化学属性、性能指标等

### 关系类型
- **组成关系**: 描述实体间的组成或包含关系
- **属性关系**: 表示实体具有某种属性或特征
- **工艺关系**: 说明工艺流程中的先后顺序或依赖关系
- **影响关系**: 描述一个实体对另一个实体的影响作用

## 技术实现

### 数据解析
系统能够自动解析Excel表格中的三元组数据，识别主语、谓语、宾语结构，并进行智能分类。

### 实体管理
- 自动去重：避免创建重复的实体节点
- 类型推断：根据实体名称和上下文推断实体类型
- 缓存机制：提高批量导入的处理效率

### 关系建模
- 语义映射：将自然语言描述映射为标准化的关系类型
- 置信度评估：为每个关系分配置信度分数
- 双向关系：支持创建双向的语义关系

## 应用场景
本系统适用于工业知识管理、技术文档整理、专家知识提取等多种场景，能够有效提升知识组织和检索的效率。

## 技术优势
- **高效处理**: 支持批量导入大规模数据
- **智能识别**: 自动识别实体类型和关系类型
- **灵活扩展**: 支持自定义实体类型和关系类型
- **数据溯源**: 完整记录数据来源和处理过程
    """
    
    # 获取数据库连接
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 创建文档记录
        document = crud_sqlite.create_source_document(
            db=db,
            filename="999_知识图谱构建技术文档.md",
            content=sample_content,
            resource_type="技术文档"
        )
        
        print(f"✅ 成功创建示例文档记录")
        print(f"📄 文档ID: {document.id}")
        print(f"📝 文件名: {document.filename}")
        print(f"📊 文档类型: {document.resource_type}")
        print(f"📅 创建时间: {document.uploaded_at}")
        print(f"📈 状态: {document.status}")
        print(f"📏 内容长度: {len(document.content)} 字符")
        
        return document.id
        
    except Exception as e:
        print(f"❌ 创建文档记录失败: {e}")
        return None
    finally:
        db.close()

def main():
    """
    主函数
    """
    print("🚀 开始创建999号示例文档")
    print("="*60)
    
    document_id = create_sample_document_999()
    
    if document_id:
        print(f"\n🎉 文档创建成功！文档ID: {document_id}")
        print("💡 该文档已保存到SQLite数据库中，可以通过API进行查询和管理")
    else:
        print("\n❌ 文档创建失败")

if __name__ == "__main__":
    main()