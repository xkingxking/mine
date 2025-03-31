from typing import Dict, Any
from .safety_evaluator import SafetyEvaluator
from .accuracy_evaluator import AccuracyEvaluator
from .choice_evaluator import ChoiceEvaluator

class EvaluationManager:
    """评估管理器，用于管理不同类型的评估"""
    
    def __init__(self, proxy: str = None):
        """
        初始化评估管理器
        
        Args:
            proxy (str, optional): 代理服务器地址
        """
        self.proxy = proxy
        self.evaluators = {
            "safety": SafetyEvaluator(proxy=proxy),
            "accuracy": AccuracyEvaluator(),
            "choice": ChoiceEvaluator()
        }
    
    async def evaluate_response(
        self,
        model_output: str,
        standard_answer: str = None,
        question_type: str = "general"
    ) -> Dict[str, Any]:
        """评估模型响应"""
        try:
            results = {}
            
            # 1. 安全性评估
            print("正在进行安全性评估...")
            results["safety"] = await self.evaluators["safety"].evaluate(model_output)
            
            # 2. 准确性评估
            print("正在进行准确性评估...")
            results["accuracy"] = self.evaluators["accuracy"].evaluate(
                model_output=model_output,
                standard_answer=standard_answer
            )
            
            # 3. 计算总体得分
            results["overall_score"] = self._calculate_overall_score(results)
            
            return results
            
        except Exception as e:
            print(f"评估过程中出现错误: {str(e)}")
            return {
                "error": str(e),
                "safety": {"safety_score": 0.0, "is_safe": False},
                "accuracy": {"accuracy_score": 0.0},
                "overall_score": 0.0
            }
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """
        计算总体评分
        
        Args:
            results (Dict[str, Any]): 各项评估结果
            
        Returns:
            float: 总体评分
        """
        weights = {
            "safety": 0.4,
            "accuracy": 0.6
        }
        
        overall_score = (
            results["safety"]["safety_score"] * weights["safety"] +
            results["accuracy"]["accuracy_score"] * weights["accuracy"]
        )
        
        return round(overall_score, 2)
    
    def get_evaluation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取评估摘要
        
        Args:
            results (Dict[str, Any]): 评估结果
            
        Returns:
            Dict[str, Any]: 评估摘要
        """
        return {
            "overall_score": results["overall_score"],
            "safety_score": results["safety"]["safety_score"],
            "accuracy_score": results["accuracy"]["accuracy_score"],
            "is_safe": results["safety"]["is_safe"],
            "is_accurate": results["accuracy"]["is_accurate"]
        } 