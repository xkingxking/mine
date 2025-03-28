from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "大模型性能与安全观测平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "用于观测和评估大语言模型性能与安全性的综合平台"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # 模型配置
    SUPPORTED_MODELS: List[str] = [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-2",
        "llama-2",
        "chatglm3"
    ]
    
    # 题库配置
    MIN_QUESTIONS: int = 500
    VALIDATION_THRESHOLD: float = 0.9
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 