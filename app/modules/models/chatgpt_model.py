from typing import Dict, Any, Optional
from openai import OpenAI
from .base_model import BaseModel
from app.core.config import get_model_config

class ChatGPTModel(BaseModel):
    """ChatGPT 模型实现"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        初始化 ChatGPT 模型
        
        Args:
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
        """
        # 获取模型配置
        config = get_model_config("openai")
        
        # 使用提供的参数覆盖配置
        api_key = api_key or config["api_key"]
        model_name = model_name or config["model_name"]
        api_base = kwargs.get("api_base", config["api_base"])
        
        super().__init__(api_key, model_name, **kwargs)
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = None) -> str:
        """
        生成模型响应
        
        Args:
            prompt (str): 用户提示词
            system_prompt (Optional[str]): 系统提示词
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大生成token数
            
        Returns:
            str: 模型生成的响应
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            
            # 更新使用统计
            self.update_usage_stats(response.usage.total_tokens)
            
            return content
            
        except Exception as e:
            raise Exception(f"生成响应时出错: {str(e)}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        return {
            "model_type": "chatgpt",
            "model_name": self.model_name,
            "api_base": self.client.base_url,
            "capabilities": await self.get_model_capabilities()
        }
    
    async def validate_api_key(self) -> bool:
        """
        验证API密钥
        
        Returns:
            bool: API密钥是否有效
        """
        if not self.api_key:
            return False
            
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
    
    async def get_model_capabilities(self) -> Dict[str, Any]:
        """
        获取模型能力信息
        
        Returns:
            Dict[str, Any]: 模型能力信息
        """
        return {
            "max_tokens": 4096,
            "supported_models": ["gpt-3.5-turbo", "gpt-4"],
            "features": [
                "chat_completion",
                "function_calling",
                "streaming"
            ]
        } 