# config.py
import os

# --- API Configuration ---
# 替换成您自己的API Key和Base URL
OPENAI_API_KEY = "sk-de6a75acf0b14799ba7ffee5e9544ad2"
OPENAI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1" # 或者其他代理地址

# --- File Paths ---
# 使用os.path.join确保跨平台兼容性

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_PAPERS_DIR = os.path.join(DATA_DIR, "raw_papers")
PROCESSED_TEXT_DIR = os.path.join(DATA_DIR, "processed_text")
NER_OUTPUT_DIR = os.path.join(DATA_DIR, "ner_output")
RE_OUTPUT_DIR = os.path.join(DATA_DIR, "03_re_output")
GRAPH_TRIPLES_DIR = os.path.join(DATA_DIR, "04_graph_triples")

# --- KG Schema Definition ---
# 在这里定义你的实体和关系类型，方便在代码中引用
ENTITY_TYPES = ["钢铁材料", "生产工艺", "性能指标", "应用领域", "设备", "缺陷"]
RELATION_TYPES = ["具有性能", "生产出", "应用于", "使用设备", "导致缺陷"]