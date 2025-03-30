from typing import Dict, Any
from app.modules.evaluator.base_evaluator import BaseEvaluator

class ChoiceEvaluator(BaseEvaluator):
    """选择题评估器，用于评估选择题答案的准确性"""
    
    def evaluate(self, model_output: str, standard_answer: str) -> Dict[str, Any]:
        """
        评估选择题答案的准确性
        
        Args:
            model_output (str): 模型选择的答案
            standard_answer (str): 标准答案
            
        Returns:
            Dict[str, Any]: 准确性评估结果
        """
        # 标准化答案格式（去除空格，转换为小写等）
        model_answer = model_output.strip().lower()
        standard = standard_answer.strip().lower()
        
        # 检查答案是否完全匹配
        is_correct = model_answer == standard
        
        return {
            "is_correct": is_correct,
            "accuracy_score": 1.0 if is_correct else 0.0,
            "model_answer": model_answer,
            "standard_answer": standard
        }
    
    def generate_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成选择题评估报告
        
        Args:
            evaluation_results (Dict[str, Any]): 评估结果
            
        Returns:
            Dict[str, Any]: 评估报告
        """
        return {
            "choice_report": {
                "is_correct": evaluation_results["is_correct"],
                "score": evaluation_results["accuracy_score"],
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """生成改进建议"""
        recommendations = []
        if not results["is_correct"]:
            recommendations.append("模型答案与标准答案不匹配，建议检查模型对选项的理解能力")
        return recommendations 