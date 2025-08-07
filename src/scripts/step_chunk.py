import os
import config
from utils import save_json, load_text

def run_chunk_on_file(input_filepath):
    """对单个文件进行文本分块"""
    print(f"正在处理文件: {input_filepath}")
    
    # 1. 加载预处理后的文本
    text_content = load_text(input_filepath)
    if not text_content:
        print("文件内容为空，跳过。")
        return

    # 2. 进行简单分块（例如，按段落分块）
    chunks = text_content.split('\n') 
    chunks = {str(i): chunk.strip() for i, chunk in enumerate(chunks, 1) if chunk.strip()}

    # 3. 保存分块结果
    if chunks:
        filename = os.path.basename(input_filepath)
        output_filepath = os.path.join(config.CHUNK_OUTPUT_DIR, filename.replace('.md', '.json'))
        save_json(chunks, output_filepath)
        print(f"分块结果已保存到: {output_filepath}")
    else:
        print("未能生成分块。")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.CHUNK_OUTPUT_DIR, exist_ok=True)
    
    # 遍历所有处理过的文本文件
    for filename in os.listdir(config.PROCESSED_TEXT_DIR):
        if filename.endswith(".md"):
            input_path = os.path.join(config.PROCESSED_TEXT_DIR, filename)
            run_chunk_on_file(input_path)
    
    print("\n所有文件的文本分块处理完成！")