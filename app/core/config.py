from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Settings(BaseModel):
    """应用配置"""
    # 项目配置
    PROJECT_NAME: str
    VERSION: str
    DESCRIPTION: str
    
    # API配置
    API_V1_STR: str
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # 数据库配置
    DATABASE_URL: str
    
    # 模型配置
    SUPPORTED_MODELS: List[str]
    
    # 题库配置
    MIN_QUESTIONS: int
    VALIDATION_THRESHOLD: float
    
    # Redis配置
    REDIS_URL: Optional[str]
    
    # API密钥
    PERSPECTIVE_API_KEY: Optional[str]
    
    # 日志配置
    LOG_LEVEL: str
    LOG_FILE: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 