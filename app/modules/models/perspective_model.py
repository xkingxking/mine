import aiohttp
import asyncio
from typing import Dict, Any, Optional
from aiohttp_socks import ProxyConnector
from .base_model import BaseModel
from app.core.config import get_model_config

class PerspectiveModel(BaseModel):
    """Perspective API 模型实现"""
    
    def __init__(self, api_key: str, model_name: str = "perspective-api", **kwargs):
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
        self.total_calls = 0
        self.total_tokens = 0
        
        # 创建支持代理的连接器
        self.connector = ProxyConnector.from_url(
            kwargs.get("proxy", "http://127.0.0.1:8453"),  # 默认使用本地代理
            ssl=False  # 禁用 SSL 验证，如果需要的话
        )
    
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
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """获取模型能力信息"""
        return {
            "model_type": "perspective",
            "capabilities": {
                "text_generation": False,
                "safety_check": True,
                "max_tokens": 0,
                "temperature": 0,
                "top_p": 0
            }
        }
    
    async def validate_api_key(self) -> bool:
        """验证 API 密钥是否有效"""
        try:
            async with aiohttp.ClientSession(connector=self.connector) as session:
                url = f"{self.api_base}/comments:analyze"
                params = {"key": self.api_key}
                data = {
                    "comment": {"text": "test"},
                    "requestedAttributes": {"TOXICITY": {}}
                }
                async with session.post(url, params=params, json=data) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 403:
                        print("API密钥无效")
                        return False
                    else:
                        print(f"API请求失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"API 密钥验证失败: {str(e)}")
            return False
    
    async def check_safety(self, text: str) -> float:
        """检查文本安全性"""
        try:
            async with aiohttp.ClientSession(connector=self.connector) as session:
                url = f"{self.api_base}/comments:analyze"
                params = {"key": self.api_key}
                data = {
                    "comment": {"text": text},
                    "requestedAttributes": {"TOXICITY": {}}
                }
                async with session.post(url, params=params, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        toxicity_score = result.get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {}).get("value", 0)
                        self.total_calls += 1
                        return toxicity_score
                    print(f"安全检查失败，状态码: {response.status}")
                    return 1.0  # 如果请求失败，返回最高毒性分数
        except Exception as e:
            print(f"安全检查失败: {str(e)}")
            return 1.0 