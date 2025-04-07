from typing import Dict, Any
from .safety_evaluator import SafetyEvaluator
from .accuracy_evaluator import AccuracyEvaluator
from .choice_evaluator import ChoiceEvaluator
import asyncio
import json

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
        self.domain_results = {}  # 存储各领域的评估结果
    
    async def evaluate_response(
        self,
        model_output: str,
        standard_answer: str = None,
        domain: str = "通用"
    ) -> Dict[str, Any]:
        """评估模型响应
        
        Args:
            model_output (str): 模型输出
            standard_answer (str, optional): 标准答案
            question_type (str, optional): 题目类型，默认为"general"
            domain (str, optional): 题目领域，默认为"通用"
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            print("\n=== 开始评估模型响应 ===")
            print(f"题目领域: {domain}")
            print(f"模型输出: {model_output[:100]}...")
            if standard_answer:
                print(f"标准答案: {standard_answer}")
            
            # 获取评估器
            accuracy_evaluator = self.evaluators.get("accuracy")
            if not accuracy_evaluator:
                raise ValueError("缺少准确性评估器")
            
            # 执行准确性评估
            accuracy_results = await accuracy_evaluator.evaluate(model_output, standard_answer)
            
            # 更新领域结果
            if domain not in self.domain_results:
                self.domain_results[domain] = {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "accuracy_score": 0.0
                }
            
            self.domain_results[domain]["total_questions"] += 1
            if accuracy_results["accuracy"]["is_accurate"]:
                self.domain_results[domain]["correct_answers"] += 1
            self.domain_results[domain]["accuracy_score"] = (
                self.domain_results[domain]["correct_answers"] / 
                self.domain_results[domain]["total_questions"]
            )
            
            # 评估结果
            results = {
                "accuracy": accuracy_results["accuracy"]
            }
            
            print("评估结果:")
            print(f"准确性分数: {results['accuracy']['accuracy_score']}")
            print(f"领域准确率: {self.domain_results[domain]['accuracy_score']:.2%}")
            print("=== 评估完成 ===\n")
            
            return results
            
        except Exception as e:
            print(f"评估过程中出现错误: {str(e)}")
            return {
                "accuracy": {
                    "accuracy_score": 0.0,
                    "similarity_level": "低",
                    "standard_answer": standard_answer,
                    "is_accurate": False,
                    "error_message": str(e)
                }
            }
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """获取评估摘要
        
        Returns:
            Dict[str, Any]: 评估摘要，包含总体得分和各领域得分
        """
        try:
            # 计算总体得分
            total_questions = sum(r["total_questions"] for r in self.domain_results.values())
            total_correct = sum(r["correct_answers"] for r in self.domain_results.values())
            overall_score = total_correct / total_questions if total_questions > 0 else 0.0
            
            # 生成摘要
            summary = {
                "overall_score": overall_score,
                "domain_scores": {
                    domain: {
                        "score": results["accuracy_score"],
                        "total_questions": results["total_questions"],
                        "correct_answers": results["correct_answers"]
                    }
                    for domain, results in self.domain_results.items()
                }
            }
            
            return summary
            
        except Exception as e:
            print(f"生成评估摘要时出错: {str(e)}")
            return {
                "overall_score": 0.0,
                "domain_scores": {},
                "error_message": str(e)
            } 