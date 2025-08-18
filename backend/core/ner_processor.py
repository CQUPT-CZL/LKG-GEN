import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config
from .utils import call_llm, save_json, load_prompt, load_json

def validate_entity_with_llm(entity, context_text, validation_prompt_template):
    """使用大模型验证实体是否合理"""
    try:
        # 基础字段检查
        if not isinstance(entity, dict):
            return None
        
        required_fields = ['entity_text', 'entity_type', 'entity_description']
        for field in required_fields:
            if field not in entity or not entity[field]:
                return None
        
        # 构建验证prompt
        prompt = validation_prompt_template.replace("{{ENTITY_NAME}}", str(entity['entity_text']))
        prompt = prompt.replace("{{ENTITY_TYPE}}", str(entity['entity_type']))
        prompt = prompt.replace("{{ENTITY_DESCRIPTION}}", str(entity['entity_description']))
        prompt = prompt.replace("{{CONTEXT_TEXT}}", str(context_text))
        
        # 调用大模型进行验证
        validation_result = call_llm(prompt, model_name="qwen-max")
        # print(f"大模型验证结果: {validation_result}")
        
        if validation_result and isinstance(validation_result, dict):
            if validation_result.get('is_valid', False):
                # 如果有修正建议，使用修正后的实体
                corrected = validation_result.get('corrected_entity')
                if corrected and isinstance(corrected, dict):
                    # 更新实体信息
                    if corrected.get('name'):
                        entity['entity_text'] = corrected['name']
                    if corrected.get('type'):
                        entity['entity_type'] = corrected['type']
                    if corrected.get('description'):
                        entity['entity_description'] = corrected['description']
                return entity
            else:
                # 实体不合理，返回None表示删除
                print(f"🗑️ 删除不合理实体: {entity['entity_text']} - {validation_result.get('reason', '未知原因')}")
                return None
        else:
            # 验证失败，保守起见保留实体
            print(f"⚠️ 实体验证失败，保留实体: {entity['entity_text']}")
            return entity
            
    except Exception as e:
        print(f"❌ 验证实体 {entity.get('entity_text', 'unknown')} 时出错: {e}")
        # 出错时保留实体
        return entity

import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import partial

# 线程锁，用于保护共享资源
result_lock = threading.Lock()

def process_single_chunk(chunk_id, chunk_text, prompt_template, validation_prompt_template, file_prefix):
    """处理单个chunk的NER任务，包含实体验证"""
    try:
        # 1. 执行NER提取
        prompt = prompt_template.replace("{{ENTITY_TYPES}}", str(config.ENTITY_TYPES))
        prompt = prompt.replace("{{TEXT_CONTENT}}", chunk_text)
        chunk_ner = call_llm(prompt, model_name="qwen-max")
        
        if chunk_ner and isinstance(chunk_ner, list):
            validated_entities = []
            original_count = len(chunk_ner)
            
            # 2. 对每个实体进行验证
            for entity in chunk_ner:
                # 为chunk_id添加文件名前缀，格式：文件名_chunk_id
                entity['chunk_id'] = [f"{file_prefix}_{chunk_id}"]
                entity['category_path'] = [f"{file_prefix}_{chunk_id}"]
                
                # 验证实体
                validated_entity = validate_entity_with_llm(entity, chunk_text, validation_prompt_template)
                if validated_entity is not None:
                    validated_entities.append(validated_entity)
            
            # 3. 输出验证统计
            validated_count = len(validated_entities)
            print("---->")
            print(f"Chunk {chunk_id}: 原始实体 {original_count} 个，验证后保留 {validated_count} 个")
            print("----<")
            removed_count = original_count - validated_count
            if removed_count > 0:
                print(f"📊 Chunk {chunk_id}: 原始实体 {original_count} 个，验证后保留 {validated_count} 个，删除 {removed_count} 个")
            
            return validated_entities
        return []
    except Exception as e:
        print(f"❌ 处理chunk {chunk_id} 时出错: {e}")
        return []

