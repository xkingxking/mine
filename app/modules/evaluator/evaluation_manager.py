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
    
    async def evaluate_response(
        self,
        model_output: str,
        standard_answer: str = None,
        question_type: str = "general"
    ) -> Dict[str, Any]:
        """评估模型响应
        
        Args:
            model_output (str): 模型输出
            standard_answer (str, optional): 标准答案
            question_type (str, optional): 题目类型，默认为"general"
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            print("\n=== 开始评估模型响应 ===")
            print(f"题目类型: {question_type}")
            print(f"模型输出: {model_output[:100]}...")
            if standard_answer:
                print(f"标准答案: {standard_answer[:100]}...")
            
            # 获取评估器
            safety_evaluator = self.evaluators.get("safety")
            accuracy_evaluator = self.evaluators.get("accuracy")
            
            if not safety_evaluator or not accuracy_evaluator:
                raise ValueError("缺少必要的评估器")
            
            # 并行执行安全性和准确性评估
            print("并行执行安全性和准确性评估...")
            safety_task = safety_evaluator.evaluate(model_output)
            accuracy_task = accuracy_evaluator.evaluate(model_output, standard_answer)
            
            safety_results, accuracy_results = await asyncio.gather(
                safety_task, accuracy_task, return_exceptions=True
            )
            
            # 检查是否有评估失败
            if isinstance(safety_results, Exception):
                print(f"安全性评估失败: {str(safety_results)}")
                safety_results = {
                    "safety": {
                        "safety_score": 0.0,
                        "toxicity_score": 0.0,
                        "toxicity_level": "高",
                        "evaluation_status": "error",
                        "error_message": str(safety_results),
                        "is_safe": "false"
                    }
                }
            
            if isinstance(accuracy_results, Exception):
                print(f"准确性评估失败: {str(accuracy_results)}")
                accuracy_results = {
                    "accuracy": {
                        "accuracy_score": 0.0,
                        "similarity_level": "低",
                        "standard_answer": standard_answer,
                        "is_accurate": "false",
                        "error_message": str(accuracy_results)
                    }
                }
            
            # 合并评估结果
            results = {
                "safety": safety_results.get("safety", {
                    "safety_score": 0.0,
                    "toxicity_score": 0.0,
                    "toxicity_level": "高",
                    "evaluation_status": "error",
                    "is_safe": "false"
                }),
                "accuracy": accuracy_results.get("accuracy", {
                    "accuracy_score": 0.0,
                    "similarity_level": "低",
                    "standard_answer": standard_answer,
                    "is_accurate": "false"
                })
            }
            
            print("评估结果:")
            print(f"安全性分数: {results['safety']['safety_score']}")
            print(f"准确性分数: {results['accuracy']['accuracy_score']}")
            print("=== 评估完成 ===\n")
            
            return results
            
        except Exception as e:
            print(f"评估过程中出现错误: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return {
                "safety": {
                    "safety_score": 0.0,
                    "toxicity_score": 0.0,
                    "toxicity_level": "高",
                    "evaluation_status": "error",
                    "error_message": str(e),
                    "is_safe": "false"
                },
                "accuracy": {
                    "accuracy_score": 0.0,
                    "similarity_level": "低",
                    "standard_answer": standard_answer,
                    "is_accurate": "false",
                    "error_message": str(e)
                }
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
        """获取评估摘要
        
        Args:
            results (Dict[str, Any]): 评估结果
            
        Returns:
            Dict[str, Any]: 评估摘要
        """
        try:
            print("\n=== 开始生成评估摘要 ===")
            print(f"输入结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
            
            # 计算总体得分
            overall_score = self._calculate_overall_score(results)
            print(f"计算得到的总体得分: {overall_score}")
            
            # 获取安全性和准确性得分
            safety_score = results.get("safety", {}).get("safety_score", 0.0)
            accuracy_score = results.get("accuracy", {}).get("accuracy_score", 0.0)
            print(f"安全性得分: {safety_score}")
            print(f"准确性得分: {accuracy_score}")
            
            # 获取评估状态
            safety_status = results.get("safety", {}).get("evaluation_status", "error")
            accuracy_status = results.get("accuracy", {}).get("evaluation_status", "error")
            print(f"安全性评估状态: {safety_status}")
            print(f"准确性评估状态: {accuracy_status}")
            
            # 生成摘要
            summary = {
                "overall_score": overall_score,
                "safety_score": safety_score,
                "accuracy_score": accuracy_score,
                "safety_status": safety_status,
                "accuracy_status": accuracy_status,
                "is_safe": results.get("safety", {}).get("is_safe", "false"),
                "is_accurate": results.get("accuracy", {}).get("is_accurate", "false")
            }
            
            print("评估摘要:")
            print(f"总体得分: {summary['overall_score']}")
            print(f"安全性得分: {summary['safety_score']}")
            print(f"准确性得分: {summary['accuracy_score']}")
            print(f"安全性状态: {summary['safety_status']}")
            print(f"准确性状态: {summary['accuracy_status']}")
            print(f"是否安全: {summary['is_safe']}")
            print(f"是否准确: {summary['is_accurate']}")
            print("=== 评估摘要生成完成 ===\n")
            
            return summary
            
        except Exception as e:
            print(f"生成评估摘要时出错: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return {
                "overall_score": 0.0,
                "safety_score": 0.0,
                "accuracy_score": 0.0,
                "safety_status": "error",
                "accuracy_status": "error",
                "is_safe": "false",
                "is_accurate": "false",
                "error_message": str(e)
            } 