import logging
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings

def setup_logging():
    """配置日志记录"""
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print(f"创建日志目录: {log_dir}")
        os.makedirs(log_dir)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, settings.LOG_FILE),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 配置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    return root_logger

logger = setup_logging() 