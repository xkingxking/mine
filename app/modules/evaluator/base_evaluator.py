from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseValidator(ABC):
    """验证器基类，定义所有验证器的基本接口"""
    
    @abstractmethod
    def validate(self, model_output: str, standard_answer: str) -> Dict[str, Any]:
        """
        执行验证
        
        Args:
            model_output (str): 模型输出
            standard_answer (str): 标准答案
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass
    
    @abstractmethod
    def generate_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成验证报告
        
        Args:
            validation_results (Dict[str, Any]): 验证结果
            
        Returns:
            Dict[str, Any]: 验证报告
        """
        pass 