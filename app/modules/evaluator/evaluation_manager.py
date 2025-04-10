from typing import Dict, Any
from .safety_evaluator import SafetyEvaluator
from .accuracy_evaluator import AccuracyEvaluator
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
            "accuracy": AccuracyEvaluator()
        }
        self.domain_results = {}  # 存储各领域的评估结果
        # 定义难度权重（支持中英文）
        self.difficulty_weights = {
            "easy": 1.0, "简单": 1.0,
            "medium": 1.5, "中等": 1.5,
            "hard": 2.0, "困难": 2.0
        }
        # 难度级别映射
        self.difficulty_mapping = {
            "简单": "easy",
            "中等": "medium",
            "困难": "hard"
        }
    
    def _normalize_difficulty(self, difficulty: str) -> str:
        """标准化难度级别"""
        # 转换为小写
        difficulty = difficulty.lower()
        # 如果是中文，映射到英文
        if difficulty in self.difficulty_mapping:
            return self.difficulty_mapping[difficulty]
        # 如果是英文，确保是小写
        if difficulty in ["easy", "medium", "hard"]:
            return difficulty
        # 默认返回中等难度
        return "medium"
    
    async def evaluate_response(
        self,
        model_output: str,
        standard_answer: str = None,
        domain: str = "通用",
        question_type: str = "choice",
        difficulty: str = "中等"  # 默认值改为中文
    ) -> Dict[str, Any]:
        """评估模型响应
        
        Args:
            model_output (str): 模型输出
            standard_answer (str, optional): 标准答案
            domain (str, optional): 题目领域，默认为"通用"
            question_type (str, optional): 题目类型，默认为"choice"
            difficulty (str, optional): 题目难度，默认为"中等"
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            print("\n=== 开始评估模型响应 ===")
            print(f"题目领域: {domain}")
            print(f"题目类型: {question_type}")
            
            # 标准化难度级别
            normalized_difficulty = self._normalize_difficulty(difficulty)
            print(f"难度级别: {difficulty} (标准化: {normalized_difficulty})")
            
            print(f"模型输出: {model_output[:100]}...")
            if standard_answer:
                print(f"标准答案: {standard_answer}")
            
            # 获取评估器
            accuracy_evaluator = self.evaluators.get("accuracy")
            if not accuracy_evaluator:
                raise ValueError("缺少准确性评估器")
            
            # 执行准确性评估
            accuracy_results = await accuracy_evaluator.evaluate(
                model_output, 
                standard_answer,
                question_type
            )
            
            # 更新领域结果
            if domain not in self.domain_results:
                self.domain_results[domain] = {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "weighted_score": 0.0,
                    "total_weight": 0.0,
                    "accuracy_score": 0.0,
                    "difficulty_stats": {
                        "easy": {"total": 0, "correct": 0},
                        "medium": {"total": 0, "correct": 0},
                        "hard": {"total": 0, "correct": 0}
                    }
                }
            
            # 获取当前题目的难度权重
            weight = self.difficulty_weights.get(normalized_difficulty, 1.0)
            
            # 更新统计信息
            self.domain_results[domain]["total_questions"] += 1
            self.domain_results[domain]["total_weight"] += weight
            self.domain_results[domain]["difficulty_stats"][normalized_difficulty]["total"] += 1
            
            if accuracy_results["accuracy"]["is_accurate"]:
                self.domain_results[domain]["correct_answers"] += 1
                self.domain_results[domain]["weighted_score"] += weight
                self.domain_results[domain]["difficulty_stats"][normalized_difficulty]["correct"] += 1
            
            # 计算加权准确率
            self.domain_results[domain]["accuracy_score"] = (
                self.domain_results[domain]["weighted_score"] / 
                self.domain_results[domain]["total_weight"]
            )
            
            # 评估结果
            results = {
                "accuracy": accuracy_results["accuracy"],
                "difficulty": difficulty,  # 返回原始难度
                "normalized_difficulty": normalized_difficulty,  # 返回标准化后的难度
                "weight": weight
            }
            
            print("评估结果:")
            print(f"准确性分数: {results['accuracy']['accuracy_score']}")
            print(f"难度级别: {difficulty}")
            print(f"难度权重: {weight}")
            print(f"领域加权准确率: {self.domain_results[domain]['accuracy_score']:.2%}")
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
    
    def  get_evaluation_summary(self) -> Dict[str, Any]:
        """获取评估摘要
        
        Returns:
            Dict[str, Any]: 评估摘要，包含总体得分和各领域得分
        """
        try:
            # 计算总体加权得分
            total_weight = sum(r["total_weight"] for r in self.domain_results.values())
            total_weighted_score = sum(r["weighted_score"] for r in self.domain_results.values())
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
            
            # 生成摘要
            summary = {
                "overall_score": overall_score,
                "domain_scores": {
                    domain: {
                        "score": results["accuracy_score"],
                        "total_questions": results["total_questions"],
                        "correct_answers": results["correct_answers"],
                        "difficulty_stats": results["difficulty_stats"]
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