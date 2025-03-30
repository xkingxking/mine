from typing import Dict, Any, List
from transformers import pipeline
import torch
import logging

logger = logging.getLogger(__name__)

class TransformationEvaluator:
    """变形评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self._model = None

    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._model = pipeline(
                "text2text-generation",
                model="THUDM/chatglm3-6b",
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
        return self._model

    def evaluate(self, original_question: Dict[str, Any], 
                transformed_question: Dict[str, Any]) -> Dict[str, Any]:
        """评估题目变形质量
        
        Args:
            original_question (Dict[str, Any]): 原始题目
            transformed_question (Dict[str, Any]): 变形后的题目
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            # 计算相似度
            similarity = self._calculate_similarity(
                original_question["content"],
                transformed_question["content"]
            )
            
            # 评估难度变化
            difficulty_change = self._evaluate_difficulty_change(
                original_question.get("difficulty", 0),
                transformed_question.get("difficulty", 0)
            )
            
            # 评估格式保持度
            format_consistency = self._evaluate_format_consistency(
                original_question,
                transformed_question
            )
            
            # 评估答案一致性
            answer_consistency = self._evaluate_answer_consistency(
                original_question.get("answer"),
                transformed_question.get("answer")
            )
            
            # 计算综合得分
            overall_score = self._calculate_overall_score(
                similarity,
                difficulty_change,
                format_consistency,
                answer_consistency
            )
            
            return {
                "overall_score": overall_score,
                "similarity": similarity,
                "difficulty_change": difficulty_change,
                "format_consistency": format_consistency,
                "answer_consistency": answer_consistency,
                "evaluation_status": "success"
            }
            
        except Exception as e:
            return self._handle_evaluation_error(str(e))

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 使用模型计算相似度
            inputs = f"计算以下两段文本的相似度（0-1之间）：\n文本1：{text1}\n文本2：{text2}"
            response = self.model(inputs, max_length=100, num_return_sequences=1)
            similarity = float(response[0]["generated_text"])
            return max(0.0, min(1.0, similarity))
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"计算相似度时出错: {str(e)}")
            return 0.0
        except Exception as e:
            logger.error(f"计算相似度时发生未知错误: {str(e)}")
            return 0.0

    def _evaluate_difficulty_change(self, original: float, transformed: float) -> float:
        """评估难度变化"""
        if original == 0 or transformed == 0:
            return 0.0
        return 1.0 - abs(original - transformed) / max(original, transformed)

    def _evaluate_format_consistency(self, original: Dict[str, Any], 
                                  transformed: Dict[str, Any]) -> float:
        """评估格式一致性"""
        # 检查关键字段是否保持一致
        key_fields = ["type", "options", "format"]
        consistency = 0.0
        for field in key_fields:
            if field in original and field in transformed:
                if original[field] == transformed[field]:
                    consistency += 1.0
        return consistency / len(key_fields)

    def _evaluate_answer_consistency(self, original_answer: Any, 
                                  transformed_answer: Any) -> float:
        """评估答案一致性"""
        if original_answer is None or transformed_answer is None:
            return 0.0
        return 1.0 if original_answer == transformed_answer else 0.0

    def _calculate_overall_score(self, similarity: float, 
                               difficulty_change: float,
                               format_consistency: float,
                               answer_consistency: float) -> float:
        """计算综合得分"""
        weights = {
            "similarity": 0.4,
            "difficulty_change": 0.2,
            "format_consistency": 0.2,
            "answer_consistency": 0.2
        }
        
        return (
            similarity * weights["similarity"] +
            difficulty_change * weights["difficulty_change"] +
            format_consistency * weights["format_consistency"] +
            answer_consistency * weights["answer_consistency"]
        )

    def _handle_evaluation_error(self, error_message: str) -> Dict[str, Any]:
        """处理评估错误"""
        return {
            "overall_score": 0.0,
            "similarity": 0.0,
            "difficulty_change": 0.0,
            "format_consistency": 0.0,
            "answer_consistency": 0.0,
            "evaluation_status": "error",
            "error_message": error_message
        }

    def generate_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成评估报告"""
        if evaluation_results.get("evaluation_status") == "error":
            return {
                "transformation_report": {
                    "status": "error",
                    "error_message": evaluation_results.get("error_message"),
                    "recommendations": ["评估过程出错，请检查系统配置"]
                }
            }

        return {
            "transformation_report": {
                "status": "success",
                "overall_score": evaluation_results["overall_score"],
                "metrics": {
                    "similarity": evaluation_results["similarity"],
                    "difficulty_change": evaluation_results["difficulty_change"],
                    "format_consistency": evaluation_results["format_consistency"],
                    "answer_consistency": evaluation_results["answer_consistency"]
                },
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成改进建议
        
        Args:
            results (Dict[str, Any]): 评估结果
            
        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []
        
        if results["similarity"] < 0.7:
            recommendations.append("题目变形程度过大，建议保持更多原始内容")
        elif results["similarity"] > 0.9:
            recommendations.append("题目变形程度过小，建议增加更多变化")
            
        if results["difficulty_change"] < 0.5:
            recommendations.append("难度变化过大，建议调整难度变化幅度")
            
        if results["format_consistency"] < 0.8:
            recommendations.append("格式一致性较低，建议保持更多原始格式")
            
        if results["answer_consistency"] < 1.0:
            recommendations.append("答案不一致，需要修正变形后的答案")
            
        if not recommendations:
            recommendations.append("题目变形质量良好，无需特别处理")
            
        return recommendations 