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
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    
    # 数据库配置
    DATABASE_URL: str
    
    # 模型配置
    SUPPORTED_MODELS: List[str]
    MIN_QUESTIONS: int = 500
    VALIDATION_THRESHOLD: float = 0.9
    
    # Redis配置
    REDIS_URL: str
    
    # API Keys
    PERSPECTIVE_API_KEY: str
    DEEPSEEK_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    DOUBAO_API_KEY: str
    QWEN_API_KEY: str
    LLAMA_API_KEY: str

    
    # 模型名称
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"
    OPENAI_MODEL_NAME: str = "gpt-4"
    GEMINI_MODEL_NAME: str = "gemini-pro"
    DOUBAO_MODEL_NAME: str = "doubao-1.5-pro-32k-250115"
    QWEN_MODEL_NAME: str = "qwen-max"
    LLAMA_MODEL_NAME: str = "llama3.3-70b-instruct"

    
    # API基础URL
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1"
    DOUBAO_API_BASE: str = "https://ark.cn-beijing.volces.com/api/v3"
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLAMA_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # 输出目录
    OUTPUT_DIR: str = "app/out"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置"""
    return Settings()

# 创建全局配置实例
settings = get_settings()

def get_model_config(model_type: str) -> Dict[str, Any]:
    """获取指定模型的配置"""
    settings = get_settings()
    config = {
        "api_key": getattr(settings, f"{model_type.upper()}_API_KEY", ""),
        "model_name": getattr(settings, f"{model_type.upper()}_MODEL_NAME", ""),
        "api_base": getattr(settings, f"{model_type.upper()}_API_BASE", "")
    }
    return config 