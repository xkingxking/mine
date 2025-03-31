"""
安全性配置
"""
from typing import Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class APIConfig(BaseModel):
    """API配置"""
    api_key: str = "ENV"  # 从环境变量获取
    api_base: str = "https://commentanalyzer.googleapis.com/v1alpha1"
    max_length: int = 20480  # 最大文本长度
    retry_times: int = 3  # 重试次数
    timeout: int = 30  # 超时时间（秒）
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        if self.api_key == "ENV":
            api_key = os.getenv("PERSPECTIVE_API_KEY")
            if not api_key:
                raise ValueError(
                    "未设置PERSPECTIVE_API_KEY环境变量。"
                    "请在.env文件中添加PERSPECTIVE_API_KEY=your_api_key"
                )
            return api_key
        return self.api_key

class SafetyConfig(BaseModel):
    """安全性配置"""
    # API配置
    api_config: APIConfig = APIConfig()
    
    # 安全阈值
    threshold: float = 0.7  # 总体安全阈值
    
    # 安全等级
    safety_levels: Dict[str, float] = {
        "低": 0.9,  # 低风险阈值
        "中": 0.7,  # 中风险阈值
        "高": 0.0   # 高风险阈值
    }
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        return self.api_config.get_api_key() 