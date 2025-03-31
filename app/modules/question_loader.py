import json
from typing import Dict, Any, List
from pathlib import Path

class QuestionLoader:
    """题目加载器，用于加载和管理题目"""
    
    def __init__(self, questions_file: str):
        """
        初始化题目加载器
        
        Args:
            questions_file (str): 题目文件路径
        """
        self.questions_file = Path(questions_file)
        self.questions = []
        self.metadata = {}
    
    def load_questions(self) -> List[Dict[str, Any]]:
        """
        加载题目
        
        Returns:
            List[Dict[str, Any]]: 题目列表
        """
        if not self.questions_file.exists():
            raise FileNotFoundError(f"题目文件不存在: {self.questions_file}")
            
        with open(self.questions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 直接使用加载的数据作为题目列表
            self.questions = data
            return self.questions
    
    def get_question_by_id(self, question_id: str) -> Dict[str, Any]:
        """
        根据ID获取题目
        
        Args:
            question_id (str): 题目ID
            
        Returns:
            Dict[str, Any]: 题目信息
        """
        for question in self.questions:
            if question["id"] == question_id:
                return question
        raise ValueError(f"未找到ID为 {question_id} 的题目")
    
    def get_questions_by_type(self, question_type: str) -> List[Dict[str, Any]]:
        """
        根据题型获取题目
        
        Args:
            question_type (str): 题型
            
        Returns:
            List[Dict[str, Any]]: 题目列表
        """
        return [q for q in self.questions if q["type"] == question_type]
    
    def get_questions_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        根据领域获取题目
        
        Args:
            domain (str): 题目领域
            
        Returns:
            List[Dict[str, Any]]: 题目列表
        """
        return [q for q in self.questions if q.get("题目领域") == domain]
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取题目元数据
        
        Returns:
            Dict[str, Any]: 元数据信息
        """
        return self.metadata 