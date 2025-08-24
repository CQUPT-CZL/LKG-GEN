# Knowledge Graph Platform API 接口文档

## 基本信息

- **项目名称**: Knowledge Graph Platform
- **API版本**: v1
- **基础URL**: `http://localhost:8000/api/v1`
- **文档生成时间**: 2024年

## 目录

1. [认证方式](#认证方式)
2. [通用响应格式](#通用响应格式)
3. [文档管理接口](#文档管理接口)
4. [知识图谱接口](#知识图谱接口)
5. [分类管理接口](#分类管理接口)
6. [数据模型](#数据模型)
7. [错误码说明](#错误码说明)

## 认证方式

目前API暂未实现认证机制，所有接口均可直接访问。

## 通用响应格式

### 成功响应
```json
{
  "data": {},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "detail": "错误描述信息"
}
```

## 文档管理接口

### 1. 获取文档列表

**接口地址**: `GET /documents/`

**请求参数**:
- `skip` (query, int, 可选): 跳过的记录数，默认为0
- `limit` (query, int, 可选): 返回的记录数，默认为100

**响应示例**:
```json
[
  {
    "id": 1,
    "filename": "钢铁行业报告.pdf",
    "status": "COMPLETED",
    "uploaded_at": "2024-01-01T10:00:00",
    "resource_type": "PDF"
  }
]
```

### 2. 获取单个文档详情

**接口地址**: `GET /documents/{document_id}`

**路径参数**:
- `document_id` (int, 必需): 文档ID

**响应示例**:
```json
{
  "id": 1,
  "filename": "钢铁行业报告.pdf",
  "status": "COMPLETED",
  "uploaded_at": "2024-01-01T10:00:00",
  "resource_type": "PDF"
}
```

### 3. 删除文档

**接口地址**: `DELETE /documents/{document_id}`

**路径参数**:
- `document_id` (int, 必需): 文档ID

**响应示例**:
```json
{
  "message": "文档删除成功",
  "details": {
    "deleted_entities": ["entity1", "entity2"],
    "updated_entities": ["entity3", "entity4"],
    "neo4j_document_deleted": true,
    "sqlite_document_deleted": true
  }
}
```

### 4. 批量创建资源

**接口地址**: `POST /documents/resources`

**请求体**:
```json
{
  "parent_id": "graph_uuid_or_category_uuid",
  "graph_id": "graph_uuid",
  "resources": [
    {
      "filename": "文档1.pdf",
      "content": "文档内容...",
      "type": "PDF"
    },
    {
      "filename": "文档2.txt",
      "content": "文档内容...",
      "type": "TEXT"
    }
  ]
}
```

**响应示例**:
```json
{
  "success_count": 2,
  "failed_count": 0,
  "total_count": 2,
  "created_resources": [
    {
      "id": 1,
      "filename": "文档1.pdf",
      "status": "PROCESSING",
      "uploaded_at": "2024-01-01T10:00:00",
      "resource_type": "PDF"
    }
  ],
  "failed_resources": []
}
```

### 5. 获取文档子图谱

**接口地址**: `GET /documents/{document_id}/subgraph`

**路径参数**:
- `document_id` (int, 必需): 文档ID

**响应示例**:
```json
{
  "entities": [
    {
      "id": "entity_uuid",
      "name": "螺纹钢",
      "type": "钢铁产品",
      "properties": {
        "description": "建筑用钢材"
      }
    }
  ],
  "relationships": [
    {
      "id": "rel_uuid",
      "type": "生产",
      "start_node_id": "entity1_uuid",
      "end_node_id": "entity2_uuid",
      "properties": {
        "confidence": 0.95
      }
    }
  ]
}
```

## 知识图谱接口

### 1. 创建知识图谱

**接口地址**: `POST /graphs/`

**请求体**:
```json
{
  "name": "钢铁行业知识图谱",
  "description": "包含钢铁行业相关知识的图谱"
}
```

**响应示例**:
```json
{
  "id": "graph_uuid",
  "name": "钢铁行业知识图谱",
  "description": "包含钢铁行业相关知识的图谱"
}
```

### 2. 获取图谱列表

**接口地址**: `GET /graphs/`

**请求参数**:
- `skip` (query, int, 可选): 跳过的记录数，默认为0
- `limit` (query, int, 可选): 返回的记录数，默认为100

**响应示例**:
```json
[
  {
    "id": "graph_uuid",
    "name": "钢铁行业知识图谱",
    "description": "包含钢铁行业相关知识的图谱"
  }
]
```

### 3. 获取单个图谱详情

**接口地址**: `GET /graphs/{graph_id}`

**路径参数**:
- `graph_id` (string, 必需): 图谱ID

**响应示例**:
```json
{
  "id": "graph_uuid",
  "name": "钢铁行业知识图谱",
  "description": "包含钢铁行业相关知识的图谱"
}
```

### 4. 删除图谱

**接口地址**: `DELETE /graphs/{graph_id}`

**路径参数**:
- `graph_id` (string, 必需): 图谱ID

**响应示例**:
```json
{
  "message": "图谱删除成功"
}
```

## 分类管理接口

### 1. 创建分类

**接口地址**: `POST /categories/`

**请求体**:
```json
{
  "name": "生产工艺",
  "parent_id": "graph_uuid_or_category_uuid"
}
```

**响应示例**:
```json
{
  "id": "category_uuid",
  "name": "生产工艺",
  "parent_id": "graph_uuid",
  "graph_id": "graph_uuid"
}
```

### 2. 获取分类详情

**接口地址**: `GET /categories/{category_id}`

**路径参数**:
- `category_id` (string, 必需): 分类ID

**响应示例**:
```json
{
  "id": "category_uuid",
  "name": "生产工艺",
  "parent_id": "graph_uuid",
  "graph_id": "graph_uuid"
}
```

### 3. 删除分类

**接口地址**: `DELETE /categories/{category_id}`

**路径参数**:
- `category_id` (string, 必需): 分类ID

**响应示例**:
```json
{
  "message": "分类删除成功"
}
```

### 4. 获取分类子图谱

**接口地址**: `GET /categories/{category_id}/subgraph`

**路径参数**:
- `category_id` (string, 必需): 分类ID

**响应示例**:
```json
{
  "entities": [
    {
      "id": "entity_uuid",
      "name": "高炉炼铁",
      "type": "生产工艺",
      "properties": {
        "temperature": "1500°C"
      }
    }
  ],
  "relationships": [
    {
      "id": "rel_uuid",
      "type": "使用",
      "start_node_id": "process_uuid",
      "end_node_id": "material_uuid",
      "properties": {
        "quantity": "大量"
      }
    }
  ]
}
```

## 数据模型

### SourceResource (文档资源)
```json
{
  "id": "integer",
  "filename": "string",
  "status": "PENDING|PROCESSING|COMPLETED|FAILED",
  "uploaded_at": "datetime",
  "resource_type": "string"
}
```

### Graph (知识图谱)
```json
{
  "id": "string (UUID)",
  "name": "string",
  "description": "string (可选)"
}
```

### Category (分类)
```json
{
  "id": "string (UUID)",
  "name": "string",
  "parent_id": "string (UUID)",
  "graph_id": "string (UUID)"
}
```

### Entity (实体)
```json
{
  "id": "string (UUID)",
  "name": "string",
  "type": "string (可选)",
  "properties": "object (可选)"
}
```

### Relationship (关系)
```json
{
  "id": "string (UUID)",
  "type": "string",
  "start_node_id": "string (UUID)",
  "end_node_id": "string (UUID)",
  "properties": "object (可选)"
}
```

### Subgraph (子图谱)
```json
{
  "entities": "Entity[]",
  "relationships": "Relationship[]"
}
```

## 预定义实体类型

系统预定义了以下实体类型，主要面向钢铁行业：

- **钢铁产品**: 螺纹钢、热轧板、冷轧板等
- **生产工艺**: 高炉炼铁、转炉炼钢、连铸等
- **原材料**: 铁矿石、焦炭、石灰石等
- **设备装置**: 高炉、转炉、轧机等
- **质量指标**: 强度、硬度、韧性等
- **技术标准**: 国标、行标、企标等
- **钢铁企业**: 宝钢、河钢、沙钢等
- **生产基地**: 钢铁厂、生产线等
- **市场应用**: 建筑、汽车、造船等
- **环保技术**: 脱硫、脱硝、除尘等
- **人员岗位**: 炼钢工、轧钢工、质检员等
- **地理位置**: 城市、省份、工业园区等

## 预定义关系类型

系统预定义了以下关系类型：

- **生产**: 企业生产钢铁产品
- **使用**: 生产工艺使用原材料
- **应用于**: 钢铁产品应用于市场
- **检测**: 质量指标检测产品
- **位于**: 企业位于地理位置
- **操作**: 人员操作设备
- **符合**: 产品符合技术标准
- **包含**: 生产基地包含设备
- **采用**: 企业采用环保技术
- **隶属于**: 人员隶属于企业
- **供应**: 供应商供应原材料
- **加工**: 设备加工原材料

## 错误码说明

| HTTP状态码 | 错误类型 | 说明 |
|-----------|---------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

## 使用示例

### 创建知识图谱并添加文档

1. **创建知识图谱**
```bash
curl -X POST "http://localhost:8000/api/v1/graphs/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "钢铁行业知识图谱",
    "description": "钢铁行业相关知识"
  }'
```

2. **批量添加文档**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/resources" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "your_graph_uuid",
    "graph_id": "your_graph_uuid",
    "resources": [
      {
        "filename": "钢铁生产工艺.pdf",
        "content": "文档内容...",
        "type": "PDF"
      }
    ]
  }'
```

3. **查看文档子图谱**
```bash
curl "http://localhost:8000/api/v1/documents/1/subgraph"
```

## 注意事项

1. **异步处理**: 文档上传后会进行异步的知识抽取处理，可通过文档状态字段查看处理进度
2. **UUID格式**: Neo4j中的ID均为UUID格式，SQLite中的ID为自增整数
3. **级联删除**: 删除文档时会自动清理相关的实体和关系
4. **实体合并**: 系统会自动合并相同名称的实体，并累计其出现频次
5. **关系去重**: 相同类型的关系不会重复创建

## 技术栈

- **Web框架**: FastAPI
- **关系数据库**: SQLite
- **图数据库**: Neo4j
- **异步任务**: BackgroundTasks
- **数据验证**: Pydantic

---

*本文档基于当前API实现自动生成，如有疑问请联系开发团队。*