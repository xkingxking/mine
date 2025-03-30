from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class BaseModel(ABC):
    """大模型基类，定义所有模型必须实现的基本接口"""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        初始化模型
        
        Args:
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.model_name = model_name
        self.config = kwargs
        self.last_call_time = None
        self.total_tokens = 0
        self.total_calls = 0
    
    @abstractmethod
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
            temperature (float): 温度参数，控制输出的随机性
            max_tokens (Optional[int]): 最大生成token数
            
        Returns:
            str: 模型生成的响应
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        pass
    
    def update_usage_stats(self, tokens: int):
        """
        更新使用统计
        
        Args:
            tokens (int): 本次调用使用的token数
        """
        self.total_tokens += tokens
        self.total_calls += 1
        self.last_call_time = datetime.now()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Returns:
            Dict[str, Any]: 使用统计信息
        """
        return {
            "total_tokens": self.total_tokens,
            "total_calls": self.total_calls,
            "last_call_time": self.last_call_time,
            "average_tokens_per_call": self.total_tokens / self.total_calls if self.total_calls > 0 else 0
        }
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        验证API密钥是否有效
        
        Returns:
            bool: API密钥是否有效
        """
        pass
    
    @abstractmethod
    async def get_model_capabilities(self) -> Dict[str, Any]:
        """
        获取模型能力信息
        
        Returns:
            Dict[str, Any]: 模型能力信息，如支持的最大token数、支持的模型版本等
        """
        pass 