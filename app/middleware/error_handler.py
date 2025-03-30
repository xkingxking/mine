from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Callable
import logging
from app.schemas.response import ResponseModel

logger = logging.getLogger(__name__)

class ErrorHandler:
    """错误处理中间件"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content=ResponseModel(
                    status="error",
                    error=str(e),
                    message="服务器内部错误"
                ).dict()
            )

def setup_error_handling(app):
    """设置错误处理"""
    app.middleware("http")(ErrorHandler()) 