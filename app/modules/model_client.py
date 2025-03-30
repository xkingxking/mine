import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.modules.models.model_factory import ModelFactory

class ModelClient:
    """模型客户端，用于与模型API交互"""
    
    def __init__(self, 
                 model_type: str, 
                 api_key: str,
                 model_name: str,
                 max_retries: int = 3, 
                 retry_delay: float = 1.0):
        """
        初始化模型客户端
        
        Args:
            model_type (str): 模型类型
            api_key (str): API密钥
            model_name (str): 模型名称
            max_retries (int): 最大重试次数
            retry_delay (float): 重试延迟（秒）
        """
        self.model = ModelFactory.create_model(
            model_type=model_type,
            api_key=api_key,
            model_name=model_name
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = None
    
    async def __aenter__(self):
        """创建异步上下文管理器"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """关闭异步上下文管理器"""
        if self.session:
            await self.session.close()
    
    async def send_prompt(self, 
                         prompt: Dict[str, str],
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        发送提示词到模型并获取响应
        
        Args:
            prompt (Dict[str, str]): 包含系统提示词和用户提示词的字典
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大生成token数
            
        Returns:
            Dict[str, Any]: 模型响应
        """
        for attempt in range(self.max_retries):
            try:
                # 获取模型响应
                response = await self.model.generate_response(
                    prompt=prompt["user"],
                    system_prompt=prompt["system"],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # 记录使用统计
                self.model.update_usage_stats(
                    len(prompt["user"]) + len(prompt["system"])
                )
                
                return {
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    async def validate_api_key(self) -> bool:
        """
        验证API密钥
        
        Returns:
            bool: API密钥是否有效
        """
        return await self.model.validate_api_key()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计
        
        Returns:
            Dict[str, Any]: 使用统计信息
        """
        return self.model.get_usage_stats() 