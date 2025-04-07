from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.modules.evaluator.base_evaluator import BaseEvaluator
import re

class AccuracyEvaluator(BaseEvaluator):
    """准确性评估器，用于评估答案的准确性"""
    
    async def evaluate(self, model_output: str, standard_answer: str = None) -> Dict[str, Any]:
        """评估模型输出的准确性"""
        print("\n=== 开始准确性评估 ===")
        print(f"标准答案: {standard_answer}")
        print(f"模型输出: {model_output[:100]}...")
        
        try:
            # 检查是否是选择题
            if standard_answer in ["A", "B", "C", "D"]:
                print("检测到选择题，进行选项匹配...")
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
            else:
                print("非选择题，使用文本相似度...")
                # 使用TF-IDF和余弦相似度计算文本相似度
                vectorizer = TfidfVectorizer()
                try:
                    tfidf_matrix = vectorizer.fit_transform([model_output, standard_answer])
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    accuracy_score = float(similarity)
                    print(f"计算得到相似度: {accuracy_score:.4f}")
                except Exception as e:
                    print(f"计算相似度时出错: {str(e)}")
                    accuracy_score = 0.0
            
            # 确定相似度级别
            similarity_level = "高" if accuracy_score >= 0.8 else "中" if accuracy_score >= 0.6 else "低"
            print(f"相似度级别: {similarity_level}")
            
            result = {
                "accuracy": {
                    "accuracy_score": accuracy_score,
                    "similarity_level": similarity_level,
                    "standard_answer": standard_answer,
                    "is_accurate": accuracy_score >= 0.8
                }
            }
            
            print("=== 准确性评估完成 ===\n")
            return result
            
        except Exception as e:
            print(f"准确性评估失败: {str(e)}")
            return {
                "accuracy": {
                    "accuracy_score": 0.0,
                    "similarity_level": "低",
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
                "level": evaluation_results["accuracy"]["similarity_level"],
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """生成改进建议"""
        recommendations = []
        if results["accuracy"]["accuracy_score"] < 0.8:
            recommendations.append("答案准确性有待提高，建议优化模型的知识理解能力")
        return recommendations 