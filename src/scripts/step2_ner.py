import os
import config
from utils import call_llm, save_json, load_text, load_prompt

def run_ner_on_file(input_filepath):
    """对单个文件进行命名实体识别"""
    print(f"正在处理文件: {input_filepath}")
    
    # 1. 加载预处理后的文本
    text_content = load_text(input_filepath)
    if not text_content:
        print("文件内容为空，跳过。")
        return

    # 2. 加载并格式化Prompt
    prompt_template = load_prompt(os.path.join(config.BASE_DIR, "prompts", "ner_prompt.txt"))
    prompt = prompt_template.replace("{{ENTITY_TYPES}}", str(config.ENTITY_TYPES))
    prompt = prompt.replace("{{TEXT_CONTENT}}", text_content)

    # 3. 调用大模型进行NER
    ner_results = call_llm(prompt)

    # 4. 保存结果到文件
    if ner_results:
        filename = os.path.basename(input_filepath)
        output_filepath = os.path.join(config.NER_OUTPUT_DIR, filename.replace('.txt', '.json'))
        save_json(ner_results, output_filepath)
        print(f"NER结果已保存到: {output_filepath}")
    else:
        print("未能从API获取NER结果。")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.NER_OUTPUT_DIR, exist_ok=True)
    
    # 遍历所有处理过的文本文件
    for filename in os.listdir(config.PROCESSED_TEXT_DIR):
        if filename.endswith(".md"):
            input_path = os.path.join(config.PROCESSED_TEXT_DIR, filename)
            run_ner_on_file(input_path)
    
    print("\n所有文件的命名实体识别处理完成！")