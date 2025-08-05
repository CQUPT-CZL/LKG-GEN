import os
import config
from utils import call_llm, save_json, load_prompt, load_json
import tqdm

def run_ner_on_file(chunk_filepath):
    """对单个分块文件进行命名实体识别"""
    print(f"正在处理分块文件: {chunk_filepath}")
    
    # 1. 加载分块数据
    chunks = load_json(chunk_filepath)
    if not chunks:
        print("分块数据为空，跳过。")
        return

    ner_results = []
    prompt_template = load_prompt(os.path.join(config.BASE_DIR, "prompts", "ner_prompt.txt"))

    # 获取文件名前缀（去掉.json扩展名）
    file_prefix = os.path.basename(chunk_filepath).replace('.json', '')
    
    # 2. 对每个chunk进行NER
    for chunk_id, chunk in tqdm.tqdm(chunks.items()):
        prompt = prompt_template.replace("{{ENTITY_TYPES}}", str(config.ENTITY_TYPES))
        prompt = prompt.replace("{{TEXT_CONTENT}}", chunk)
        chunk_ner = call_llm(prompt, model_name="qwen-max")
        if chunk_ner and isinstance(chunk_ner, list):
            for entity in chunk_ner:
                # 为chunk_id添加文件名前缀，格式：文件名_chunk_id
                entity['chunk_id'] = [f"{file_prefix}_{chunk_id}"]
                ner_results.append(entity)


    # 3. 保存所有chunks的NER结果
    if ner_results:
        filename = os.path.basename(chunk_filepath)
        output_filepath = os.path.join(config.NER_OUTPUT_DIR, filename)
        save_json(ner_results, output_filepath)
        print(f"NER结果已保存到: {output_filepath}")
    else:
        print("未能从API获取NER结果。")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.NER_OUTPUT_DIR, exist_ok=True)

    # 遍历所有分块文件
    for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
        if filename.endswith(".json"):
            chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
            run_ner_on_file(chunk_path)
    
    print("\n所有分块文件的命名实体识别处理完成！")