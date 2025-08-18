import os
import sys
import json
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

# 导入重构后的核心模块
try:
    from core import (
        config, save_json, load_json, load_text, load_prompt, call_llm,
        run_chunk_on_file, run_ner_on_file, run_relation_extraction_on_all,
        simple_entity_disambiguation, ensure_output_files_exist,
        run_disambiguate_on_all_files
    )
except ImportError as e:
    print(f"导入知识图谱构建核心模块失败: {e}")
    print("请确保backend/core目录下的模块可用")

from data_manager import DataManager

class KnowledgeGraphBuilder:
    """知识图谱构建器 - 整合现有的Python脚本"""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager or DataManager()
        
        # 确保必要的目录存在
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # 当前工作目录（用于独立构建模式）
        self.current_work_dir = None
        
        # 确保src/data目录结构存在
        self._ensure_data_directories()
        
        # 确保输出文件存在
        ensure_output_files_exist()
    
    def _ensure_data_directories(self):
        """确保数据目录结构存在"""
        try:
            # 使用config中定义的目录
            directories = [
                config.PROCESSED_TEXT_DIR,
                config.CHUNK_OUTPUT_DIR,
                config.NER_OUTPUT_DIR,
                config.NER_PRO_OUTPUT_DIR,
                config.RE_OUTPUT_DIR
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                
        except Exception as e:
            print(f"创建数据目录失败: {e}")
    

    
    def _get_work_directories(self, graph_id: str) -> Dict[str, str]:
        """根据图谱ID获取工作目录"""
        if not graph_id:
            raise ValueError("图谱ID不能为空")
        
        # 所有图谱都使用图谱特定的子目录
        return config.get_graph_data_dirs(graph_id)
    
    def _update_config_paths(self, work_dirs: Dict[str, str]):
        """临时更新config中的路径"""
        self.original_paths = {
            "PROCESSED_TEXT_DIR": config.PROCESSED_TEXT_DIR,
            "CHUNK_OUTPUT_DIR": config.CHUNK_OUTPUT_DIR,
            "NER_OUTPUT_DIR": config.NER_OUTPUT_DIR,
            "NER_PRO_OUTPUT_DIR": config.NER_PRO_OUTPUT_DIR,
            "RE_OUTPUT_DIR": config.RE_OUTPUT_DIR
        }
        
        # 更新config路径
        config.PROCESSED_TEXT_DIR = work_dirs["PROCESSED_TEXT_DIR"]
        config.CHUNK_OUTPUT_DIR = work_dirs["CHUNK_OUTPUT_DIR"]
        config.NER_OUTPUT_DIR = work_dirs["NER_OUTPUT_DIR"]
        config.NER_PRO_OUTPUT_DIR = work_dirs["NER_PRO_OUTPUT_DIR"]
        config.RE_OUTPUT_DIR = work_dirs["RE_OUTPUT_DIR"]
    
    def _restore_config_paths(self):
        """恢复config中的原始路径"""
        if hasattr(self, 'original_paths'):
            config.PROCESSED_TEXT_DIR = self.original_paths["PROCESSED_TEXT_DIR"]
            config.CHUNK_OUTPUT_DIR = self.original_paths["CHUNK_OUTPUT_DIR"]
            config.NER_OUTPUT_DIR = self.original_paths["NER_OUTPUT_DIR"]
            config.NER_PRO_OUTPUT_DIR = self.original_paths["NER_PRO_OUTPUT_DIR"]
            config.RE_OUTPUT_DIR = self.original_paths["RE_OUTPUT_DIR"]
    
    async def process_document(self, file_path: str, filename: str, 
                             target_graph_id: str = None,
                             progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """处理文档并附加到现有知识图谱
        
        Args:
            file_path: 文档文件路径
            filename: 文档文件名
            target_graph_id: 目标图谱ID（可选，如果不指定则创建新图谱）
            progress_callback: 进度回调函数
        
        Returns:
            Dict: 处理结果，包含成功状态、图谱ID、统计信息等
        """
        graph_id = target_graph_id
        
        try:
            # 记录整个流程的开始时间
            total_start_time = datetime.now()
            
            print(f"🚀 开始处理文档: {filename}")
            print(f"📁 文件路径: {file_path}")
            print(f"🔧 构建模式: 附加到现有图谱")
            print(f"🎯 目标图谱ID: {target_graph_id}")
            
            # 🆕 获取图谱信息以确定使用的目录
            if not target_graph_id:
                raise ValueError("目标图谱ID不能为空")
                
            graph_info = self.data_manager.get_graph(target_graph_id)
            if not graph_info:
                raise ValueError(f"图谱 {target_graph_id} 不存在")
                
            graph_name = graph_info.get('name')
            print(f"📊 目标图谱名称: {graph_name}")
            
            # 设置工作目录 - 使用图谱ID而不是图谱名称
            work_dirs = self._get_work_directories(target_graph_id)
            self._update_config_paths(work_dirs)
            print(f"📂 使用数据目录: {work_dirs}")
            
            if progress_callback:
                progress_callback(5, "开始文档预处理")
            
            # 1. 文档预处理
            print("📝 步骤1: 开始文档预处理...")
            processed_file_path = await self._preprocess_document(file_path, filename)
            print(f"✅ 文档预处理完成，输出文件: {processed_file_path}")
            if progress_callback:
                progress_callback(15, "文档预处理完成")
            
            # 2. 文本分块
            print("🔪 步骤2: 开始文档分块...")
            chunk_result = await self._chunk_document(processed_file_path)
            print(f"✅ 文档分块完成，生成 {chunk_result.get('chunks_count', 0)} 个块")
            if progress_callback:
                progress_callback(30, f"文本分块完成，共生成 {chunk_result.get('chunks_count', 0)} 个文本块")
            
            # 3. 实体识别
            print("🏷️ 步骤3: 开始实体识别...")
            ner_result = await self._extract_entities(chunk_result["chunk_file"])
            print(f"✅ 实体识别完成，识别出 {ner_result.get('entities_count', 0)} 个实体")
            if progress_callback:
                progress_callback(45, f"实体识别完成，共识别 {ner_result.get('entities_count', 0)} 个实体")
            
            # 4. 实体消歧
            print("🔍 步骤4: 开始实体消歧...")
            disambig_result = await self._disambiguate_entities()
            print(f"✅ 实体消歧完成，处理 {disambig_result.get('entities_count', 0)} 个唯一实体")
            if progress_callback:
                progress_callback(55, f"实体消歧完成，共处理 {disambig_result.get('entities_count', 0)} 个唯一实体")
            
            # 5. 关系抽取
            print("🔗 步骤5: 开始关系抽取...")
            relation_result = await self._extract_relations(progress_callback)
            print(f"✅ 关系抽取完成，抽取出 {relation_result.get('relations_count', 0)} 个关系")
            
            # 6. 构建知识图谱
            print("🕸️ 步骤6: 开始构建知识图谱...")
            kg_result = await self._build_knowledge_graph(filename, ner_result, relation_result, graph_id, progress_callback)
            print(f"✅ 知识图谱构建完成，图谱ID: {kg_result['graph_id']}")
            
            # 7. 清理临时文件
            print("🧹 步骤7: 清理临时文件...")
            await self._cleanup_temp_files(file_path)
            print("✅ 临时文件清理完成")
            
            print("🎉 知识图谱构建流程全部完成！")
            
            # 恢复原始配置路径
            self._restore_config_paths()
            
            # 计算整个流程的总处理时间
            total_end_time = datetime.now()
            total_processing_time = (total_end_time - total_start_time).total_seconds()
            print(f"⏱️ 时间计算调试信息:")
            print(f"   开始时间: {total_start_time}")
            print(f"   结束时间: {total_end_time}")
            print(f"   总处理时间: {total_processing_time:.2f}秒")
            
            # 使用构建结果中的图谱ID
            final_graph_id = kg_result["graph_id"]
            
            return {
                "success": True,
                "graph_id": final_graph_id,
                "statistics": {
                    "entities_count": kg_result["entities_count"],
                    "relations_count": kg_result["relations_count"],
                    "chunks_processed": chunk_result.get("chunks_count", 0),
                    "processing_time": f"{total_processing_time:.2f}秒"
                },
                "message": "知识图谱构建成功",
                "details": {
                    "chunk_result": chunk_result,
                    "ner_result": ner_result,
                    "disambig_result": disambig_result,
                    "relation_result": relation_result,
                    "kg_result": kg_result
                }
            }
            
        except Exception as e:
            print(f"💥 处理文档时发生异常: {str(e)}")
            import traceback
            print(f"📋 异常堆栈: {traceback.format_exc()}")
            
            # 恢复原始配置路径
            self._restore_config_paths()
            
            if progress_callback:
                progress_callback(0, f"处理失败: {str(e)}")
            
            # 尝试清理临时文件
            try:
                await self._cleanup_temp_files(file_path)
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "message": "知识图谱构建失败"
            }
    
    async def _preprocess_document(self, file_path: str, filename: str) -> str:
        """文档预处理 - 转换为markdown格式"""
        try:
            print(f"📝 开始文档预处理，处理文件: {file_path}")
            print(f"📄 文件名: {filename}")
            
            # 检查输入文件是否存在
            if not os.path.exists(file_path):
                print(f"❌ 输入文件不存在: {file_path}")
                raise Exception(f"输入文件不存在: {file_path}")
            
            # 确保预处理输出目录存在
            os.makedirs(config.PROCESSED_TEXT_DIR, exist_ok=True)
            print(f"📁 预处理输出目录: {config.PROCESSED_TEXT_DIR}")
            
            # 读取文件内容
            print("📖 读取文件内容...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📊 原始文件大小: {len(content)} 字符")
                print(f"📝 原始内容预览: {content[:200]}...")
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                raise Exception(f"读取文件失败: {e}")
            
            # 简单的文本预处理
            print("🔄 开始文本清理...")
            processed_content = self._clean_text(content)
            print(f"📊 处理后文件大小: {len(processed_content)} 字符")
            print(f"📝 处理后内容预览: {processed_content[:200]}...")
            
            # 保存到processed_text目录
            processed_filename = filename.replace('.txt', '.md').replace('.pdf', '.md')
            processed_file_path = os.path.join(config.PROCESSED_TEXT_DIR, processed_filename)
            print(f"💾 保存预处理结果到: {processed_file_path}")
            
            try:
                with open(processed_file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                print("✅ 预处理结果保存成功")
            except Exception as e:
                print(f"❌ 保存预处理结果失败: {e}")
                raise Exception(f"保存预处理结果失败: {e}")
            
            return processed_file_path
            
        except Exception as e:
            print(f"❌ 文档预处理过程出错: {e}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            raise Exception(f"文档预处理失败: {e}")
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        print("🧹 开始清理文本内容...")
        
        # 移除多余的空白字符
        lines = text.split('\n')
        cleaned_lines = []
        
        original_lines_count = len(lines)
        print(f"📊 原始行数: {original_lines_count}")
        
        for line in lines:
            line = line.strip()
            if line:  # 跳过空行
                cleaned_lines.append(line)
        
        cleaned_lines_count = len(cleaned_lines)
        print(f"📊 清理后行数: {cleaned_lines_count} (移除了 {original_lines_count - cleaned_lines_count} 个空行)")
        
        result = '\n'.join(cleaned_lines)
        print(f"✅ 文本清理完成")
        
        return result
    
    async def _chunk_document(self, processed_file_path: str) -> Dict[str, Any]:
        """文档分块处理"""
        try:
            print(f"🔪 开始文档分块，处理文件: {processed_file_path}")
            
            # 检查输入文件是否存在
            if not os.path.exists(processed_file_path):
                print(f"❌ 预处理文件不存在: {processed_file_path}")
                raise Exception(f"预处理文件不存在: {processed_file_path}")
            
            # 确保分块输出目录存在
            os.makedirs(config.CHUNK_OUTPUT_DIR, exist_ok=True)
            print(f"📁 分块输出目录: {config.CHUNK_OUTPUT_DIR}")
            
            # 检查输入文件内容
            try:
                with open(processed_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📊 输入文件大小: {len(content)} 字符")
                print(f"📝 文件内容预览: {content[:200]}...")
            except Exception as e:
                print(f"❌ 读取预处理文件失败: {e}")
                raise Exception(f"读取预处理文件失败: {e}")
            
            print("🔄 开始调用分块处理函数...")
            # 调用现有的分块函数
            await asyncio.get_event_loop().run_in_executor(
                None, run_chunk_on_file, processed_file_path
            )
            print("✅ 分块处理函数调用完成")
            
            # 获取分块结果文件路径
            filename = os.path.basename(processed_file_path)
            chunk_filename = filename.replace('.md', '.json')
            chunk_file_path = os.path.join(config.CHUNK_OUTPUT_DIR, chunk_filename)
            
            print(f"🔍 检查分块结果文件: {chunk_file_path}")
            
            # 检查分块结果文件是否存在
            if not os.path.exists(chunk_file_path):
                print(f"❌ 分块结果文件不存在: {chunk_file_path}")
                # 列出分块输出目录的所有文件
                try:
                    files_in_dir = os.listdir(config.CHUNK_OUTPUT_DIR)
                    print(f"📂 分块输出目录中的文件: {files_in_dir}")
                except Exception as e:
                    print(f"❌ 无法列出分块输出目录文件: {e}")
                raise Exception("分块结果文件未生成")
            
            # 读取分块结果
            print("📖 读取分块结果文件...")
            chunks = load_json(chunk_file_path)
            chunks_count = len(chunks) if chunks else 0
            print(f"✅ 成功读取分块结果，共 {chunks_count} 个文本块")
            
            if chunks and len(chunks) > 0:
                chunk_keys = list(chunks.keys())
                print(f"📝 分块示例: {chunk_keys[0] if chunk_keys else 'None'}")
            
            return {
                "success": True,
                "chunk_file": chunk_file_path,
                "chunks_count": chunks_count
            }
            
        except Exception as e:
            print(f"❌ 文档分块过程出错: {e}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            raise Exception(f"文档分块失败: {e}")
    
    async def _extract_entities(self, chunk_file_path: str) -> Dict[str, Any]:
        """实体识别处理"""
        try:
            print(f"🔄 开始实体识别，处理文件: {chunk_file_path}")
            
            # 检查输入文件是否存在
            if not os.path.exists(chunk_file_path):
                print(f"❌ 输入文件不存在: {chunk_file_path}")
                raise Exception(f"输入文件不存在: {chunk_file_path}")
            
            # 确保输出目录存在
            os.makedirs(config.NER_OUTPUT_DIR, exist_ok=True)
            print(f"📁 NER输出目录: {config.NER_OUTPUT_DIR}")
            
            # 检查输入文件内容
            try:
                chunks = load_json(chunk_file_path)
                print(f"📊 读取到 {len(chunks) if chunks else 0} 个文本块")
                if chunks:
                    print(f"📝 第一个块预览: {str(list(chunks.keys())[0] if chunks else 'None')[:100]}...")
            except Exception as e:
                print(f"❌ 读取输入文件失败: {e}")
                raise Exception(f"读取输入文件失败: {e}")
            
            print("🔄 开始调用NER处理函数...")
            # 调用现有的NER函数
            # 调用step2_ner.py中的run_ner_on_file函数进行实体识别
            # 参数1: chunk_file_path - 分块后的文件路径
            # 参数2: 2 - 使用2个线程进行并行处理
            await asyncio.get_event_loop().run_in_executor(
                None, run_ner_on_file, chunk_file_path, 2
            )
            print("✅ NER处理函数调用完成")
            
            # 获取NER结果文件路径
            filename = os.path.basename(chunk_file_path)
            ner_file_path = os.path.join(config.NER_OUTPUT_DIR, filename)
            
            print(f"📁 查找NER结果文件: {ner_file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(ner_file_path):
                print(f"⚠️ NER结果文件不存在: {ner_file_path}")
                # 列出输出目录的所有文件
                try:
                    files_in_dir = os.listdir(config.NER_OUTPUT_DIR)
                    print(f"📂 NER输出目录中的文件: {files_in_dir}")
                except Exception as e:
                    print(f"❌ 无法列出NER输出目录文件: {e}")
                
                return {
                    "success": False,
                    "error": "NER结果文件未生成",
                    "entities_count": 0
                }
            
            # 读取NER结果
            print("📖 读取NER结果文件...")
            entities = load_json(ner_file_path)
            print(f"✅ 成功读取NER结果，共 {len(entities) if entities else 0} 个实体")
            
            if entities and len(entities) > 0:
                print(f"📝 实体示例: {entities[0] if entities else 'None'}")
            
            return {
                "success": True,
                "ner_file": ner_file_path,
                "entities_count": len(entities) if entities else 0
            }
            
        except Exception as e:
            print(f"❌ 实体识别过程出错: {e}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            raise Exception(f"实体识别失败: {e}")
    
    async def _disambiguate_entities(self) -> Dict[str, Any]:
        """实体消歧处理"""
        try:
            print("🔍 开始实体消歧处理...")
            
            # 检查输入文件是否存在
            ner_output_dir = config.NER_OUTPUT_DIR
            print(f"📁 检查NER输出目录: {ner_output_dir}")
            
            if not os.path.exists(ner_output_dir):
                print(f"❌ NER输出目录不存在: {ner_output_dir}")
                raise Exception(f"NER输出目录不存在: {ner_output_dir}")
            
            # 列出NER输出目录中的文件
            try:
                ner_files = os.listdir(ner_output_dir)
                print(f"📂 NER输出目录中的文件: {ner_files}")
            except Exception as e:
                print(f"❌ 无法列出NER输出目录文件: {e}")
                raise Exception(f"无法访问NER输出目录: {e}")
            
            # 确保消歧输出目录存在
            os.makedirs(config.NER_PRO_OUTPUT_DIR, exist_ok=True)
            print(f"📁 消歧输出目录: {config.NER_PRO_OUTPUT_DIR}")
            
            print("🔄 开始调用消歧处理函数...")
            # 直接调用消歧处理函数
            success = await asyncio.get_event_loop().run_in_executor(
                None, run_disambiguate_on_all_files
            )
            print(f"✅ 消歧处理函数调用完成，结果: {success}")
            
            if not success:
                print("❌ 实体消歧处理返回失败")
                raise Exception("实体消歧处理失败")
            
            # 获取消歧结果文件路径
            disambig_file_path = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
            print(f"🔍 检查消歧结果文件: {disambig_file_path}")
            
            # 检查消歧结果文件是否存在
            if not os.path.exists(disambig_file_path):
                print(f"❌ 消歧结果文件不存在: {disambig_file_path}")
                # 列出消歧输出目录的所有文件
                try:
                    files_in_dir = os.listdir(config.NER_PRO_OUTPUT_DIR)
                    print(f"📂 消歧输出目录中的文件: {files_in_dir}")
                except Exception as e:
                    print(f"❌ 无法列出消歧输出目录文件: {e}")
                raise Exception("消歧结果文件未生成")
            
            # 读取消歧结果
            print("📖 读取消歧结果文件...")
            disambiguated_entities = load_json(disambig_file_path)
            entities_count = len(disambiguated_entities) if disambiguated_entities else 0
            print(f"✅ 成功读取消歧结果，共 {entities_count} 个实体")
            
            if disambiguated_entities and len(disambiguated_entities) > 0:
                print(f"📝 消歧实体示例: {disambiguated_entities[0] if disambiguated_entities else 'None'}")
            
            return {
                "success": True,
                "disambig_file": disambig_file_path,
                "entities_count": entities_count
            }
            
        except Exception as e:
            print(f"❌ 实体消歧过程出错: {e}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            raise Exception(f"实体消歧失败: {e}")
    
    async def _extract_relations(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """关系抽取处理"""
        try:
            if progress_callback:
                progress_callback(60, "开始关系抽取...")
            
            # 调用带进度的关系抽取函数
            await asyncio.get_event_loop().run_in_executor(
                None, self._run_relation_extraction_with_progress, progress_callback
            )
            
            # 获取关系抽取结果文件路径
            relations_file_path = os.path.join(config.RE_OUTPUT_DIR, "all_relations.json")
            
            # 读取关系抽取结果
            relations = load_json(relations_file_path)
            
            if progress_callback:
                progress_callback(80, f"关系抽取完成，共抽取 {len(relations) if relations else 0} 个关系")
            
            return {
                "success": True,
                "relations_file": relations_file_path,
                "relations_count": len(relations) if relations else 0
            }
            
        except Exception as e:
            raise Exception(f"关系抽取失败: {e}")
    
    def _run_relation_extraction_with_progress(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        """带进度显示的关系抽取"""
        print("🔄 开始关系抽取处理...")
        
        # 加载消歧后的实体文件
        disambiguated_entities_path = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
        
        if not os.path.exists(disambiguated_entities_path):
            raise Exception(f"找不到消歧实体文件: {disambiguated_entities_path}")
        
        print(f"📄 正在加载消歧实体文件: all_entities_disambiguated.json")
        disambiguated_entities = load_json(disambiguated_entities_path)
        
        if not disambiguated_entities:
            raise Exception("消歧实体数据为空")
        
        print(f"✅ 加载了 {len(disambiguated_entities)} 个消歧后的实体")
        
        # 加载所有文档chunks（附加模式）
        print("📚 加载所有文档chunks...")
        all_chunks = self._load_all_chunks()
        
        if not all_chunks:
            raise Exception("没有找到任何chunk数据")
        
        # 创建 chunk_id -> entities 的映射
        chunk_to_entities_map = self._create_chunk_to_entities_map(disambiguated_entities)
        
        extracted_triples = []
        total_chunks = len(chunk_to_entities_map)
        
        print(f"🔗 开始处理 {total_chunks} 个文本块的关系抽取")
        
        for i, (chunk_id, entities) in enumerate(chunk_to_entities_map.items()):
            # 更新进度
            progress = 60 + int((i / total_chunks) * 15)  # 60-75%的进度范围
            if progress_callback:
                progress_callback(progress, f"正在处理第 {i+1}/{total_chunks} 个文本块: {chunk_id[:20]}...")
            
            chunk_text = all_chunks.get(chunk_id, "")
            if not chunk_text:
                print(f"⚠️  Chunk {chunk_id} 在chunk数据中不存在，跳过")
                continue
            
            if len(entities) < 2:
                continue  # 实体数量少于2个，无法形成关系
            
            # 为当前块抽取关系
            triples_from_chunk = self._extract_relations_for_chunk(chunk_id, chunk_text, entities)
            
            validated_triples = []
            # 将实体列表转为集合，便于快速查找
            valid_entity_set = set(entities)
            
            for triple in triples_from_chunk:
                if len(triple) == 3:
                    head, relation, tail = triple
                    # 检查头实体和尾实体是否都在合法的实体列表中
                    if head in valid_entity_set and tail in valid_entity_set:
                        validated_triples.append(triple)
                    else:
                        print(f"--- [已过滤] 发现幻觉实体，已丢弃: {triple}")
            
            # 为每个三元组添加来源信息
            for triple in validated_triples:
                if len(triple) == 3:
                    extracted_triples.append({
                        "head": triple[0],
                        "relation": triple[1],
                        "tail": triple[2],
                        "source_chunk_id": chunk_id
                    })
        
        # 去重处理
        if progress_callback:
            progress_callback(75, "正在去重和整理关系数据...")
        
        unique_triples_str = {json.dumps(d, sort_keys=True) for d in extracted_triples}
        final_triples = [json.loads(s) for s in unique_triples_str]
        
        # 保存所有关系抽取结果到统一文件
        output_path = os.path.join(config.RE_OUTPUT_DIR, "all_relations.json")
        save_json(final_triples, output_path)
        
        print(f"✅ 关系抽取处理完成！")
        print(f"📈 统计信息:")
        print(f"   🏷️  处理实体数: {len(disambiguated_entities)}")
        print(f"   📄 处理chunk数: {len(chunk_to_entities_map)}")
        print(f"   🔗 抽取关系数: {len(final_triples)}")
        print(f"   💾 结果保存到: {output_path}")
    
    def _load_all_chunks(self):
        """加载所有chunk文件的内容（用于附加模式）"""
        all_chunks = {}
        
        for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
            if filename.endswith(".json"):
                chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
                file_prefix = filename.replace('.json', '')
                
                chunks = load_json(chunk_path)
                if chunks:
                    # 为每个chunk_id添加文件名前缀
                    for chunk_id, chunk_text in chunks.items():
                        prefixed_chunk_id = f"{file_prefix}_{chunk_id}"
                        all_chunks[prefixed_chunk_id] = chunk_text
                        
                    print(f"📄 加载了文件 {filename}，包含 {len(chunks)} 个chunks")
        
        print(f"📊 总共加载了 {len(all_chunks)} 个chunks")
        return all_chunks
    
    def _load_current_chunks(self):
        """仅加载当前文档的chunk文件内容（用于独立构建模式）"""
        all_chunks = {}
        
        # 获取最新的chunk文件（按修改时间排序）
        chunk_files = []
        for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
            if filename.endswith(".json"):
                chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
                mtime = os.path.getmtime(chunk_path)
                chunk_files.append((mtime, filename, chunk_path))
        
        if not chunk_files:
            print("❌ 没有找到任何chunk文件")
            return all_chunks
        
        # 按修改时间排序，获取最新的文件
        chunk_files.sort(reverse=True)
        latest_file = chunk_files[0]
        filename = latest_file[1]
        chunk_path = latest_file[2]
        
        print(f"📄 独立构建模式：仅加载最新的chunk文件 {filename}")
        
        file_prefix = filename.replace('.json', '')
        chunks = load_json(chunk_path)
        if chunks:
            # 为每个chunk_id添加文件名前缀
            for chunk_id, chunk_text in chunks.items():
                prefixed_chunk_id = f"{file_prefix}_{chunk_id}"
                all_chunks[prefixed_chunk_id] = chunk_text
                
            print(f"📄 加载了文件 {filename}，包含 {len(chunks)} 个chunks")
        
        print(f"📊 独立构建模式：总共加载了 {len(all_chunks)} 个chunks")
        return all_chunks
    
    def _create_chunk_to_entities_map(self, disambiguated_entities: list):
        """创建从chunk_id到实体名称列表的映射"""
        from collections import defaultdict
        chunk_map = defaultdict(list)
        for entity in disambiguated_entities:
            # 我们只关心规范名称
            canonical_name = entity["entity_text"]
            for chunk_id in entity["chunk_id"]:
                if canonical_name not in chunk_map[chunk_id]:
                    chunk_map[chunk_id].append(canonical_name)
        return chunk_map
    
    def _extract_relations_for_chunk(self, chunk_id: str, chunk_text: str, entities_in_chunk: list):
        """为单个文本块调用LLM进行关系抽取"""
        try:
            # 加载关系抽取提示词
            re_prompt = load_prompt(config.RE_PROMPT_PATH)
            
            # 构建实体列表字符串
            entities_str = ", ".join(entities_in_chunk)
            
            # 加载关系类型
            relation_types = "\n".join([
                "使用原料", "生产产品", "应用于", "具有性质", "包含成分",
                "经过工艺", "使用设备", "产生副产品", "影响因素", "测量指标"
            ])
            
            # 构建完整的提示词
            full_prompt = re_prompt.replace("{{CHUNK_TEXT}}", chunk_text).replace("{{ENTITIES_IN_CHUNK}}", entities_str).replace("{{RELATION_TYPES}}", relation_types)
            
            # 调用LLM
            response = call_llm(full_prompt)
            
            # 解析响应，提取三元组
            if isinstance(response, list):
                # 如果返回的是列表，直接处理
                triples = []
                for item in response:
                    if isinstance(item, dict) and 'head' in item and 'relation' in item and 'tail' in item:
                        triples.append([item['head'], item['relation'], item['tail']])
                    elif isinstance(item, list) and len(item) == 3:
                        triples.append(item)
            elif isinstance(response, dict) and 'relations' in response:
                # 如果返回的是包含relations字段的字典
                triples = []
                for item in response['relations']:
                    if isinstance(item, dict) and 'head' in item and 'relation' in item and 'tail' in item:
                        triples.append([item['head'], item['relation'], item['tail']])
                    elif isinstance(item, list) and len(item) == 3:
                        triples.append(item)
            else:
                # 其他情况返回空列表
                triples = []
            
            print(f"📝 Chunk {chunk_id}: 发现 {len(triples)} 个关系")
            return triples
            
        except Exception as e:
            print(f"❌ 处理chunk {chunk_id} 时出错: {e}")
            return []
    
    def _parse_relation_response(self, response: str):
        """解析LLM的关系抽取响应"""
        triples = []
        try:
            # 尝试解析JSON格式的响应
            if response.strip().startswith('['):
                parsed = json.loads(response)
                for item in parsed:
                    if isinstance(item, dict) and 'head' in item and 'relation' in item and 'tail' in item:
                        triples.append([item['head'], item['relation'], item['tail']])
                    elif isinstance(item, list) and len(item) == 3:
                        triples.append(item)
            else:
                # 尝试解析文本格式的响应
                lines = response.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) == 3:
                            triples.append(parts)
                    elif '->' in line:
                        # 处理 "实体1 -> 关系 -> 实体2" 格式
                        parts = [p.strip() for p in line.split('->')]
                        if len(parts) == 3:
                            triples.append([parts[0], parts[1], parts[2]])
        except Exception as e:
            print(f"解析关系响应时出错: {e}")
        
        return triples
    
    async def _build_knowledge_graph(self, filename: str, ner_result: Dict, relation_result: Dict, 
                                    target_graph_id: Optional[str] = None,
                                    progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """构建知识图谱并保存到数据管理器"""
        try:
            start_time = datetime.now()
            
            if progress_callback:
                progress_callback(85, "开始构建知识图谱...")
            
            # 决定图谱ID
            if target_graph_id:
                # 附加到指定的目标图谱
                graph_id = target_graph_id
                print(f"🔗 附加到现有图谱ID: {graph_id}")
            else:
                # 创建新的知识图谱
                graph_name = f"从 {filename} 构建的知识图谱"
                graph_description = f"基于文档 {filename} 自动构建的知识图谱，包含实体识别和关系抽取结果"
                
                graph = self.data_manager.create_graph(
                    name=graph_name,
                    description=graph_description
                )
                graph_id = graph["id"]
                print(f"📊 创建新图谱ID: {graph_id}")
            
            if progress_callback:
                progress_callback(87, "正在读取实体和关系数据...")
            
            # 读取消歧后的实体数据
            disambig_file_path = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
            entities_raw_data = load_json(disambig_file_path)
            
            # 读取关系数据
            relations_file_path = os.path.join(config.RE_OUTPUT_DIR, "all_relations.json")
            relations_raw_data = load_json(relations_file_path)
            
            if progress_callback:
                progress_callback(90, "正在转换数据格式...")
            
            # 转换实体数据格式以匹配import_kg_data的期望
            entities_data = []
            for entity in entities_raw_data:
                entities_data.append({
                    "name": entity["entity_text"],
                    "type": entity["entity_type"],
                    "description": entity.get("entity_description", ""),
                    "frequency": len(entity.get("chunk_id", [])),  # 使用出现次数作为频率
                    "source_chunks": entity.get("chunk_id", [])
                })
            
            # 转换关系数据格式以匹配import_kg_data的期望
            relations_data = []
            for relation in relations_raw_data:
                relations_data.append({
                    "source_entity": relation["head"],
                    "target_entity": relation["tail"],
                    "relation_type": relation["relation"],
                    "confidence": 0.8,  # 默认置信度
                    "description": f"从文档中抽取的关系: {relation['head']} {relation['relation']} {relation['tail']}",
                    "source_chunk_id": relation.get("source_chunk_id", "")
                })
            
            if progress_callback:
                progress_callback(93, f"正在保存 {len(entities_data)} 个实体和 {len(relations_data)} 个关系到图谱目录...")
            
            # 清理图谱的旧数据
            print(f"🔄 开始清理图谱 {graph_id} 的旧数据...")
            self.data_manager._clear_graph_data(graph_id)
            
            # 直接将消歧后的数据保存到图谱特定目录
            print(f"📁 数据已生成在 ner_pro_output/{graph_id} 目录中，无需复制...")
            
            # 直接使用ner_pro_output目录中的数据文件
            target_entities_file = disambig_file_path  # 直接使用原始消歧文件
            target_relations_file = relations_file_path  # 直接使用原始关系文件
            
            print(f"✅ 实体数据位于: {target_entities_file}")
            print(f"✅ 关系数据位于: {target_relations_file}")
            print(f"💡 数据管理器将直接从 ner_pro_output 目录读取数据")
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            entities_count = len(entities_data)
            relations_count = len(relations_data)
            
            print(f"✅ 知识图谱构建完成！包含 {entities_count} 个实体和 {relations_count} 个关系")
            
            if progress_callback:
                progress_callback(100, f"知识图谱构建完成！包含 {entities_count} 个实体和 {relations_count} 个关系")
            
            return {
                "success": True,
                "graph_id": graph_id,
                "entities_count": entities_count,
                "relations_count": relations_count,
                "processing_time": processing_time,
                "entities_file": str(target_entities_file),
                "relations_file": str(target_relations_file)
            }
            
        except Exception as e:
            raise Exception(f"构建知识图谱失败: {e}")
    
    async def _cleanup_temp_files(self, original_file_path: str):
        """清理临时文件和目录"""
        try:
            import shutil
            
            # 删除上传的原始文件
            if os.path.exists(original_file_path):
                os.remove(original_file_path)
            
            # 清理临时目录
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"已清理临时目录: {self.temp_dir}")
            
            # 清理处理过程中的输出目录（可选）
            # 注意：这里不清理config中的输出目录，因为用户可能需要查看中间结果
            
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return ['.txt', '.md', '.pdf', '.docx']
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证文件格式和大小"""
        try:
            file_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                return {"valid": False, "error": "文件不存在"}
            
            # 检查文件扩展名
            if file_path.suffix.lower() not in self.get_supported_formats():
                return {
                    "valid": False, 
                    "error": f"不支持的文件格式，支持的格式: {', '.join(self.get_supported_formats())}"
                }
            
            # 检查文件大小（限制为10MB）
            file_size = file_path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB
            
            if file_size > max_size:
                return {
                    "valid": False, 
                    "error": f"文件过大，最大支持 {max_size // (1024*1024)}MB"
                }
            
            return {
                "valid": True,
                "file_size": file_size,
                "file_format": file_path.suffix.lower()
            }
            
        except Exception as e:
            return {"valid": False, "error": f"文件验证失败: {str(e)}"}