import asyncio
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import json

from app.modules.question_loader import QuestionLoader
from app.modules.prompt_builder import PromptBuilder
from app.modules.model_client import ModelClient
from app.modules.evaluator.evaluation_manager import EvaluationManager
from app.modules.reporting.report_generator import ReportGenerator
from app.core.config import settings

# 加载环境变量
load_dotenv()

async def get_model_output(question: str, model_name: str, proxy: str = None) -> str:
    """获取模型输出
    
    Args:
        question (str): 问题内容
        model_name (str): 模型类型（如 'deepseek'）
        proxy (str, optional): 代理服务器地址
        
    Returns:
        str: 模型输出
    """
    try:
        print(f"\n=== 开始获取模型输出 ===")
        print(f"问题: {question[:100]}...")
        print(f"模型类型: {model_name}")
        
        # 获取API密钥和实际模型名称
        api_key = os.getenv('DEEPSEEK_API_KEY')
        actual_model_name = os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-chat')
        
        if not api_key:
            raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
            
        print(f"使用模型: {actual_model_name}")
        
        # 构建提示词
        prompt_builder = PromptBuilder()
        # 添加必要的字段
        question_data = {
            "question": question,
            "type": "general",  # 默认类型
            "answer": "",  # 空答案
            "题目领域": "通用",  # 默认领域
            "难度级别": "中等",  # 默认难度
            "测试指标": "通用能力"  # 默认指标
        }
        prompt = prompt_builder.build_prompt(question_data)
        
        # 创建模型客户端
        async with ModelClient(model_name, api_key=api_key, model_name=actual_model_name, proxy=proxy) as client:
            # 发送到模型并获取响应
            response = await client.send_prompt(prompt)
            print("成功获取模型输出")
            print("=== 模型输出获取完成 ===\n")
            return response["content"]
            
    except Exception as e:
        print(f"获取模型输出时出错: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise

async def process_questions(
    questions_file: str,
    output_dir: str,
    model_name: str,
    proxy: str = None
):
    """处理问题并生成评估报告"""
    try:
        # 使用QuestionLoader加载问题
        print(f"\n=== 开始加载问题 ===")
        question_loader = QuestionLoader(questions_file)
        questions = question_loader.load_questions()
        metadata = question_loader.get_metadata()
        
        print(f"成功加载 {len(questions)} 个问题")
        if metadata:
            print(f"题目元数据: {metadata}")
        
        # 初始化评估管理器
        evaluation_manager = EvaluationManager(proxy=proxy)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{model_name}_{timestamp}_full.json")
        
        # 处理每个问题
        results = []
        for i, question in enumerate(questions, 1):
            try:
                print(f"\n=== 处理第 {i}/{len(questions)} 个问题 ===")
                print(f"题目ID: {question.get('id', 'N/A')}")
                
                # 统一题目字段
                if isinstance(question, str):
                    question = {
                        "question": question,
                        "answer": "",
                        "type": "general",
                        "题目领域": "通用",
                        "难度级别": "中等",
                        "测试指标": "通用能力"
                    }
                else:
                    # 确保所有必要字段都存在
                    question = {
                        "question": question.get("question", question.get("问题", "")),
                        "answer": question.get("answer", question.get("答案", "")),
                        "type": question.get("type", question.get("类型", "general")),
                        "题目领域": question.get("题目领域", question.get("domain", "通用")),
                        "难度级别": question.get("难度级别", question.get("difficulty", "中等")),
                        "测试指标": question.get("测试指标", question.get("metric", "通用能力"))
                    }
                
                print(f"处理题目: {question['question'][:100]}...")
                print(f"题目类型: {question['type']}")
                print(f"题目领域: {question['题目领域']}")
                print(f"难度级别: {question['难度级别']}")
                
                # 获取模型输出
                model_output = await get_model_output(
                    question["question"],
                    model_name,
                    proxy
                )
                
                # 评估模型输出
                evaluation_results = await evaluation_manager.evaluate_response(
                    model_output,
                    question["answer"],
                    question["type"]
                )
                
                # 获取评估摘要
                evaluation_summary = evaluation_manager.get_evaluation_summary(evaluation_results)
                
                # 构建结果
                result = {
                    "id": question.get("id", f"Q{i}"),
                    "question": question["question"],
                    "model_output": model_output,
                    "standard_answer": question["answer"],
                    "question_type": question["type"],
                    "domain": question["题目领域"],
                    "difficulty": question["难度级别"],
                    "metric": question["测试指标"],
                    "choices": question.get("choices", {}),
                    "safety_score": evaluation_results["safety"]["safety_score"],
                    "accuracy_score": evaluation_results["accuracy"]["accuracy_score"],
                    "overall_score": evaluation_summary["overall_score"],
                    "safety_status": evaluation_results["safety"].get("evaluation_status", "completed"),
                    "accuracy_status": evaluation_results["accuracy"].get("evaluation_status", "completed"),
                    "is_safe": evaluation_results["safety"]["is_safe"],
                    "is_accurate": evaluation_results["accuracy"]["is_accurate"]
                }
                
                results.append(result)
                print(f"问题 {i} 处理完成")
                
            except Exception as e:
                print(f"处理问题时出错: {str(e)}")
                print(f"问题内容: {question.get('question', '未知')}")
                print(f"错误类型: {type(e)}")
                import traceback
                print(f"错误堆栈: {traceback.format_exc()}")
                continue
        
        # 保存结果
        print("\n=== 保存评估结果 ===")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"评估结果已保存到: {output_file}")
        print(f"成功处理 {len(results)}/{len(questions)} 个问题")
        print("=== 处理完成 ===\n")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="大语言模型评估工具")
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="模型类型（如 'qwen'）"
    )
    parser.add_argument(
        "--questions",
        type=str,
        required=True,
        help="题目文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出目录（可选）"
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default="http://127.0.0.1:8453",
        help="代理服务器地址（可选，默认：http://127.0.0.1:8453）"
    )
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行主流程
    asyncio.run(process_questions(
        questions_file=args.questions,
        output_dir=str(output_dir),
        model_name=args.model,
        proxy=args.proxy
    ))

if __name__ == "__main__":
    main() 