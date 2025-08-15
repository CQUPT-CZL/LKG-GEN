#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱构建流水线
整合文本分块、命名实体识别、实体消歧、关系抽取等步骤
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    config, ensure_output_files_exist,
    process_all_chunk_files, process_all_ner_files,
    run_disambiguate_on_all_files, run_relation_extraction_on_all
)

class KnowledgeGraphPipeline:
    """知识图谱构建流水线"""
    
    def __init__(self):
        """初始化流水线"""
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        print("🔧 正在初始化目录结构...")
        ensure_output_files_exist()
        print("✅ 目录结构初始化完成")
    
    def run_full_pipeline(self, 
                         max_file_workers: int = 2,
                         max_chunk_workers: int = 4) -> Dict[str, Any]:
        """运行完整的知识图谱构建流水线"""
        print("🚀 开始运行知识图谱构建流水线...")
        
        results = {
            "success": False,
            "steps_completed": [],
            "errors": [],
            "output_files": {}
        }
        
        try:
            # 步骤1: 文本分块
            print("\n" + "="*50)
            print("📝 步骤1: 文本分块处理")
            print("="*50)
            chunk_results = process_all_chunk_files()
            if chunk_results:
                results["steps_completed"].append("chunking")
                results["output_files"]["chunks"] = chunk_results
                print(f"✅ 文本分块完成，处理了 {len(chunk_results)} 个文件")
            else:
                raise Exception("文本分块失败")
            
            # 步骤2: 命名实体识别
            print("\n" + "="*50)
            print("🏷️ 步骤2: 命名实体识别")
            print("="*50)
            ner_results = process_all_ner_files(max_file_workers, max_chunk_workers)
            if ner_results:
                results["steps_completed"].append("ner")
                results["output_files"]["ner"] = ner_results
                print(f"✅ 命名实体识别完成")
            else:
                raise Exception("命名实体识别失败")
            
            # 步骤3: 实体消歧
            print("\n" + "="*50)
            print("🔗 步骤3: 实体消歧处理")
            print("="*50)
            disambig_result = run_disambiguate_on_all_files()
            if disambig_result:
                results["steps_completed"].append("disambiguation")
                results["output_files"]["disambiguation"] = disambig_result
                print(f"✅ 实体消歧完成")
            else:
                raise Exception("实体消歧失败")
            
            # 步骤4: 关系抽取
            print("\n" + "="*50)
            print("🔗 步骤4: 关系抽取")
            print("="*50)
            relation_result = run_relation_extraction_on_all()
            if relation_result:
                results["steps_completed"].append("relation_extraction")
                results["output_files"]["relations"] = relation_result
                print(f"✅ 关系抽取完成")
            else:
                raise Exception("关系抽取失败")
            
            results["success"] = True
            
            # 输出最终统计
            print("\n" + "="*60)
            print("🎉 知识图谱构建流水线执行完成！")
            print("="*60)
            print(f"📊 执行统计:")
            print(f"   ✅ 完成步骤: {', '.join(results['steps_completed'])}")
            print(f"   📁 输出文件:")
            for step, files in results["output_files"].items():
                if isinstance(files, list):
                    print(f"      {step}: {len(files)} 个文件")
                else:
                    print(f"      {step}: {files}")
            print("="*60)
            
        except Exception as e:
            error_msg = f"流水线执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            results["success"] = False
        
        return results
    
    def run_single_step(self, step: str, **kwargs) -> Any:
        """运行单个步骤"""
        print(f"🔄 运行单个步骤: {step}")
        
        if step == "chunking":
            return process_all_chunk_files()
        elif step == "ner":
            max_file_workers = kwargs.get("max_file_workers", 2)
            max_chunk_workers = kwargs.get("max_chunk_workers", 4)
            return process_all_ner_files(max_file_workers, max_chunk_workers)
        elif step == "disambiguation":
            return run_disambiguate_on_all_files()
        elif step == "relation_extraction":
            return run_relation_extraction_on_all()
        else:
            raise ValueError(f"未知的步骤: {step}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="知识图谱构建流水线")
    parser.add_argument("--step", type=str, choices=["chunking", "ner", "disambiguation", "relation_extraction", "full"],
                       default="full", help="要执行的步骤")
    parser.add_argument("--max-file-workers", type=int, default=2, help="文件并发处理数")
    parser.add_argument("--max-chunk-workers", type=int, default=4, help="chunk并发处理数")
    
    args = parser.parse_args()
    
    pipeline = KnowledgeGraphPipeline()
    
    if args.step == "full":
        results = pipeline.run_full_pipeline(
            max_file_workers=args.max_file_workers,
            max_chunk_workers=args.max_chunk_workers
        )
        if results["success"]:
            print("\n🎉 流水线执行成功！")
            sys.exit(0)
        else:
            print("\n❌ 流水线执行失败！")
            for error in results["errors"]:
                print(f"   {error}")
            sys.exit(1)
    else:
        try:
            result = pipeline.run_single_step(
                args.step,
                max_file_workers=args.max_file_workers,
                max_chunk_workers=args.max_chunk_workers
            )
            if result:
                print(f"\n✅ 步骤 {args.step} 执行成功！")
                sys.exit(0)
            else:
                print(f"\n❌ 步骤 {args.step} 执行失败！")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ 步骤 {args.step} 执行出错: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()