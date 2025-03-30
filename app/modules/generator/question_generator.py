from typing import List, Dict, Any
from app.core.model_loader import get_model_loader
from app.schemas.question import Question
import json
import random
from transformers import pipeline

class QuestionGenerator:
    """题目生成器"""
    
    def __init__(self):
        self.model = None
        self.model_loader = get_model_loader()
        self.question_types = ["choice", "short_answer", "true_false"]
        self.sources = ["crawler", "model_generation"]
    
    def _load_model(self):
        """懒加载模型"""
        if self.model is None:
            self.model = self.model_loader.load_model("THUDM/chatglm3-6b")
    
    def generate(self, prompt: str, count: int = 1) -> List[Question]:
        """生成题目"""
        self._load_model()
        
        # 构建提示词
        system_prompt = """你是一个专业的题目生成器。请根据给定的主题和要求生成题目。
要求：
1. 题目内容要清晰、准确
2. 答案要正确、完整
3. 难度要适中
4. 格式要规范
"""
        
        user_prompt = f"""请生成{count}道题目，主题是：{prompt}
要求：
1. 每道题目包含：内容、类型、选项（如果是选择题）、答案、难度
2. 题目类型可以是：选择题(choice)、问答题(essay)、判断题(judgment)
3. 难度范围：0-1
4. 返回JSON格式
"""
        
        # 调用模型生成
        response = self.model.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # 解析结果
        try:
            questions_data = json.loads(response)
            if not isinstance(questions_data, list):
                questions_data = [questions_data]
                
            questions = []
            for q_data in questions_data:
                question = Question(
                    content=q_data["content"],
                    type=q_data["type"],
                    options=q_data.get("options"),
                    answer=q_data["answer"],
                    difficulty=float(q_data["difficulty"])
                )
                questions.append(question)
                
            return questions
            
        except Exception as e:
            raise ValueError(f"解析生成结果失败: {str(e)}")
    
    def generate_questions(self, count: int = 500) -> List[Dict[str, Any]]:
        """生成指定数量的题目"""
        questions = []
        for _ in range(count):
            question_type = random.choice(self.question_types)
            source = random.choice(self.sources)
            
            if source == "crawler":
                question = self._generate_from_crawler(question_type)
            else:
                question = self._generate_from_model(question_type)
                
            questions.append(question)
            
        return questions
    
    def _generate_from_crawler(self, question_type: str) -> Dict[str, Any]:
        """从爬虫数据生成题目"""
        # TODO: 实现爬虫数据获取和题目生成逻辑
        pass
    
    def _generate_from_model(self, question_type: str) -> Dict[str, Any]:
        """使用模型生成题目"""
        # TODO: 实现模型生成题目逻辑
        pass 