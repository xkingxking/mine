from typing import Dict, Any
from .safety_evaluator import SafetyEvaluator
from .accuracy_evaluator import AccuracyEvaluator
from .choice_evaluator import ChoiceEvaluator

class EvaluationManager:
    """评估管理器，用于管理不同类型的评估"""
    
    def __init__(self):
        self.evaluators = {
            "safety": SafetyEvaluator(),
            "accuracy": AccuracyEvaluator(),
            "choice": ChoiceEvaluator()
        }
    
    async def evaluate_response(self,
                              model_output: str,
                              standard_answer: str,
                              question_type: str) -> Dict[str, Any]:
        """
        评估模型响应
        
        Args:
            model_output (str): 模型输出
            standard_answer (str): 标准答案
            question_type (str): 题型
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        results = {}
        
        # 安全性评估
        if hasattr(self.evaluators["safety"], "evaluate_async"):
            safety_result = await self.evaluators["safety"].evaluate_async(model_output)
        else:
            safety_result = self.evaluators["safety"].evaluate(model_output)
        results["safety"] = safety_result
        
        # 准确性评估
        if hasattr(self.evaluators["accuracy"], "evaluate_async"):
            accuracy_result = await self.evaluators["accuracy"].evaluate_async(
                model_output,
                standard_answer
            )
        else:
            accuracy_result = self.evaluators["accuracy"].evaluate(
                model_output,
                standard_answer
            )
        results["accuracy"] = accuracy_result
        
        # 选择题特定评估
        if question_type == "choice":
            if hasattr(self.evaluators["choice"], "evaluate_async"):
                choice_result = await self.evaluators["choice"].evaluate_async(
                    model_output,
                    standard_answer
                )
            else:
                choice_result = self.evaluators["choice"].evaluate(
                    model_output,
                    standard_answer
                )
            results["choice"] = choice_result
        
        # 计算总体评分
        results["overall_score"] = self._calculate_overall_score(results)
        
        return results
    
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