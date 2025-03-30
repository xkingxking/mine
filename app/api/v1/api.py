from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.modules.question_generator.generator import QuestionGenerator
from app.modules.evaluator.safety_evaluator import SafetyEvaluator
from app.modules.transformer.transformer import QuestionTransformer
from app.modules.transformer.evaluator import TransformationEvaluator
from app.modules.report_generator.report import ReportGenerator
from app.middleware.error_handler import setup_error_handling
from app.schemas.response import ResponseModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionTransform

router = APIRouter()

# 初始化组件
question_generator = QuestionGenerator()
safety_evaluator = SafetyEvaluator()
question_transformer = QuestionTransformer()
transformation_evaluator = TransformationEvaluator()
report_generator = ReportGenerator()

# 设置错误处理
setup_error_handling(router)

@router.post("/questions/generate", response_model=ResponseModel)
async def generate_questions(count: int = 500):
    """生成题目"""
    questions = await question_generator.generate_questions(count)
    return ResponseModel(
        status="success",
        data=questions,
        message=f"成功生成{count}道题目"
    )

@router.post("/questions/transform", response_model=ResponseModel)
async def transform_question(transform_data: QuestionTransform):
    """变形题目"""
    transformed = await question_transformer.transform(
        transform_data.question.dict(),
        transform_data.transform_type
    )
    return ResponseModel(
        status="success",
        data=transformed,
        message="题目变形成功"
    )

@router.post("/questions/transform/evaluate", response_model=ResponseModel)
async def evaluate_transformation(
    original_question: QuestionCreate,
    transformed_question: QuestionCreate
):
    """评估题目变形质量"""
    results = await transformation_evaluator.evaluate(
        original_question.dict(),
        transformed_question.dict()
    )
    return ResponseModel(
        status="success",
        data=results,
        message="变形评估完成"
    )

@router.post("/evaluate", response_model=ResponseModel)
async def evaluate_model(model_output: Dict[str, Any]):
    """评估模型输出"""
    results = await safety_evaluator.evaluate(model_output)
    return ResponseModel(
        status="success",
        data=results,
        message="模型评估完成"
    )

@router.post("/reports/generate", response_model=ResponseModel)
async def generate_report(evaluation_results: Dict[str, Any]):
    """生成评估报告"""
    report = await report_generator.generate_report(evaluation_results)
    return ResponseModel(
        status="success",
        data=report,
        message="报告生成成功"
    )

@router.get("/reports/{report_id}", response_model=ResponseModel)
async def get_report(report_id: str):
    """获取评估报告"""
    report = await report_generator.get_report(report_id)
    return ResponseModel(
        status="success",
        data=report,
        message="获取报告成功"
    )

@router.get("/reports/{report_id}/export", response_model=ResponseModel)
async def export_report(report_id: str, format: str = "pdf"):
    """导出评估报告"""
    file_path = await report_generator.export_report(report_id, format)
    return ResponseModel(
        status="success",
        data={"file_path": file_path},
        message="报告导出成功"
    ) 