def run_ner_on_file(chunk_filepath, max_workers=4):
    """对单个分块文件进行命名实体识别（多线程版本，包含实体验证）"""
    print(f"🔄 正在处理分块文件: {chunk_filepath}")
    
    # 1. 加载分块数据
    chunks = load_json(chunk_filepath)
    if not chunks:
        print("⚠️ 分块数据为空，跳过。")
        return None

    ner_results = []
    prompt_template = load_prompt(config.NER_PROMPT_PATH)
    
    # 加载实体验证prompt模板
    validation_prompt_template = load_prompt(config.ENTITY_VALIDATION_PROMPT_PATH)

    # 获取文件名前缀（去掉.json扩展名）
    file_prefix = os.path.basename(chunk_filepath).replace('.json', '')
    
    # 2. 使用多线程对每个chunk进行NER和验证
    print(f"📊 开始处理 {len(chunks)} 个chunks，使用 {max_workers} 个线程（包含实体验证）")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_chunk = {
            executor.submit(process_single_chunk, chunk_id, chunk_text, prompt_template, validation_prompt_template, file_prefix): chunk_id
            for chunk_id, chunk_text in chunks.items()
        }
        
        # 收集结果
        with tqdm.tqdm(total=len(chunks), desc=f"处理 {os.path.basename(chunk_filepath)}") as pbar:
            for future in as_completed(future_to_chunk):
                chunk_id = future_to_chunk[future]
                try:
                    chunk_result = future.result()
                    with result_lock:
                        ner_results.extend(chunk_result)
                except Exception as e:
                    print(f"❌ 处理chunk {chunk_id} 时出现异常: {e}")
                finally:
                    pbar.update(1)

    # 3. 保存NER结果并输出统计信息
    if ner_results:
        filename = os.path.basename(chunk_filepath)
        output_filepath = os.path.join(config.NER_OUTPUT_DIR, filename)
        save_json(ner_results, output_filepath)
        print(f"✅ NER结果已保存到: {output_filepath}")
        print(f"📈 文件 {filename} 验证后共保留 {len(ner_results)} 个有效实体")
        return output_filepath
    else:
        print("⚠️ 未能生成NER结果。")
        return None

def process_file_wrapper(chunk_path, max_workers_per_file=4):
    """文件处理包装器"""
    try:
        result = run_ner_on_file(chunk_path, max_workers_per_file)
        if result:
            return f"✅ 成功处理: {os.path.basename(chunk_path)}"
        else:
            return f"⚠️ 处理失败: {os.path.basename(chunk_path)}"
    except Exception as e:
        return f"❌ 处理异常: {os.path.basename(chunk_path)} - {e}"

def process_all_files(max_file_workers=2, max_chunk_workers=4):
    """处理所有分块文件的NER任务"""
    print("🚀 开始多线程NER处理...")
    print(f"📋 配置: 文件并发数={max_file_workers}, 每文件chunk并发数={max_chunk_workers}")
    
    # 确保输出目录存在
    os.makedirs(config.NER_OUTPUT_DIR, exist_ok=True)
    
    # 获取所有分块文件
    chunk_files = []
    for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
        if filename.endswith(".json"):
            chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
            chunk_files.append(chunk_path)
    
    if not chunk_files:
        print("⚠️ 未找到需要处理的分块文件")
        return []
    
    print(f"📁 找到 {len(chunk_files)} 个分块文件待处理")
    
    # 使用多线程处理文件
    with ThreadPoolExecutor(max_workers=max_file_workers) as executor:
        # 创建部分函数，固定max_workers_per_file参数
        process_func = partial(process_file_wrapper, max_workers_per_file=max_chunk_workers)
        
        # 提交所有文件处理任务
        future_to_file = {
            executor.submit(process_func, chunk_path): chunk_path
            for chunk_path in chunk_files
        }
        
        # 收集结果
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
    
    # 统计结果
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
    
    return results

if __name__ == "__main__":
    MAX_FILE_WORKERS = 2  # 同时处理的文件数量
    MAX_CHUNK_WORKERS = 4  # 每个文件内同时处理的chunk数量
    process_all_files(MAX_FILE_WORKERS, MAX_CHUNK_WORKERS)