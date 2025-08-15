# 知识图谱生成系统 - 后端

## 📁 项目结构

```
backend/
├── core/                    # 核心处理模块
│   ├── __init__.py         # 模块初始化
│   ├── config.py           # 配置文件
│   ├── utils.py            # 工具函数
│   ├── chunker.py          # 文本分块处理
│   ├── ner_processor.py    # 命名实体识别
│   ├── relation_extractor.py # 关系抽取
│   └── graph_processor.py  # 图谱处理和实体消歧
├── prompts/                # 提示词模板
│   ├── ner_prompt.txt      # NER提示词
│   ├── re_prompt.txt       # 关系抽取提示词
│   └── disambiguation_prompt.txt # 实体消歧提示词
├── main.py                 # FastAPI主服务
├── pipeline.py             # 知识图谱构建流水线
├── kg_builder.py           # 知识图谱构建器
├── data_manager.py         # 数据管理器
├── kg_wrapper.py           # 图谱包装器
└── requirements.txt        # 依赖包列表
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `core/config.py` 文件，设置你的API密钥：

```python
OPENAI_API_KEY = "your-api-key-here"
OPENAI_API_BASE = "your-api-base-url"
```

### 3. 运行流水线

#### 运行完整流水线
```bash
python pipeline.py --step full
```

#### 运行单个步骤
```bash
# 文本分块
python pipeline.py --step chunking

# 命名实体识别
python pipeline.py --step ner --max-file-workers 2 --max-chunk-workers 4

# 实体消歧
python pipeline.py --step disambiguation

# 关系抽取
python pipeline.py --step relation_extraction
```

### 4. 启动Web服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 处理流程

1. **文本分块** (`chunker.py`)
   - 将长文本分割成小块
   - 便于后续并行处理

2. **命名实体识别** (`ner_processor.py`)
   - 使用大模型识别文本中的实体
   - 支持多线程并行处理
   - 可配置实体类型

3. **实体消歧** (`graph_processor.py`)
   - 合并相似的实体
   - 解决实体歧义问题
   - 生成规范化的实体列表

4. **关系抽取** (`relation_extractor.py`)
   - 识别实体间的关系
   - 生成知识图谱三元组
   - 过滤无效关系

## 🔧 配置说明

### 实体类型配置

在 `core/config.py` 中可以自定义实体类型：

```python
ENTITY_TYPES = [
    "钢铁材料",
    "生产工艺", 
    "性能指标",
    "应用领域",
    # ... 更多类型
]
```

### 关系类型配置

```python
RELATION_TYPES = [
    "具有性能",
    "生产出",
    "应用于",
    # ... 更多关系
]
```

### 并发配置

- `MAX_FILE_WORKERS`: 同时处理的文件数量
- `MAX_CHUNK_WORKERS`: 每个文件内同时处理的chunk数量

## 📁 数据目录结构

```
data/
├── raw_papers/              # 原始论文文件
├── processed_text/          # 预处理后的文本
├── chunk_output/            # 分块结果
├── ner_output/              # NER结果
├── ner_pro_output/          # 消歧后的实体
├── re_output/               # 关系抽取结果
└── graph_triples/           # 最终的图谱三元组
```

## 🔌 API接口

### 主要端点

- `GET /api/health` - 健康检查
- `POST /api/documents/upload` - 上传文档并构建知识图谱
- `GET /api/graphs` - 获取图谱列表
- `GET /api/graphs/{graph_id}` - 获取特定图谱
- `GET /api/system/performance` - 系统性能监控

### 使用示例

```python
import requests

# 上传文档
with open('document.md', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/documents/upload',
        files={'file': f},
        data={'build_mode': 'standalone'}
    )
```

## 🛠️ 开发说明

### 添加新的处理步骤

1. 在 `core/` 目录下创建新的处理模块
2. 在 `core/__init__.py` 中导入新模块
3. 在 `pipeline.py` 中添加新的步骤
4. 更新 `kg_builder.py` 以集成新功能

### 自定义提示词

编辑 `prompts/` 目录下的提示词模板文件，根据你的领域需求调整提示词。

## 🐛 故障排除

### 常见问题

1. **API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证API配额是否充足

2. **内存不足**
   - 减少并发数量
   - 增加系统内存
   - 优化批处理大小

3. **处理速度慢**
   - 调整并发参数
   - 使用更快的模型
   - 优化文本分块策略

## 📝 更新日志

### v2.0.0 (当前版本)
- 🔄 重构项目结构，将src内容整合到backend
- 📦 模块化设计，提高代码可维护性
- 🚀 新增流水线管理器
- 🔧 优化配置管理
- 📊 改进错误处理和日志记录
- 🎯 增强并发处理能力

## 📄 许可证

本项目采用 MIT 许可证。