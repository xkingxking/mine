import aiohttp
from typing import Dict, Any, Optional
from .base_model import BaseModel
from app.core.config import get_model_config

class PerspectiveModel(BaseModel):
    """Perspective API 模型实现"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        初始化 Perspective 模型
        
        Args:
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
        """
        # 获取模型配置
        config = get_model_config("perspective")
        
        # 使用提供的参数覆盖配置
        api_key = api_key or config["api_key"]
        model_name = model_name or config["model_name"]
        api_base = kwargs.get("api_base", "https://commentanalyzer.googleapis.com/v1alpha1")
        
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = None) -> str:
        """
        生成模型响应（Perspective API 不支持生成响应）
        
        Args:
            prompt (str): 用户提示词
            system_prompt (Optional[str]): 系统提示词（不使用）
            temperature (float): 温度参数（不使用）
            max_tokens (Optional[int]): 最大生成token数（不使用）
            
        Returns:
            str: 空字符串，因为 Perspective API 不支持生成响应
        """
        return ""
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        return {
            "model_name": self.model_name,
            "api_base": self.api_base,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens
        }
    
    async def validate_api_key(self) -> bool:
        """
        验证API密钥
        
        Returns:
            bool: API密钥是否有效
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 发送一个简单的测试请求
                test_text = "Hello, this is a test message."
                response = await self.check_safety(test_text)
                return response is not None
        except Exception:
            return False
    
    async def check_safety(self, text: str) -> float:
        """
        检查文本的安全性
        
        Args:
            text (str): 要检查的文本
            
        Returns:
            float: 安全分数（0-1之间，1表示最安全）
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/comments:analyze"
                payload = {
                    "comment": {"text": text},
                    "requestedAttributes": {"TOXICITY": {}}
                }
                
                async with session.post(url, json=payload, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 获取毒性分数并转换为安全分数（1 - 毒性分数）
                        toxicity_score = result.get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {}).get("value", 0)
                        return 1 - toxicity_score
                    else:
                        raise Exception(f"API请求失败: {response.status}")
        except Exception as e:
            raise Exception(f"安全检查失败: {str(e)}") 