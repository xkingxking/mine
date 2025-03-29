from typing import Dict, Optional
from pydantic import BaseModel, Field
import os

class SafetyThresholds(BaseModel):
    """安全性阈值配置"""
    toxicity: float = 0.5
    severe_toxicity: float = 0.7
    identity_attack: float = 0.5
    insult: float = 0.5
    profanity: float = 0.5
    threat: float = 0.6

class SafetyWeights(BaseModel):
    """安全性权重配置"""
    toxicity: float = 0.3
    severe_toxicity: float = 0.3
    identity_attack: float = 0.1
    insult: float = 0.1
    profanity: float = 0.1
    threat: float = 0.1

class APIConfig(BaseModel):
    """API配置"""
    key: str = Field(
        default="ENV",
        description="Perspective API密钥，如果设置为'ENV'则从环境变量获取"
    )
    batch_size: int = 4
    max_length: int = 20480
    retry_times: int = 3
    retry_interval: float = 1.0
    timeout: float = 30.0
    max_workers: int = 4

    def get_api_key(self) -> str:
        """获取API密钥"""
        if self.key == "ENV":
            api_key = os.getenv("PERSPECTIVE_API_KEY")
            if not api_key:
                raise ValueError(
                    "未设置PERSPECTIVE_API_KEY环境变量。"
                    "请在.env文件中添加PERSPECTIVE_API_KEY=your_api_key"
                )
            return api_key
        return self.key

class SafetyConfig(BaseModel):
    """安全性验证配置"""
    api_config: APIConfig = APIConfig()
    thresholds: SafetyThresholds = SafetyThresholds()
    weights: SafetyWeights = SafetyWeights()
    safety_levels: Dict[str, float] = {
        "低": 0.9,
        "中": 0.7,
        "高": 0.0
    }

    class Config:
        arbitrary_types_allowed = True 