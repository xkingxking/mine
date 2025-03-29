from typing import Dict, Any, List, Optional
from transformers import pipeline
import torch

class QuestionTransformer:
    """题目变形器"""
    
    def __init__(self):
        """初始化变形器"""
        self.transform_types = {
            "paraphrase": "同义改写",
            "difficulty_adjust": "难度调整",
            "context_change": "上下文改变",
            "format_change": "格式改变",
            "perspective_change": "视角改变"
        }
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

    def transform(self, question: Dict[str, Any], transform_type: str) -> Dict[str, Any]:
        """对题目进行变形
        
        Args:
            question (Dict[str, Any]): 原始题目
            transform_type (str): 变形类型
            
        Returns:
            Dict[str, Any]: 变形后的题目
        """
        if transform_type not in self.transform_types:
            raise ValueError(f"不支持的变形类型: {transform_type}")
            
        try:
            # 根据变形类型选择相应的处理方法
            transform_method = getattr(self, f"_transform_{transform_type}")
            transformed = transform_method(question)
            
            # 保持原始题目的其他属性
            transformed.update({
                k: v for k, v in question.items() 
                if k not in ["content", "options", "answer", "difficulty"]
            })
            
            return transformed
            
        except Exception as e:
            raise Exception(f"题目变形失败: {str(e)}")

    def _transform_paraphrase(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """同义改写"""
        prompt = f"请对以下题目进行同义改写，保持题目类型和答案不变：\n{question['content']}"
        response = self.model(prompt, max_length=200, num_return_sequences=1)
        return {
            "content": response[0]["generated_text"],
            "options": question.get("options", []),
            "answer": question.get("answer"),
            "difficulty": question.get("difficulty", 0.5)
        }

    def _transform_difficulty_adjust(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """难度调整"""
        current_difficulty = question.get("difficulty", 0.5)
        # 随机调整难度
        new_difficulty = max(0.1, min(0.9, current_difficulty + (torch.rand(1).item() - 0.5) * 0.2))
        
        prompt = f"请调整以下题目的难度（当前难度：{current_difficulty:.2f}，目标难度：{new_difficulty:.2f}）：\n{question['content']}"
        response = self.model(prompt, max_length=200, num_return_sequences=1)
        
        return {
            "content": response[0]["generated_text"],
            "options": question.get("options", []),
            "answer": question.get("answer"),
            "difficulty": new_difficulty
        }

    def _transform_context_change(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """上下文改变"""
        prompt = f"请改变以下题目的上下文，但保持核心问题不变：\n{question['content']}"
        response = self.model(prompt, max_length=200, num_return_sequences=1)
        return {
            "content": response[0]["generated_text"],
            "options": question.get("options", []),
            "answer": question.get("answer"),
            "difficulty": question.get("difficulty", 0.5)
        }

    def _transform_format_change(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """格式改变"""
        current_type = question.get("type", "choice")
        if current_type == "choice":
            # 将选择题转换为填空题
            prompt = f"请将以下选择题转换为填空题：\n{question['content']}\n选项：{question.get('options', [])}"
            response = self.model(prompt, max_length=200, num_return_sequences=1)
            return {
                "content": response[0]["generated_text"],
                "type": "fill_blank",
                "answer": question.get("answer"),
                "difficulty": question.get("difficulty", 0.5)
            }
        else:
            # 将填空题转换为选择题
            prompt = f"请将以下填空题转换为选择题：\n{question['content']}"
            response = self.model(prompt, max_length=200, num_return_sequences=1)
            return {
                "content": response[0]["generated_text"],
                "type": "choice",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                "answer": "A",
                "difficulty": question.get("difficulty", 0.5)
            }

    def _transform_perspective_change(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """视角改变"""
        prompt = f"请从不同视角重新表述以下题目：\n{question['content']}"
        response = self.model(prompt, max_length=200, num_return_sequences=1)
        return {
            "content": response[0]["generated_text"],
            "options": question.get("options", []),
            "answer": question.get("answer"),
            "difficulty": question.get("difficulty", 0.5)
        } 