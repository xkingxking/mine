from typing import Dict, Any
from app.modules.evaluator.base_evaluator import BaseEvaluator
import re
from .nochoice_evaluator import EnhancedEvaluator

class AccuracyEvaluator(BaseEvaluator):
    """准确性评估器，用于评估选择题答案的准确性"""
    
    def __init__(self):
        self.nochoice_evaluator = EnhancedEvaluator()
        
    async def evaluate(self, model_output: str, standard_answer: str = None, question_type: str = "choice") -> Dict[str, Any]:
        """评估模型输出的准确性
        
        Args:
            model_output (str): 模型输出
            standard_answer (str): 标准答案
            question_type (str): 题目类型，可选值：choice, short_answer, true_false, code, translation, scenario
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        print("\n=== 开始准确性评估 ===")
        print(f"题目类型: {question_type}")
        print(f"标准答案: {standard_answer}")
        print(f"模型输出: {model_output[:100]}...")
        
        try:
            if question_type == "choice":
                # 选择题评估逻辑
                answer_match = re.search(r'[A-D]', model_output)
                if answer_match:
                    extracted_answer = answer_match.group()
                    print(f"选择题评估结果:")
                    print(f"提取到的答案: {extracted_answer}")
                    is_correct = extracted_answer == standard_answer
                    print(f"答案匹配{'正确' if is_correct else '错误'}")
                    accuracy_score = 1.0 if is_correct else 0.0
                else:
                    print("未找到有效答案")
                    accuracy_score = 0.0
                    
            elif question_type == "true_false":
                # 判断题评估逻辑
                answer_match = re.search(r'(正确|错误)', model_output)
                if answer_match:
                    print(f"判断题评估结果:")
                    extracted_answer = answer_match.group()
                    print(f"提取到的答案: {extracted_answer}")
                    is_correct = extracted_answer == standard_answer
                    print(f"答案匹配{'正确' if is_correct else '错误'}")
                    accuracy_score = 1.0 if is_correct else 0.0
                else:
                    print("未找到有效答案")
                    accuracy_score = 0.0
                    
            elif question_type == "short_answer":
                # 使用 NoChoiceEvaluator 评估简答题
                accuracy_score, is_correct = self.nochoice_evaluator.evaluate_short_answer(model_output, standard_answer)
                
            elif question_type == "code":
                # 使用 NoChoiceEvaluator 评估代码题
                accuracy_score, is_correct = self.nochoice_evaluator.evaluate_code(model_output, standard_answer)
                
            elif question_type == "translation":
                # 使用 NoChoiceEvaluator 评估翻译题
                accuracy_score, is_correct = self.nochoice_evaluator.evaluate_translation(model_output, standard_answer)
                
            elif question_type == "scenario":
                # 使用 NoChoiceEvaluator 评估场景题
                accuracy_score, is_correct = self.nochoice_evaluator.evaluate_scenario(model_output, standard_answer)
                
            else:
                print(f"未知题目类型: {question_type}")
                accuracy_score = 0.0
                is_correct = False
            
            result = {
                "accuracy": {
                    "accuracy_score": accuracy_score,
                    "standard_answer": standard_answer,
                    "is_accurate": is_correct
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