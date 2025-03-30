from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置类"""
    
    # 项目基本信息
    PROJECT_NAME: str = "大模型性能与安全观测平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "用于观测和评估大语言模型的性能与安全性"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # 模型配置
    SUPPORTED_MODELS: List[str] = ["gpt-3.5-turbo", "gpt-4", "claude-2", "llama-2", "chatglm3"]
    
    # 题库配置
    MIN_QUESTIONS: int = 500
    VALIDATION_THRESHOLD: float = 0.9
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API密钥配置
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    PERSPECTIVE_API_KEY: str = ""
    
    # 模型配置
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"
    OPENAI_MODEL_NAME: str = "gpt-4"
    GEMINI_MODEL_NAME: str = "gemini-pro"
    
    # API基础URL
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings()

def get_model_config(model_type: str) -> Dict[str, Any]:
    """获取指定模型的配置"""
    settings = get_settings()
    config = {
        "api_key": getattr(settings, f"{model_type.upper()}_API_KEY", ""),
        "model_name": getattr(settings, f"{model_type.upper()}_MODEL_NAME", ""),
        "api_base": getattr(settings, f"{model_type.upper()}_API_BASE", "")
    }
    return config 