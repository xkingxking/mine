import json
from typing import Dict, Any, Optional

class PromptBuilder:
    """提示词构建器，用于构建不同类型的提示词"""
    
    def __init__(self):
        self.system_prompts = {
            "default": """你是一个专业的题目解答助手。
            """,
            
            "choice": """你是一个专业的题目解答助手，请直接输出选项，不要输出任何解释。
            在回答时请注意：
            1. 答案格式要求严格（必须是 A、B、C、D）
            2. 不要包含任何其他文字或解释
            3. 确保答案的准确性
            4. 如果无法确定答案，请选择最可能的选项""",
            
            "short_answer": """你是一个专业的题目解答助手，请提供简洁准确的答案。
            在回答时请注意：
            1. 答案要简洁明了，直接回答问题
            2. 不要包含无关的解释或背景信息
            3. 确保答案的准确性和完整性
            4. 如果无法确定答案，请说明原因""",
            
            "true_false": """你是一个专业的题目解答助手，请直接回答"正确"或"错误"。
            在回答时请注意：
            1. 答案格式要求严格（必须是"正确"或"错误"）
            2. 不要包含任何其他文字或解释
            3. 确保答案的准确性
            4. 如果无法确定答案，请选择最可能的选项""",
            
            "code": """你是一个专业的编程题目解答助手，请提供完整的代码实现。
            在回答时请注意：
            1. 提供完整的、可运行的代码
            2. 代码要简洁高效，符合最佳实践
            3. 包含必要的注释说明
            4. 确保代码的正确性和可读性""",
            
            "translation": """你是一个专业的翻译题目解答助手，请提供准确的翻译结果。
            在回答时请注意：
            1. 翻译要准确、通顺
            2. 保持原文的风格和语气
            3. 注意专业术语的准确性
            4. 确保翻译的完整性和可读性""",
            
            "scenario": """你是一个专业的场景分析题目解答助手，请提供合理的解决方案。
            在回答时请注意：
            1. 分析要全面、深入
            2. 解决方案要具体、可行
            3. 考虑各种可能的情况
            4. 确保回答的实用性和可操作性"""
        }
        
        #这边可以补全其他题型的提示词
        
    
    def build_prompt(self, 
                    question_data: Dict[str, Any],
                    system_prompt: Optional[str] = None) -> Dict[str, str]:
        """
        构建提示词
        
        Args:
            question_data (Dict[str, Any]): 题目信息
            system_prompt (Optional[str]): 自定义系统提示词
            
        Returns:
            Dict[str, str]: 包含系统提示词和用户提示词的字典
        """
        # 获取或构建系统提示词
        if system_prompt:
            system = system_prompt
        else:
            system = self.system_prompts.get(
                question_data["type"],
                self.system_prompts["default"]
            )
        
        # 构建用户提示词
        user = f"""
        请回答以下题目：
        题目：{question_data['question']}
        类型：{question_data['type']}
        领域：{question_data.get('题目领域', '未知')}
        难度：{question_data.get('难度级别', '未知')}
        测试指标：{question_data.get('测试指标', '未知')}
        """
        
        # 处理选择题选项
        if question_data['type'] == 'choice' and 'choices' in question_data:
            choices = question_data['choices']
            if isinstance(choices, dict):
                choices_str = "\n".join([f"{k}. {v}" for k, v in choices.items()])
                user += f"\n选项：\n{choices_str}\n"
        
        # 根据题型添加特定指令
        user += self._get_type_specific_instruction(question_data["type"])
        
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
            "choice": "\n请从选项中选择一个正确答案",
            "short_answer": "\n请提供答案。",
            "true_false": "\n请回答'正确'或'错误'",
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