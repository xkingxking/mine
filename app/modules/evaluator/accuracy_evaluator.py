from typing import Dict, Any
from app.modules.evaluator.base_evaluator import BaseEvaluator
import re

class AccuracyEvaluator(BaseEvaluator):
    """准确性评估器，用于评估选择题答案的准确性"""
    
    async def evaluate(self, model_output: str, standard_answer: str = None) -> Dict[str, Any]:
        """评估模型输出的准确性"""
        print("\n=== 开始准确性评估 ===")
        print(f"标准答案: {standard_answer}")
        print(f"模型输出: {model_output[:100]}...")
        
        try:
            # 提取模型输出中的答案
            answer_match = re.search(r'[A-D]', model_output)
            if answer_match:
                extracted_answer = answer_match.group()
                print(f"提取到的答案: {extracted_answer}")
                is_correct = extracted_answer == standard_answer
                print(f"答案匹配{'正确' if is_correct else '错误'}")
                accuracy_score = 1.0 if is_correct else 0.0
            else:
                print("未找到有效答案")
                accuracy_score = 0.0
            
            result = {
                "accuracy": {
                    "accuracy_score": accuracy_score,
                    "standard_answer": standard_answer,
                    "is_accurate": accuracy_score == 1.0
                }
            }
            
            print("=== 准确性评估完成 ===\n")
            return result
            
        except Exception as e:
            print(f"准确性评估失败: {str(e)}")
            return {
                "accuracy": {
                    "accuracy_score": 0.0,
                    "standard_answer": standard_answer,
                    "is_accurate": False,
                    "error_message": str(e)
                }
            }
    
    def generate_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成准确性评估报告
        
        Args:
            evaluation_results (Dict[str, Any]): 评估结果
            
        Returns:
            Dict[str, Any]: 评估报告
        """
        return {
            "accuracy_report": {
                "score": evaluation_results["accuracy"]["accuracy_score"],
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """生成改进建议"""
        recommendations = []
        if results["accuracy"]["accuracy_score"] < 1.0:
            recommendations.append("答案准确性有待提高，建议优化模型的知识理解能力")
        return recommendations 