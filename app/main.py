import asyncio
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
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
            "type": "default",  # 默认类型
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

async def process_questions(questions: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    """处理问题列表"""
    try:
        # 初始化评估管理器和报告生成器
        evaluation_manager = EvaluationManager()
        report_generator = ReportGenerator(args.output if args.output else settings.OUTPUT_DIR)
        
        # 处理每个问题
        for question in questions:
            try:
                # 获取模型输出
                model_output = await get_model_output(
                    question["question"],
                    args.model,
                    args.proxy
                )
                
                # 保存模型输出到问题字典中
                question["model_output"] = model_output
                
                # 评估模型输出
                evaluation_results = await evaluation_manager.evaluate_response(
                    model_output=model_output,
                    standard_answer=question["answer"],
                    domain=question.get("题目领域", "通用")
                )
                
                # 打印评估结果
                print(f"\n评估结果:")
                print(f"准确性分数: {evaluation_results['accuracy']['accuracy_score']}")
                print(f"是否准确: {evaluation_results['accuracy']['is_accurate']}")
                
            except Exception as e:
                print(f"处理问题时出错: {str(e)}")
                continue
        
        # 获取评估摘要
        evaluation_summary = evaluation_manager.get_evaluation_summary()
        
        # 打印评估摘要
        print("\n=== 评估摘要 ===")
        print(f"总体得分: {evaluation_summary['overall_score']:.2%}")
        for domain, scores in evaluation_summary["domain_scores"].items():
            print(f"{domain}得分: {scores['score']:.2%} ({scores['correct_answers']}/{scores['total_questions']})")
        
        # 生成报告
        report = report_generator.generate_report(
            evaluation_summary=evaluation_summary,
            model_name=args.model,
            questions=questions
        )
        
        # 保存报告
        report_path = report_generator.save_report(report, args.model)
        print(f"\n报告已保存到: {report_path}")
        
    except Exception as e:
        print(f"处理问题时出错: {str(e)}")
        raise

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
    
    # 加载题目
    question_loader = QuestionLoader(args.questions)
    questions = question_loader.load_questions()
    
    # 运行主流程
    asyncio.run(process_questions(questions, args))

if __name__ == "__main__":
    main() 