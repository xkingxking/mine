from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.modules.evaluator.base_evaluator import BaseEvaluator

class AccuracyEvaluator(BaseEvaluator):
    """准确性评估器，用于评估答案的准确性"""
    
    def evaluate(self, model_output: str, standard_answer: str) -> Dict[str, Any]:
        """
        评估答案的准确性
        
        Args:
            model_output (str): 模型答案
            standard_answer (str): 标准答案
            
        Returns:
            Dict[str, Any]: 准确性评估结果
        """
        # 使用文本相似度计算答案准确性
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([model_output, standard_answer])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            similarity = 0.0
        
        return {
            "accuracy_score": similarity,
            "similarity_level": "高" if similarity >= 0.8 else "中" if similarity >= 0.6 else "低",
            "model_answer": model_output,
            "standard_answer": standard_answer
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
                "score": evaluation_results["accuracy_score"],
                "level": evaluation_results["similarity_level"],
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """生成改进建议"""
        recommendations = []
        if results["accuracy_score"] < 0.8:
            recommendations.append("答案准确性有待提高，建议优化模型的知识理解能力")
        return recommendations 