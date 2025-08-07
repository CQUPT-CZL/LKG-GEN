import os
import config
from utils import call_llm, save_json, load_prompt, load_json
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import partial

# 线程锁，用于保护共享资源
result_lock = threading.Lock()

def process_single_chunk(chunk_id, chunk_text, prompt_template, file_prefix):
    """处理单个chunk的NER任务"""
    try:
        prompt = prompt_template.replace("{{ENTITY_TYPES}}", str(config.ENTITY_TYPES))
        prompt = prompt.replace("{{TEXT_CONTENT}}", chunk_text)
        chunk_ner = call_llm(prompt, model_name="qwen-max")
        
        if chunk_ner and isinstance(chunk_ner, list):
            for entity in chunk_ner:
                # 为chunk_id添加文件名前缀，格式：文件名_chunk_id
                entity['chunk_id'] = [f"{file_prefix}_{chunk_id}"]
            return chunk_ner
        return []
    except Exception as e:
        print(f"处理chunk {chunk_id} 时出错: {e}")
        return []

def run_ner_on_file(chunk_filepath, max_workers=4):
    """对单个分块文件进行命名实体识别（多线程版本）"""
    print(f"🔄 正在处理分块文件: {chunk_filepath}")
    
    # 1. 加载分块数据
    chunks = load_json(chunk_filepath)
    if not chunks:
        print("⚠️ 分块数据为空，跳过。")
        return

    ner_results = []
    prompt_template = load_prompt(os.path.join(config.BASE_DIR, "prompts", "ner_prompt.txt"))

    # 获取文件名前缀（去掉.json扩展名）
    file_prefix = os.path.basename(chunk_filepath).replace('.json', '')
    
    # 2. 使用多线程对每个chunk进行NER
    print(f"📊 开始处理 {len(chunks)} 个chunks，使用 {max_workers} 个线程")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_chunk = {
            executor.submit(process_single_chunk, chunk_id, chunk_text, prompt_template, file_prefix): chunk_id
            for chunk_id, chunk_text in chunks.items()
        }
        
        # 使用tqdm显示进度
        with tqdm.tqdm(total=len(chunks), desc="处理chunks") as pbar:
            for future in as_completed(future_to_chunk):
                chunk_id = future_to_chunk[future]
                try:
                    chunk_ner = future.result()
                    if chunk_ner:
                        with result_lock:
                            ner_results.extend(chunk_ner)
                except Exception as e:
                    print(f"❌ 处理chunk {chunk_id} 时出错: {e}")
                finally:
                    pbar.update(1)


    # 3. 保存所有chunks的NER结果
    if ner_results:
        filename = os.path.basename(chunk_filepath)
        output_filepath = os.path.join(config.NER_OUTPUT_DIR, filename)
        save_json(ner_results, output_filepath)
        print(f"✅ NER结果已保存到: {output_filepath}，共处理 {len(ner_results)} 个实体")
    else:
        print("⚠️ 未能从API获取NER结果。")

def process_file_wrapper(chunk_path, max_workers_per_file=4):
    """文件处理的包装函数，用于多线程处理文件"""
    try:
        run_ner_on_file(chunk_path, max_workers_per_file)
        return f"✅ 成功处理: {os.path.basename(chunk_path)}"
    except Exception as e:
        error_msg = f"❌ 处理文件 {os.path.basename(chunk_path)} 时出错: {e}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    # 多线程配置
    MAX_FILE_WORKERS = 2  # 同时处理的文件数量
    MAX_CHUNK_WORKERS = 4  # 每个文件内同时处理的chunk数量
    
    print("🚀 开始多线程NER处理...")
    print(f"📋 配置: 文件并发数={MAX_FILE_WORKERS}, 每文件chunk并发数={MAX_CHUNK_WORKERS}")
    
    # 确保输出目录存在
    os.makedirs(config.NER_OUTPUT_DIR, exist_ok=True)

    # 获取所有需要处理的文件
    chunk_files = []
    for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
        if filename.endswith(".json"):
            chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
            chunk_files.append(chunk_path)
    
    if not chunk_files:
        print("⚠️ 未找到需要处理的分块文件")
        exit(1)
    
    print(f"📁 找到 {len(chunk_files)} 个分块文件待处理")
    
    # 使用多线程处理文件
    with ThreadPoolExecutor(max_workers=MAX_FILE_WORKERS) as executor:
        # 创建部分函数，固定chunk worker数量
        process_func = partial(process_file_wrapper, max_workers_per_file=MAX_CHUNK_WORKERS)
        
        # 提交所有文件处理任务
        future_to_file = {
            executor.submit(process_func, chunk_path): chunk_path
            for chunk_path in chunk_files
        }
        
        # 显示总体进度
        results = []
        with tqdm.tqdm(total=len(chunk_files), desc="处理文件") as pbar:
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_msg = f"❌ 处理文件 {os.path.basename(file_path)} 时出现异常: {e}"
                    print(error_msg)
                    results.append(error_msg)
                finally:
                    pbar.update(1)
    
    # 输出处理结果统计
    success_count = sum(1 for r in results if "✅" in r)
    error_count = len(results) - success_count
    
    print("\n" + "="*50)
    print("🎉 所有分块文件的命名实体识别处理完成！")
    print(f"📊 处理统计: 成功 {success_count} 个，失败 {error_count} 个")
    if error_count > 0:
        print("❌ 失败的文件:")
        for result in results:
            if "❌" in result:
                print(f"   {result}")
    print("="*50)