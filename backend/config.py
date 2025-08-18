# config.py
import os

# --- API Configuration ---
# 替换成您自己的API Key和Base URL
OPENAI_API_KEY = "sk-de6a75acf0b14799ba7ffee5e9544ad2"
OPENAI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1" # 或者其他代理地址

# --- File Paths ---
# 使用os.path.join确保跨平台兼容性

# 获取backend目录的绝对路径
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)  # 项目根目录
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPTS_DIR = os.path.join(BACKEND_DIR, "prompts")

RAW_PAPERS_DIR = os.path.join(DATA_DIR, "raw_papers")
PROCESSED_TEXT_DIR = os.path.join(DATA_DIR, "processed_text")
CHUNK_OUTPUT_DIR = os.path.join(DATA_DIR, "chunk_output")
NER_PRO_OUTPUT_DIR = os.path.join(DATA_DIR, "ner_pro_output")
NER_OUTPUT_DIR = os.path.join(DATA_DIR, "ner_output")
RE_OUTPUT_DIR = os.path.join(DATA_DIR, "re_output")
GRAPH_TRIPLES_DIR = os.path.join(DATA_DIR, "graph_triples")

# --- Prompt Paths ---
NER_PROMPT_PATH = os.path.join(PROMPTS_DIR, "ner_prompt.txt")
RE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "re_prompt.txt")
DISAMBIGUATION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "disambiguation_prompt.txt")
ENTITY_VALIDATION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "entity_validation_prompt.txt")

# --- KG Schema Definition ---
# 在这里定义你的实体和关系类型，方便在代码中引用
ENTITY_TYPES = [
    "钢铁材料",      # 包括各类钢材、合金等
    "生产工艺",      # 如热处理、轧制等工艺流程
    "性能指标",      # 如强度、硬度、韧性等
    "应用领域",      # 如建筑、汽车、船舶等
    "设备",         # 生产设备和检测设备
    "缺陷",         # 产品缺陷和质量问题
    "化学成分",      # 材料的化学组成
    "热处理工艺",    # 具体的热处理方法
    "机械性能",      # 具体的机械性能指标
    "表面处理",      # 表面处理工艺
    "检测方法"       # 质量检测方法
]

RELATION_TYPES = [
    "具有性能",      # 材料与性能的关系
    "生产出",       # 工艺与产品的关系
    "应用于",       # 材料与应用领域的关系
    "使用设备",      # 工艺与设备的关系
    "导致缺陷",      # 工艺与缺陷的关系
    "包含成分",      # 材料与化学成分的关系
    "需要检测",      # 产品与检测方法的关系
    "改善性能",      # 工艺与性能的关系
    "防止缺陷",      # 工艺与缺陷的预防关系
    "互相影响"       # 不同性能指标间的关系
]