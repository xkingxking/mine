import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.modules.question_loader import QuestionLoader
from app.modules.prompt_builder import PromptBuilder
from app.modules.model_client import ModelClient
from app.modules.evaluator.evaluation_manager import EvaluationManager
from app.modules.reporting.report_generator import ReportGenerator
from app.core.config import settings

async def process_questions(
    model_type: str,
    questions_file: str,
    output_dir: Optional[str] = None
) -> None:
    """
    处理题目并生成评估报告
    
    Args:
        model_type: 模型类型（如 'deepseek'）
        questions_file: 题目文件路径
        output_dir: 输出目录（可选）
    """
    try:
        # 1. 加载题目
        print(f"正在加载题目文件: {questions_file}")
        question_loader = QuestionLoader(questions_file)
        questions = question_loader.load_questions()
        print(f"成功加载 {len(questions)} 道题目")
        
        # 2. 构建提示词
        prompt_builder = PromptBuilder()
        
        # 3. 创建模型客户端
        print(f"正在初始化模型: {model_type}")
        # 从 settings 获取 API 密钥和模型名称
        api_key = settings.DEEPSEEK_API_KEY if model_type == "deepseek" else settings.PERSPECTIVE_API_KEY
        model_name = settings.DEEPSEEK_MODEL_NAME if model_type == "deepseek" else "perspective-api"
        
        async with ModelClient(model_type, api_key=api_key, model_name=model_name) as client:
            # 4. 评估响应
            evaluation_manager = EvaluationManager()
            
            # 5. 生成报告
            report_generator = ReportGenerator(output_dir)
            
            results = []
            for i, question in enumerate(questions, 1):
                print(f"正在处理第 {i}/{len(questions)} 题")
                
                # 构建提示词
                prompt = prompt_builder.build_prompt(question)
                
                # 发送到模型并获取响应
                response = await client.send_prompt(prompt)
                
                # 评估响应
                evaluation_results = await evaluation_manager.evaluate_response(
                    model_output=response["content"],
                    standard_answer=question.get("answer", ""),
                    question_type=question["type"]
                )
                
                # 记录结果
                result = {
                    "question_id": question["id"],
                    "question_type": question["type"],
                    "domain": question.get("题目领域", "未知"),
                    "model_output": response["content"],
                    "evaluation_results": evaluation_results
                }
                results.append(result)
            
            # 生成完整报告
            report_data = {
                "model_type": model_type,
                "model_name": client.model.model_name,
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 使用字符串格式
                "total_questions": len(questions),
                "successful_responses": len([r for r in results if "error" not in r]),
                "failed_responses": len([r for r in results if "error" in r]),
                "detailed_results": results,
                "usage_stats": {
                    "total_calls": client.model.total_calls,
                    "total_tokens": client.model.total_tokens
                }
            }
            
            # 生成所有类型的报告
            print("正在生成评估报告...")
            report_generator.generate_all_reports(report_data, model_type)
            print("评估报告生成完成！")
            
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
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
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行主流程
    asyncio.run(process_questions(
        model_type=args.model,
        questions_file=args.questions,
        output_dir=str(output_dir)
    ))

if __name__ == "__main__":
    main() 