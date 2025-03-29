from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseEvaluator(ABC):
    """评估器基类，定义所有评估器的基本接口"""
    
    @abstractmethod
    def evaluate(self, model_output: str, standard_answer: str) -> Dict[str, Any]:
        """
        执行评估
        
        Args:
            model_output (str): 模型输出
            standard_answer (str): 标准答案
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        pass
    
    @abstractmethod
    def generate_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成评估报告
        
        Args:
            evaluation_results (Dict[str, Any]): 评估结果
            
        Returns:
            Dict[str, Any]: 评估报告
        """
        pass 