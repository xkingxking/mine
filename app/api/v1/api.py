from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.modules.question_generator.generator import QuestionGenerator
from app.modules.evaluator.safety_evaluator import SafetyEvaluator
from app.modules.transformer.transformer import QuestionTransformer
from app.modules.transformer.evaluator import TransformationEvaluator
from app.modules.report_generator.report import ReportGenerator

api_router = APIRouter()

# 初始化各个模块
question_generator = QuestionGenerator()
safety_evaluator = SafetyEvaluator()
question_transformer = QuestionTransformer()
transformation_evaluator = TransformationEvaluator()
report_generator = ReportGenerator()

@api_router.post("/questions/generate")
async def generate_questions(count: int = 500) -> Dict[str, Any]:
    """生成测试题库"""
    try:
        questions = question_generator.generate_questions(count)
        return {
            "status": "success",
            "data": questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/questions/transform")
async def transform_question(
    question: Dict[str, Any],
    transform_type: str
) -> Dict[str, Any]:
    """变形题目
    
    Args:
        question (Dict[str, Any]): 原始题目
        transform_type (str): 变形类型
        
    Returns:
        Dict[str, Any]: 变形后的题目
    """
    try:
        transformed_question = question_transformer.transform(question, transform_type)
        return transformed_question
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/questions/transform/evaluate")
async def evaluate_transformation(
    original_question: Dict[str, Any],
    transformed_question: Dict[str, Any]
) -> Dict[str, Any]:
    """评估题目变形质量
    
    Args:
        original_question (Dict[str, Any]): 原始题目
        transformed_question (Dict[str, Any]): 变形后的题目
        
    Returns:
        Dict[str, Any]: 评估报告
    """
    try:
        evaluation_results = transformation_evaluator.evaluate(
            original_question,
            transformed_question
        )
        report = transformation_evaluator.generate_report(evaluation_results)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evaluate")
async def evaluate_model_response(
    model_input: str,
    model_output: str,
    evaluation_types: List[str] = None
) -> Dict[str, Any]:
    """评估模型输出"""
    try:
        results = safety_evaluator.evaluate(model_output)
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/report/generate")
async def generate_report(
    test_results: Dict[str, Any],
    report_type: str = "comprehensive"
) -> Dict[str, Any]:
    """生成测试报告"""
    try:
        report = report_generator.generate_report(
            test_results, report_type
        )
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/report/export")
async def export_report(
    report: Dict[str, Any],
    format: str = "pdf"
) -> Dict[str, Any]:
    """导出报告"""
    try:
        file_path = report_generator.export_report(report, format)
        return {
            "status": "success",
            "data": {"file_path": file_path}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 