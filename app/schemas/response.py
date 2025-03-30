"""
响应模型
"""
from typing import Any, Optional
from pydantic import BaseModel

class ResponseModel(BaseModel):
    status: str
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str 