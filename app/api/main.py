from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
from pathlib import Path

from app.modules.question_loader import QuestionLoader
from app.modules.evaluator.evaluation_manager import EvaluationManager
from app.modules.reporting.report_generator import ReportGenerator
from app.core.config import settings

app = FastAPI(title="LLM Evaluation API")

# 配置静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """返回前端页面"""
    return {"message": "请访问 /static/index.html"}

class EvaluationRequest(BaseModel):
    model_name: str
    dataset_path: str
    proxy: Optional[str] = None

class EvaluationResponse(BaseModel):
    status: str
    report_path: Optional[str] = None
    error: Optional[str] = None

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_model(request: EvaluationRequest):
    """评估模型接口"""
    try:
        # 检查数据集文件是否存在
        dataset_path = Path(request.dataset_path)
        if not dataset_path.exists():
            raise HTTPException(status_code=400, detail="数据集文件不存在")
        
        # 加载问题
        question_loader = QuestionLoader(str(dataset_path))
        questions = question_loader.load_questions()
        
        # 初始化评估管理器和报告生成器
        evaluation_manager = EvaluationManager()
        report_generator = ReportGenerator(settings.OUTPUT_DIR)
        
        # 处理每个问题
        for question in questions:
            try:
                # 获取模型输出
                model_output = await get_model_output(
                    question["question"],
                    request.model_name,
                    request.proxy
                )
                
                # 保存模型输出
                question["model_output"] = model_output
                
                # 评估模型输出
                await evaluation_manager.evaluate_response(
                    model_output=model_output,
                    standard_answer=question["answer"],
                    domain=question.get("题目领域", "通用")
                )
                
            except Exception as e:
                print(f"处理问题时出错: {str(e)}")
                continue
        
        # 获取评估摘要
        evaluation_summary = evaluation_manager.get_evaluation_summary()
        
        # 生成报告
        report = report_generator.generate_report(
            evaluation_summary=evaluation_summary,
            model_name=request.model_name,
            questions=questions
        )
        
        # 保存报告
        report_path = report_generator.save_report(report, request.model_name)
        
        return EvaluationResponse(
            status="success",
            report_path=str(report_path)
        )
        
    except Exception as e:
        return EvaluationResponse(
            status="error",
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 