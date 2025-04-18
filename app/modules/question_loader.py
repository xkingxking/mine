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
        self.domain = self._get_domain_from_filename()
    
    def _get_domain_from_filename(self) -> str:
        """从文件名获取领域信息"""
        filename = self.questions_file.name
        domain_map = {
            "philosophy": "哲学",
            "medical": "医学",
            "math": "数学",
            "law": "法学",
            "education": "教育",
            "geography": "地理",
            "economics": "经济",
            "chinese_literature": "中国文学",
            "chinese_history": "中国历史",
            "humaneval": "编程",
            "safety": "安全",
            "reasoning": "推理能力",
            "security": "安全能力",
            "knowledge": "知识能力",
            "comprehension": "理解能力",
            "language": "语言能力",
            "interdisciplinary": "学科综合能力"
        }
        
        for key, value in domain_map.items():
            if key in filename.lower():
                return value
        return "通用"
    
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
            
            # 检查数据格式
            if isinstance(data, dict):
                # 如果是字典格式，提取元数据和题目列表
                self.metadata = {k: v for k, v in data.items() if k != "questions"}
                self.questions = data.get("questions", [])
            elif isinstance(data, list):
                # 如果是列表格式，直接使用
                self.questions = data
            else:
                raise ValueError(f"不支持的数据格式: {type(data)}")
            
            # 验证每个题目的格式
            required_fields = ["id", "type", "question"]
            for q in self.questions:
                if not isinstance(q, dict):
                    raise ValueError(f"题目必须是字典格式: {q}")
                missing_fields = [f for f in required_fields if f not in q]
                if missing_fields:
                    raise ValueError(f"题目缺少必要字段 {missing_fields}: {q}")
            
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