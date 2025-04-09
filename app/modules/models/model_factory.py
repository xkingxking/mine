from typing import Dict, Type, Optional
from .base_model import BaseModel
from .chatgpt_model import ChatGPTModel
from .deepseek_model import DeepseekModel
from .doubao_model import DoubaoModel
from .qwen_model import QwenModel

class ModelFactory:
    """模型工厂类，用于创建和管理不同的模型实例"""
    
    _models: Dict[str, Type[BaseModel]] = {}
    
    @classmethod
    def register_model(cls, model_type: str, model_class: Type[BaseModel]):
        """
        注册新的模型类型
        
        Args:
            model_type (str): 模型类型标识符
            model_class (Type[BaseModel]): 模型类
        """
        cls._models[model_type] = model_class
    
    @classmethod
    def create_model(cls, 
                    model_type: str, 
                    api_key: str,
                    model_name: str,
                    **kwargs) -> Optional[BaseModel]:
        """
        创建模型实例
        
        Args:
            model_type (str): 模型类型标识符
            api_key (str): API密钥
            model_name (str): 模型名称
            **kwargs: 其他配置参数
            
        Returns:
            Optional[BaseModel]: 模型实例，如果类型不存在则返回None
            
        Raises:
            ValueError: 当模型类型未注册时抛出
        """
        if model_type not in cls._models:
            raise ValueError(f"未注册的模型类型: {model_type}")
        
        # 将 api_key 添加到 kwargs 中
        kwargs["api_key"] = api_key
        
        # 创建模型实例
        return cls._models[model_type](model_name=model_name, **kwargs)
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Type[BaseModel]]:
        """
        获取所有可用的模型类型
        
        Returns:
            Dict[str, Type[BaseModel]]: 可用的模型类型字典
        """
        return cls._models.copy()
    
    @classmethod
    def is_model_available(cls, model_type: str) -> bool:
        """
        检查模型类型是否可用
        
        Args:
            model_type (str): 模型类型标识符
            
        Returns:
            bool: 模型类型是否可用
        """
        return model_type in cls._models


