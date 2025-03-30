from pydantic import BaseModel, Field
from typing import Any, Optional

class ResponseModel(BaseModel):
    """统一响应模型"""
    status: str = Field(..., description="响应状态")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {"result": "some data"},
                "message": "操作成功"
            }
        } 