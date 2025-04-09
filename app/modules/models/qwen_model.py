import aiohttp
from typing import Dict, Any, Optional
from .base_model import BaseModel
from app.core.config import get_model_config

class QwenModel(BaseModel):
    """通义千问大模型实现"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        初始化通义千问模型
        
        Args:
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
        """
        # 获取模型配置
        config = get_model_config("qwen")
        
        # 使用提供的参数覆盖配置
        api_key = api_key or config["api_key"]
        model_name = model_name or config["model_name"]
        api_base = kwargs.get("api_base", config["api_base"])
        
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
        生成通义千问模型响应
        
        Args:
            prompt (str): 用户提示词
            system_prompt (Optional[str]): 系统提示词
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大生成token数
            
        Returns:
            str: 模型生成的响应
            
        Raises:
            Exception: API调用失败时抛出
        """
        if not self.api_key:
            raise ValueError("未设置通义千问 API Key，请在环境变量中设置 QWEN_API_KEY")
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 更新使用统计
                    self.update_usage_stats(result.get("usage", {}).get("total_tokens", 0))
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"通义千问 API调用失败: {error_text}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取通义千问模型信息"""
        return {
            "model_type": "qwen",
            "model_name": self.model_name,
            "api_base": self.api_base,
            "capabilities": await self.get_model_capabilities()
        }
    
    async def validate_api_key(self) -> bool:
        """验证通义千问 API密钥"""
        if not self.api_key:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/models",
                    headers=self.headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_model_capabilities(self) -> Dict[str, Any]:
        """获取通义千问模型能力信息"""
        return {
            "max_tokens": 32768,
            "supported_models": ["qwen-max", "qwen-plus", "qwen-turbo"],
            "features": [
                "chat_completion",
                "function_calling",
                "streaming"
            ]
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass 