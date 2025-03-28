from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.modules.question_generator.generator import QuestionGenerator
from app.modules.validator.validator import ModelValidator
from app.modules.report_generator.report import ReportGenerator

api_router = APIRouter()

# 初始化各个模块
question_generator = QuestionGenerator()
model_validator = ModelValidator()
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
    """对题目进行变形"""
    try:
        transformed = question_generator.transform_question(
            question, transform_type
        )
        return {
            "status": "success",
            "data": transformed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/validate")
async def validate_model_response(
    model_input: str,
    model_output: str,
    validation_types: List[str] = None
) -> Dict[str, Any]:
    """验证模型输出"""
    try:
        results = model_validator.validate_response(
            model_input, model_output, validation_types
        )
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