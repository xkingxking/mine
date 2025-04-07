import json
from typing import Dict, Any, Optional

class PromptBuilder:
    """提示词构建器，用于构建不同类型的提示词"""
    
    def __init__(self):
        self.system_prompts = {
            "default": """你是一个专业的题目解答助手，请根据题目类型提供准确的答案和简要解题思路。
            在回答时请注意：
            1. 保持答案的准确性和完整性
            2. 提供清晰的解题思路
            3. 对于代码题，确保代码可以正常运行
            4. 对于翻译题，保持翻译的准确性和流畅性
            5. 对于场景题，提供合理的分析和解决方案""",
            
            "code": """你是一个专业的编程助手，请提供清晰、可运行的代码实现。
            在回答时请注意：
            1. 代码必须可以正常运行
            2. 包含必要的注释说明
            3. 遵循编程最佳实践
            4. 考虑代码的可读性和可维护性""",
            
            "translation": """你是一个专业的翻译助手，请提供准确、流畅的翻译结果。
            在回答时请注意：
            1. 保持原文的意思和语气
            2. 符合目标语言的表达习惯
            3. 注意专业术语的准确性
            4. 保持翻译的流畅性""",
            
            "scenario": """你是一个专业的场景分析助手，请提供合理的分析和解决方案。
            在回答时请注意：
            1. 全面分析场景要素
            2. 考虑多个可能的解决方案
            3. 评估每个方案的优缺点
            4. 给出最合理的建议"""
            #这边可以补全其他题型的提示词
        }
    
    def build_prompt(self, 
                    question: Dict[str, Any],
                    system_prompt: Optional[str] = None) -> Dict[str, str]:
        """
        构建提示词
        
        Args:
            question (Dict[str, Any]): 题目信息
            system_prompt (Optional[str]): 自定义系统提示词
            
        Returns:
            Dict[str, str]: 包含系统提示词和用户提示词的字典
        """
        # 获取或构建系统提示词
        if system_prompt:
            system = system_prompt
        else:
            system = self.system_prompts.get(
                question["type"],
                self.system_prompts["default"]
            )
        
        # 构建用户提示词
        user = f"""
        请回答以下题目：
        题目：{question['question']}
        类型：{question['type']}
        领域：{question.get('题目领域', '未知')}
        难度：{question.get('难度级别', '未知')}
        测试指标：{question.get('测试指标', '未知')}
        """
        
        if "choices" in question:
            choices_str = "\n".join([f"{k}. {v}" for k, v in question['choices'].items()])
            user += f"\n选项：\n{choices_str}"
        
        # 根据题型添加特定指令
        user += self._get_type_specific_instruction(question["type"])
        
        return {
            "system": system,
            "user": user
        }
    
    def _get_type_specific_instruction(self, question_type: str) -> str:
        """
        获取题型特定的指令
        
        Args:
            question_type (str): 题型
            
        Returns:
            str: 特定指令
        """
        instructions = {
            "choice": "\n请从选项中选择一个正确答案，并说明选择理由。",
            "short_answer": "\n请提供详细答案和解题思路（如需演示，请用文字描述）。",
            "true_false": "\n请回答'正确'或'错误'，并简要说明理由。",
            "code": "\n请提供完整的代码实现，并说明关键步骤。",
            "translation": "\n请提供准确的翻译结果，并说明翻译要点。",
            "scenario": "\n请分析场景并给出合理的解决方案，说明理由。"
        }
        return instructions.get(question_type, "")
    
    def add_system_prompt(self, prompt_type: str, prompt: str):
        """
        添加自定义系统提示词
        
        Args:
            prompt_type (str): 提示词类型
            prompt (str): 提示词内容
        """
        self.system_prompts[prompt_type] = prompt 