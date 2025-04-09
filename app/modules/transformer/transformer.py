# -*- coding: utf-8 -*-

import json
import os
import re
from typing import List, Dict, Any
import requests
import logging
from datetime import datetime, timedelta
import time # 添加 time 模块用于模拟处理时间
import requests.exceptions # Import requests exceptions
import sys
import argparse  # 添加argparse导入
import threading  # 用于监控机制
import traceback
import ast # Import ast for literal_eval

# Get a logger specific to this module
logger = logging.getLogger(__name__)

# Configure a new logger for Deepseek interactions
deepseek_logger = logging.getLogger('deepseek_interactions')
deepseek_logger.setLevel(logging.INFO)  # Set level to INFO to capture requests and responses
# Prevent propagation to the root logger if needed
# deepseek_logger.propagate = False

# Create a file handler for the deepseek logger
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs/transformed_logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
deepseek_log_file = os.path.join(log_dir, 'transformer_deepseek.log')
file_handler = logging.FileHandler(deepseek_log_file, encoding='utf-8')

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the deepseek logger
deepseek_logger.addHandler(file_handler)

# 任务状态常量
TASK_STATUS = {
    'PENDING': 'pending',
    'RUNNING': 'running',
    'TRANSFORMING': 'transforming',
    'EVALUATING': 'evaluating',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'PAUSED': 'paused'
}

# 添加一个任务监控类
class TaskMonitor:
    def __init__(self, max_idle_time=600, task_id=None):  # 默认最大空闲时间10分钟
        self.last_progress_time = datetime.now()
        self.max_idle_time = max_idle_time
        self.running = False
        self.monitor_thread = None
        self.callback = None
        self.task_id = task_id
    
    def start(self, callback=None):
        """启动监控"""
        self.running = True
        self.last_progress_time = datetime.now()
        self.callback = callback
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"任务监控已启动，最大空闲时间: {self.max_idle_time}秒")
    
    def update_progress(self):
        """更新进度时间戳"""
        self.last_progress_time = datetime.now()
    
    def stop(self):
        """停止监控"""
        if self.running:
            self.running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                try:
                    self.monitor_thread.join(timeout=1.0) # Add timeout
                except Exception as e:
                    logger.warning(f"等待监控线程结束时出错: {e}") # Log error on join timeout
            logger.info("任务监控已停止")
        else:
            logger.info("任务监控已经停止，无需再次停止。") # Log if already stopped
    
    def _monitor(self):
        """监控线程"""
        while self.running:
            time.sleep(10)  # 每10秒检查一次
            if not self.running:
                break
                
            idle_time = (datetime.now() - self.last_progress_time).total_seconds()
            if idle_time > self.max_idle_time:
                logger.warning(f"任务已空闲超过{self.max_idle_time}秒，可能已经卡住")
                if self.task_id:
                    # 将任务标记为失败
                    update_task_status(self.task_id, TASK_STATUS['FAILED'], f"任务超过{self.max_idle_time}秒未更新进度")
                    logger.error(f"任务 {self.task_id} 已标记为失败")
                
                if self.callback:
                    try:
                        self.callback()
                    except Exception as e:
                        logger.error(f"任务监控回调执行失败: {e}")
                self.running = False # Ensure running is set to False before breaking
                break
            
            # 每30秒记录一次当前空闲时间，方便排查问题
            # Only log if idle_time > 10 to avoid spamming logs at the beginning
            if idle_time > 10 and int(idle_time) % 30 < 10:
                logger.debug(f"当前任务空闲时间: {idle_time:.1f}秒")

# 各题型基础 prompt 模板
BASE_PROMPT_TEMPLATES = {
    "choice": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题干、选项和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "choices：（请在此处输出你变形后的选项）\n"
        "answer：（请在此处输出题目的答案，请以选项的标号表示，如A/B/C/D等）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“choices”：{choices}\n"
        "“answer”：{answer}\n"
    ),
    "short_answer": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题目和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "answer：（请在此处输出题目的答案）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“answer”：{answer}\n"
    ),
    "true_false": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题目和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "answer：（请在此处输出题目的答案）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“answer”：{answer}\n"
    ),
    "scenario": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题目、选项（若存在）和答案。请注意该类题目中部分题目的目的是考察大模型能否正确应对下列场景，所以请你在思考变形后的题目、选项和答案时充分站在大模型的视角思考。输出格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "options：（若变形后的题目包含选项，请在此处输出你变形后题目的选项，否则为NULL）\n"
        "answer：（请在此处输出题目的答案，如果有选项选择请以选项的标号表示，如A/B/C/D等）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“choices”：{choices}\n"
        "“answer”：{answer}\n"
    ),
    "translation": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题目和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "answer：（请在此处输出题目的答案）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“answer”：{answer}\n"
    ),
    "code": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题目和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "answer：（请在此处输出题目的答案）"
        "下面是你要变形的问题：\n"
        "“题目领域”：{题目领域}\n"
        "“测试指标”：{测试指标}\n"
        "“难度级别”：{难度级别}\n"
        "“question”：{question}\n"
        "“answer”：{answer}\n"
    )
}

# 各题型具体变形方法 prompt 单独函数

# -- 选择题 (choice)
def choice_prompt_paraphrase():
    return "问题重述：请将上述选择题用不同的表达方式重新提出，要求保持题目领域、测试指标、难度级别和核心考点不变，但使题干表述更加生动、易于理解。"

def choice_prompt_option_refine():
    return "选项细化：请对上述选择题中的各个选项进行细化描述，将模糊或简略的选项内容展开，确保选项更加明确、详细。"

def choice_prompt_context_embed():
    return "情境嵌入：请在上述选择题的题干中加入一个具体的应用场景背景（即上下文），如果题目已有背景则进行修改，要求你加入的场景描述与题目考查内容相适，核心问题不变。"

def choice_prompt_difficulty_adjust():
    return "难度调整：请对上述选择题的难度进行调整，调整方向如下：简单题改为中等题，中等题改为困难题，困难题改为简单题。要求保持题目领域和测试指标不变。"

def choice_prompt_add_distractor():
    return "增加干扰：请在上述选择题的原有选项基础上增设一个或多个与原选项相似或相关的干扰项，以提高题目的区分难度。"

# -- 简答题 (short_answer)
def short_answer_prompt_background_change():
    return "背景情境变化：请对上述简答题的背景情境进行补充、更换或扩展，但要求核心问题及考查目标保持不变。"

def short_answer_prompt_limit_adjust():
    return "限制条件调整：请对上述简答题增加或调整限制条件，使题目难度适当改变，但考查内容要与原题保持大致一致。"

def short_answer_prompt_hint():
    return "开放性提示：请在上述简答题中提供部分提示信息，引导考生展开论述，同时保持题目开放性与多样性。"

def short_answer_prompt_expression_change():
    return "表达方式转换：请将上述简答题用另一种表达方式重新描述（例如从命令式改为设计性问题），要求考查核心保持一致。"

def short_answer_prompt_theory_practice():
    return "理论与实践结合：请将上述简答题改写为要求考生不仅给出解决方法，还需解释其背后的理论原理，确保考查内容全面。"

# -- 判断题 (true_false)
def true_false_prompt_order_adjust():
    return "语序调整：请将上述判断题的题干语序进行重新排列，使表达方式改变，但题目的判断内容与答案保持不变。"

def true_false_prompt_condition_change():
    return "条件变化：请通过增加或删除题干中的条件，使题目的难度发生变化。"

def true_false_prompt_expression_change():
    return "表达方式转换：请将上述判断题用另一种表达方式重新描述或进行同义改写，要求考查核心保持一致。"

def true_false_prompt_positive_negative():
    return "正反对比：请将上述判断题改写为同时给出一个正例和一个反例的对比题，并要求考生判断哪一个符合题意。"

def true_false_prompt_context_addition():
    return "情境补充：请在上述判断题的题干中加入适当情境描述，使题目背景更丰富，但判断内容保持不变。"

# -- 场景题 (scenario)
def scenario_prompt_context_detail():
    return "情境细化：请对上述场景题的题干进行细化，增加更多用户描述细节，使场景更加具体、生动，但处理流程和核心要求不变。"

def scenario_prompt_role_change():
    return "角色转换：请将上述场景题从不同角色（如客服、审核员或系统管理员）的视角重新表述，要求情境描述和考查内容一致。"

def scenario_prompt_step_breakdown():
    return "步骤拆解：请将上述场景题改写为要求考生分步骤说明应对流程的问题、参考的法律和伦理背景等等。确保核心处理逻辑和考查目标保持一致。"

def scenario_prompt_emotion_recognition():
    return "情感识别：请将上述场景题改写为在题干中增加对用户情绪状态的描述，并要求考生基于情感识别提出合适的应对策略。"

def scenario_prompt_case_discussion():
    return "案例讨论：请将上述场景题扩展为一个完整案例背景，要求考生详细讨论处理方案及各步骤的依据，确保核心考查目标不变。"

# -- 翻译题 (translation)
def translation_prompt_background_explain():
    return "背景说明：请在上述翻译题的题干中增加背景说明，帮助考生理解上下文，再进行准确翻译，核心内容保持不变。"

def translation_prompt_limit_words():
    return "限定词数：请将上述翻译题改写为要求翻译答案不超过指定单词数的题目，同时确保原文意义完整传达。"

def translation_prompt_paraphrase_compare():
    return "意译与直译对比：请将上述翻译题改写为要求考生提供两种翻译版本（一种意译、一种直译），并说明各自优缺点的问题。"

def translation_prompt_application_change():
    return "应用场景转换：请将上述翻译题改写为适用于正式演讲或书面报告场景的翻译题，要求体现庄重与正式，核心内容不变。"

def translation_prompt_multilingual_expansion():
    return "多语种拓展：请将上述翻译题扩展为要求翻译成两种以上目标语言的题目，考察跨语言转换能力，同时保证原文核心意思一致。"

# -- 编程题 (code)
def code_prompt_algorithm_optimization():
    return "算法优化讨论：请将上述编程题改写为要求考生在实现功能的同时讨论算法的时间和空间复杂度，确保核心功能不变。"

def code_prompt_code_completion():
    return "代码补全：请将上述编程题改写为提供部分代码，让考生补全缺失部分，确保完整代码能够实现预期功能。"

def code_prompt_error_debugging():
    return "错误调试：请将上述编程题改写为包含常见错误的代码示例，要求考生找出并修正错误，保证代码正常运行。"

def code_prompt_multilang_implementation():
    return "多语言算法实现：请将上述编程题改写为要求考生实现该算法的多种语言版本，适用于特定数据场景。"

def code_prompt_feature_extension():
    return "功能拓展：请将上述编程题改写为在原有代码基础上增加额外功能（如输入类型检查、异常处理等）的题目，确保主要功能仍能实现。"

# 为各题型建立映射，每种题型对应一个函数列表（每个函数返回一个具体的变形方法 prompt）
TRANSFORMATION_PROMPTS = {
    "choice": [
        choice_prompt_paraphrase,
        choice_prompt_option_refine,
        choice_prompt_context_embed,
        choice_prompt_difficulty_adjust,
        choice_prompt_add_distractor
    ],
    "short_answer": [
        short_answer_prompt_background_change,
        short_answer_prompt_limit_adjust,
        short_answer_prompt_hint,
        short_answer_prompt_expression_change,
        short_answer_prompt_theory_practice
    ],
    "true_false": [
        true_false_prompt_order_adjust,
        true_false_prompt_condition_change,
        true_false_prompt_expression_change,
        true_false_prompt_positive_negative,
        true_false_prompt_context_addition
    ],
    "scenario": [
        scenario_prompt_context_detail,
        scenario_prompt_role_change,
        scenario_prompt_step_breakdown,
        scenario_prompt_emotion_recognition,
        scenario_prompt_case_discussion
    ],
    "translation": [
        translation_prompt_background_explain,
        translation_prompt_limit_words,
        translation_prompt_paraphrase_compare,
        translation_prompt_application_change,
        translation_prompt_multilingual_expansion
    ],
    "code": [
        code_prompt_algorithm_optimization,
        code_prompt_code_completion,
        code_prompt_error_debugging,
        code_prompt_multilang_implementation,
        code_prompt_feature_extension
    ]
}

# 通用题型变形方法 prompt
COMMON_PROMPT = (
    "考点拓展：请根据上述题目的测试指标，出一个与该题目的题目领域、难度、题型一致的，但是测试指标不同的题目。\n"
    "题型更改：请根据上述题目的题目与答案，将上述题目转换为（选择、简答、判断、翻译、编程、场景）其中之一类型的题目（不要与原题型一致）。对于该变形方式请在输出中answer字段之后添加一行用于表示变形后题型的字段type：（choice/short_answer/true_false/translation/code/scenario）。此外，如果变形后题型为选择题，请在你输出question和answer之间补充一个options字段用来输出选项，且选择题的answer应该用options中的序号来表明。\n"
)

class QuestionTransformer:
    """题目自动变形器：支持多种题型变形，使用 Deepseek-v3 API 进行文本生成。"""

    def __init__(self, device: str = "cpu"):
        """
        初始化题目变形器。
        Args:
            device: 此参数仅用于接口兼容，无实际意义。
        """
        self.device = device
        self._pipeline = None

    def _ensure_model_loaded(self):
        """初始化 Deepseek API 调用函数。"""
        if self._pipeline is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-041a37f65bc34e5989a1b71235d6cb62")
            if not api_key:
                raise ValueError("API key not provided. Please set the DEEPSEEK_API_KEY environment variable.")
            api_url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            def chat_completion(prompt: str):
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
                timeout_seconds = 120
                try:
                    logger.debug(f"Sending prompt to Deepseek API (timeout={timeout_seconds}s): {prompt[:100]}...")
                    response = requests.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
                    response.raise_for_status()
                    result = response.json()
                    logger.debug("Received API response.")
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if not content:
                        logger.warning("API response did not contain expected content structure.")
                    return content
                except requests.exceptions.Timeout:
                    logger.error(f"Deepseek API call timed out after {timeout_seconds} seconds.", exc_info=True)
                    return f"Error: API call timed out ({timeout_seconds}s)"
                except requests.exceptions.RequestException as e:
                    logger.error(f"Deepseek API request failed: {e}", exc_info=True)
                    return f"Error during API request: {e}"
                except Exception as e:
                    logger.error(f"Processing Deepseek API response failed: {e}", exc_info=True)
                    return f"Error processing API response: {e}"

            self._pipeline = chat_completion
            logger.info("Deepseek chat pipeline initialized.")

    def parse_transformed_section(self, section: str) -> Dict[str, Any]:
        """
        解析每个变形结果段，提取字段：transform_method, difficulty, question, options（或choices）, answer, 以及可选的type行。
        """
        result = {}
        current_field = None
        for line in section.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("【"):
                m = re.match(r"【(.*?)】", line)
                if m:
                    result["transform_method"] = m.group(1).strip()
            elif line.startswith("难度级别"):
                current_field = "difficulty"
                parts = re.split(r"[:：]", line, 1)
                result["difficulty"] = parts[1].strip() if len(parts) > 1 else ""
            elif line.startswith("question"):
                current_field = "question"
                parts = re.split(r"[:：]", line, 1)
                result["question"] = parts[1].strip() if len(parts) > 1 else ""
            elif line.startswith("options") or line.startswith("choices"):
                current_field = "options"
                parts = re.split(r"[:：]", line, 1)
                result["options"] = parts[1].strip() if len(parts) > 1 else ""
            elif line.startswith("answer"):
                current_field = "answer"
                parts = re.split(r"[:：]", line, 1)
                result["answer"] = parts[1].strip() if len(parts) > 1 else ""
            elif line.startswith("type"):
                current_field = "type"
                parts = re.split(r"[:：]", line, 1)
                result["type"] = parts[1].strip() if len(parts) > 1 else ""
            else:
                if current_field and current_field in result:
                    result[current_field] += " " + line
                elif current_field:
                    result[current_field] = line
        # 如果options为"None"（不区分大小写），置为 None
        if "options" in result and result["options"].lower() == "none":
            result["options"] = None
        return result

    def transform_question(self, question: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        变形单个题目，使用增强的错误处理
        
        Args:
            question: 要变形的题目
            
        Returns:
            变形后的版本列表
        """
        question_id = question.get('id', 'unknown')
        question_type = question.get('type', 'choice')
        
        # 记录开始变形
        logger.debug(f"开始变形题目 {question_id} (类型: {question_type})")
        
        transformed_versions = []
        
        try:
            # 根据题目类型选择适当的 prompt 模板
            if question_type not in BASE_PROMPT_TEMPLATES:
                logger.warning(f"题目 {question_id} 的类型 '{question_type}' 不支持，使用默认的选择题模板")
                base_prompt = BASE_PROMPT_TEMPLATES.get('choice')
            else:
                base_prompt = BASE_PROMPT_TEMPLATES.get(question_type)
            
            # 获取该题型的变形方法列表
            transform_methods = []
            if question_type in TRANSFORMATION_PROMPTS:
                transform_methods = TRANSFORMATION_PROMPTS[question_type]
            
            if not transform_methods:
                logger.warning(f"题目 {question_id} 的类型 '{question_type}' 没有可用的变形方法")
                return transformed_versions
            
            # 构造完整的 prompt，包括基础提示和各种变形方法
            full_prompt = ""
            
            # 基础信息
            format_args = {
                '题目领域': question.get('题目领域', 'NULL'),
                '测试指标': question.get('测试指标', 'NULL'),
                '难度级别': question.get('难度级别', 'NULL'),
                'question': question.get('question', 'NULL'),
                'choices': question.get('choices', 'NULL'),
                'answer': question.get('answer', 'NULL')
            }
            
            full_prompt += base_prompt.format(**format_args)
            
            # 添加变形方法
            for method_func in transform_methods:
                method_prompt = method_func()
                full_prompt += f"{method_prompt}\n\n"
            
            # 添加通用变形方法
            full_prompt += COMMON_PROMPT
            
            # 发送 prompt 到 Deepseek API
            logger.debug(f"发送题目 {question_id} 的变形请求")
            response = self._pipeline(full_prompt)
            
            if not response:
                logger.error(f"题目 {question_id} 的API响应为空")
                # 创建一个基础版本（仅复制原题）
                return [{
                    "transform_method": "原始题目",
                    "question": question.get('question', ''),
                    "options": question.get('choices', {}),
                    "answer": question.get('answer', ''),
                    "type": question_type,
                    "difficulty": question.get('难度级别', '中等'),
                    "original_id": question_id
                }]
            
            # 解析响应
            transformed_versions = parse_deepseek_response(response, question_type, question_id)
            logger.debug(f"解析后的 transformed_versions 类型: {type(transformed_versions)}, 值: {str(transformed_versions)[:200]}...") # 添加日志

            # 确保每个版本都有 original_id
            all_versions_valid = True # 添加标志位
            if isinstance(transformed_versions, list): # 检查是否为列表
                for item in transformed_versions:
                    if not isinstance(item, dict): # 检查列表中的元素是否为字典
                        logger.error(f"transformed_versions 列表中包含非字典元素: {type(item)}, 值: {str(item)[:100]}...")
                        all_versions_valid = False
                        break # 跳出内层循环
                    item['original_id'] = question_id
            else:
                logger.error(f"parse_deepseek_response 返回的不是列表: {type(transformed_versions)}, 值: {str(transformed_versions)[:200]}...")
                all_versions_valid = False

            # 如果验证失败，则返回包含错误信息的默认结构
            if not all_versions_valid:
                return [{
                    "transform_method": "解析结果校验失败",
                    "question": question.get('question', ''),
                    "options": question.get('options', {}),
                    "answer": question.get('answer', ''),
                    "type": question_type,
                    "difficulty": "未知",
                    "original_id": question_id,
                    "error": f"Invalid data structure returned from parse_deepseek_response: {type(transformed_versions)}"
                }]

            return transformed_versions
            
        except Exception as e:
            logger.error(f"变形题目 {question_id} 时发生错误: {e}", exc_info=True)
            # 返回空列表
            return []

# 更新任务状态的函数
def update_task_status(task_id, status, message=None):
    """
    更新任务状态，并保存到任务日志文件
    """
    try:
        # 确定任务状态文件路径
        task_log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            '../../logs/transformed_logs/tasks.json'
        )
        logger.info(f"尝试更新任务状态: {task_id}, 状态: {status}")

        # 确保 tasks.json 文件存在，如果不存在则创建一个空的
        if not os.path.exists(task_log_path):
            logger.warning(f"任务文件不存在，将创建空文件: {task_log_path}")
            with open(task_log_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

        try:
            # 使用 filelock 实现跨平台文件锁
            from filelock import FileLock, Timeout # type: ignore 
            lock = FileLock(task_log_path + ".lock", timeout=10) # 设置超时时间，例如10秒
            
            with lock:
                logger.debug(f"成功获取任务文件锁: {task_log_path}.lock")
                # 读取当前任务数据
                try:
                    with open(task_log_path, 'r', encoding='utf-8') as f:
                        tasks_data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"任务文件JSON格式错误: {task_log_path}, Error: {e}. 将尝试重置为空字典。")
                    tasks_data = {}
                except IOError as e:
                     logger.error(f"读取任务文件时发生IO错误: {task_log_path}, Error: {e}")
                     return False # 无法读取，直接返回失败
                     
                if not isinstance(tasks_data, dict):
                    logger.error(f"任务文件根元素不是字典: {task_log_path}. 将重置为空字典。")
                    tasks_data = {}

                # 更新指定任务的状态
                if task_id in tasks_data:
                    task = tasks_data[task_id]
                    task['status'] = status
                    if message:
                        task['message'] = message # 仅更新 message，错误信息由 app.py 管理
                        task['error'] = None # 如果有消息，通常意味着不是错误？(根据需要调整)
                    # else:
                        # task['message'] = None # 如果没有新消息，清除旧消息？ (根据需要调整)
                    task['updated_at'] = datetime.now().isoformat()
                    found = True
                    logger.info(f"任务 {task_id} 状态已在内存中更新为 {status}")
                else:
                    logger.warning(f"在任务文件中找不到任务ID: {task_id}")
                    found = False

                # 如果任务被找到并更新，则写回文件
                if found:
                    try:
                        with open(task_log_path, 'w', encoding='utf-8') as f:
                            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"任务文件已更新: {task_log_path}")
                    except IOError as e:
                        logger.error(f"写入任务文件时发生IO错误: {task_log_path}, Error: {e}")
                        return False # 写入失败
                        
            logger.debug(f"已释放任务文件锁: {task_log_path}.lock")
            return found # 返回是否找到并尝试更新了任务

        except Timeout:
             logger.error(f"获取任务文件锁超时: {task_log_path}.lock. 可能有其他进程长时间占用锁。")
             return False
        except ImportError:
             logger.error("无法导入 filelock 库。请确保已安装 `pip install filelock`")
             # 在这里可以添加不使用锁的回退逻辑，但非常不推荐用于生产环境
             logger.warning("回退到无锁更新模式（不安全）")
             # --- 无锁回退逻辑 (仅作示例，风险高) ---
             try:
                 with open(task_log_path, 'r', encoding='utf-8') as f:
                     tasks_data = json.load(f)
                 if not isinstance(tasks_data, dict):
                     tasks_data = {}
                 if task_id in tasks_data:
                     tasks_data[task_id]['status'] = status
                     if message: tasks_data[task_id]['message'] = message
                     tasks_data[task_id]['updated_at'] = datetime.now().isoformat()
                     with open(task_log_path, 'w', encoding='utf-8') as f:
                          json.dump(tasks_data, f, ensure_ascii=False, indent=2)
                     logger.info(f"任务 {task_id} 状态已更新为 {status} (无锁)")
                     return True
                 else:
                     logger.warning(f"在任务文件中找不到任务ID: {task_id} (无锁)")
                     return False
             except Exception as e:
                  logger.error(f"无锁更新任务状态时出错: {e}")
                  return False
             # --- 无锁回退结束 ---
        except Exception as e:
             # 捕获其他可能的 filelock 相关错误
             logger.error(f"处理文件锁或读写任务文件时出错: {e}", exc_info=True)
             return False

    except Exception as e:
        # 捕获函数级别的意外错误
        logger.error(f"更新任务状态函数执行时发生意外错误: {e}", exc_info=True)
        return False

def send_to_deepseek(prompt, retry_count=3, timeout=120):
    """
    将构造好的 prompt 发送给 Deepseek，并返回其返回的结果文本。
    增强错误处理和超时机制，并添加重试功能。
    
    Args:
        prompt: 要发送的prompt
        retry_count: 重试次数，默认3次
        timeout: 超时时间，单位秒，默认120秒
    
    Returns:
        API返回的结果文本，如果失败则返回None并记录错误
    """
    # 检查API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-041a37f65bc34e5989a1b71235d6cb62") # Backup key
    if not api_key:
        logger.error("Deepseek API密钥未设置。请设置DEEPSEEK_API_KEY环境变量或在代码中提供")
        return None

    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048
    }
    
    # 记录完整的请求内容（但隐藏API密钥）到主日志
    safe_headers = headers.copy()
    safe_headers["Authorization"] = "Bearer sk-***"
    log_data = {
        "url": api_url,
        "headers": safe_headers,
        "payload": payload # Keep payload for general logger
    }
    logger.info(f"发送到Deepseek的请求（简略）: {json.dumps(log_data, ensure_ascii=False, indent=2)}") # Indent for readability

    # Log complete prompt and payload to deepseek_logger
    deepseek_logger.info(f"--- Deepseek Request ---")
    deepseek_logger.info(f"URL: {api_url}")
    deepseek_logger.info(f"Headers: {json.dumps(safe_headers, indent=2)}")
    deepseek_logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}") # Log full payload with prompt here
    # deepseek_logger.info(f"Prompt:\n{prompt}") # Log prompt separately if needed for very long prompts
    
    current_retry = 0
    while current_retry <= retry_count:
        try:
            logger.debug(f"发送请求到Deepseek API (timeout={timeout}s)... (尝试 {current_retry+1}/{retry_count+1})")
            start_time = time.time()
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            elapsed_time = time.time() - start_time
            logger.debug(f"Deepseek API响应耗时: {elapsed_time:.2f}秒")
            
            # 记录响应状态
            logger.debug(f"Deepseek API响应状态码: {response.status_code}")
            # Log complete response text/json to deepseek_logger regardless of status code for debugging
            response_text = ""
            try:
                 # Try to decode as JSON first
                 res_json = response.json()
                 response_text = json.dumps(res_json, ensure_ascii=False, indent=2)
                 deepseek_logger.info(f"--- Deepseek Response (Status: {response.status_code}) ---\n{response_text}")
            except json.JSONDecodeError:
                 # If not JSON, log raw text
                 response_text = response.text
                 deepseek_logger.info(f"--- Deepseek Response (Status: {response.status_code}, Not JSON) ---\n{response_text}")

            
            # 处理不同的HTTP状态码
            if response.status_code == 200:
                logger.debug("Deepseek API连接成功")
                # res_json already parsed above
                content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "") # Safer access

                if not content:
                     logger.warning("Deepseek API返回成功，但响应内容为空。")
                     # Consider if this should be retried or returned as None/empty string
                     # For now, return empty string to avoid errors in parsing downstream
                     return "" # Return empty string instead of None

                # Log returned content to main logger (optional, as it's in deepseek log)
                # logger.info(f"Deepseek API 返回内容 (前100字符): {content[:100]}...")
                
                return content
            elif response.status_code == 401:
                logger.error("Deepseek API密钥无效或未授权")
                return None # Don't retry on auth errors
            elif response.status_code == 429:
                # Respect Retry-After header if present
                try:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(f"Deepseek API请求频率限制，将在 {retry_after} 秒后重试")
                    time.sleep(retry_after)
                except ValueError:
                     wait_time = min(60, 5 * (current_retry + 1)) # Fallback wait time
                     logger.warning(f"Deepseek API请求频率限制 (无法解析Retry-After)，将在 {wait_time} 秒后重试")
                     time.sleep(wait_time)

                current_retry += 1
                continue # Retry
            # Handle other 4xx/5xx errors
            elif 400 <= response.status_code < 600:
                logger.error(f"Deepseek API请求失败: HTTP {response.status_code}, 响应: {response_text[:500]}") # Log more of the response
                # Decide whether to retry based on status code (e.g., retry on 5xx, not on 4xx)
                if response.status_code >= 500:
                    current_retry += 1
                    if current_retry <= retry_count:
                        wait_time = min(30, 2 ** current_retry)  # 指数退避
                        logger.info(f"等待{wait_time}秒后进行第{current_retry+1}/{retry_count+1}次重试 (服务器错误)")
                        time.sleep(wait_time)
                        continue # Retry
                    else:
                        logger.error(f"达到最大重试次数 ({retry_count})，放弃。")
                        return None # Failed after retries
                else:
                    logger.error("客户端错误，不进行重试。")
                    return None # Don't retry client errors like 400 Bad Request

            # Handle unexpected status codes if any
            else:
                 logger.warning(f"收到意外的 HTTP 状态码: {response.status_code}")
                 current_retry += 1 # Treat as potentially transient
                 if current_retry <= retry_count:
                    wait_time = min(30, 2 ** current_retry)
                    logger.info(f"等待{wait_time}秒后进行第{current_retry+1}/{retry_count+1}次重试 (未知错误)")
                    time.sleep(wait_time)
                    continue # Retry
                 else:
                    logger.error(f"达到最大重试次数 ({retry_count})，放弃。")
                    return None # Failed after retries
                
        except requests.exceptions.Timeout:
            logger.error(f"Deepseek API请求超时（{timeout}秒）")
            current_retry += 1
            if current_retry <= retry_count:
                wait_time = min(30, 2 ** current_retry)
                logger.info(f"等待{wait_time}秒后进行第{current_retry+1}/{retry_count+1}次重试 (超时)")
                time.sleep(wait_time)
            continue
            
        except requests.exceptions.RequestException as e: # Catch broader requests exceptions
            logger.error(f"Deepseek API连接错误: {e}")
            current_retry += 1
            if current_retry <= retry_count:
                wait_time = min(30, 2 ** current_retry)
                logger.info(f"等待{wait_time}秒后进行第{current_retry+1}/{retry_count+1}次重试 (连接错误)")
                time.sleep(wait_time)
            continue
            
        except Exception as e:
            logger.error(f"Deepseek API请求发生未知错误: {e}", exc_info=True)
            current_retry += 1
            if current_retry <= retry_count:
                wait_time = min(30, 2 ** current_retry)
                logger.info(f"等待{wait_time}秒后进行第{current_retry+1}/{retry_count+1}次重试 (未知错误)")
                time.sleep(wait_time)
            continue
    
    logger.error(f"经过{retry_count+1}次尝试后，Deepseek API请求仍然失败")
    return None

def transform_questions(source_file, output_file, progress_callback=None, max_idle_time=600, task_id=None):
    """
    对题库进行变形处理
    
    Args:
        source_file: 源题库JSON文件路径
        output_file: 输出变形后题库的JSON文件路径
        progress_callback: 进度回调函数
        max_idle_time: 最大空闲时间(秒)，超过会被监控器标记为失败
        task_id: 任务ID，用于状态监控
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 创建日志目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs/transformed_logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.info(f"开始/恢复变形任务，输入: {source_file}, 输出: {output_file}, Task ID: {task_id}")
    
    # 如果有任务ID，更新任务状态为运行中 (或根据情况恢复)
    if task_id:
        # 检查是否是从暂停状态恢复
        # 这个逻辑可能更适合放在 app.py 的重试/启动逻辑中
        # 这里仅作状态更新
        update_task_status(task_id, TASK_STATUS['RUNNING'], "开始/恢复变形题目")
    
    # 创建任务监控器
    monitor = TaskMonitor(max_idle_time=max_idle_time, task_id=task_id)

    result = {
         'metadata': {},
         'transformed_at': None, # 将在任务完成时设置
         'source_file': os.path.basename(source_file) if source_file else None,
         'questions': [] # 将从检查点加载或初始化
    }
    questions_to_process = []
    total_questions = 0
    processed_count_in_this_run = 0 # 本次运行处理的数量
    start_index = 0 # 从哪个索引开始处理
    loaded_from_checkpoint = False

    try:
        # --- 检查点加载逻辑 --- 
        if os.path.exists(output_file):
            logger.info(f"检测到已存在的输出文件（检查点）: {output_file}，尝试加载...")
            try:
                with open(output_file, 'r', encoding='utf-8') as f_checkpoint:
                    result = json.load(f_checkpoint)
                if not isinstance(result, dict) or 'questions' not in result or not isinstance(result['questions'], list):
                     logger.warning("检查点文件格式无效，将从头开始。")
                     result = {'metadata': {}, 'questions': []} # 重置 result
                else:
                     loaded_from_checkpoint = True
                     logger.info(f"成功从检查点加载了 {len(result['questions'])} 条已处理的记录。")
                     # 更新元数据中的源文件和任务ID（如果需要）
                     result['source_file'] = os.path.basename(source_file)
                     # result['task_id'] = task_id # 可选
            except json.JSONDecodeError as e:
                logger.warning(f"解析检查点文件JSON失败: {output_file}, Error: {e}. 将从头开始。")
                result = {'metadata': {}, 'questions': []} # 重置 result
            except IOError as e:
                 logger.warning(f"读取检查点文件失败: {output_file}, Error: {e}. 将从头开始。")
                 result = {'metadata': {}, 'questions': []} # 重置 result
        # --- 检查点加载结束 --- 

        # 检查输入文件是否存在 (必须在检查点之后，因为需要原始问题列表)
        if not source_file or not os.path.exists(source_file):
            error_msg = f"输入文件不存在或无效: {source_file}"
            logger.error(error_msg)
            if task_id:
                update_task_status(task_id, TASK_STATUS['FAILED'], error_msg)
            raise FileNotFoundError(error_msg)
        
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            except OSError as e:
                error_msg = f"创建输出目录失败: {output_dir}, Error: {e}"
                logger.error(error_msg)
                if task_id:
                    update_task_status(task_id, TASK_STATUS['FAILED'], error_msg)
                raise # Reraise the error
        
        # 读取原始题目文件
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
        except json.JSONDecodeError as e:
             error_msg = f"解析输入文件JSON失败: {source_file}, Error: {e}"
             logger.error(error_msg)
             if task_id:
                  update_task_status(task_id, TASK_STATUS['FAILED'], error_msg)
             raise # Reraise the error
        except IOError as e:
             error_msg = f"读取输入文件失败: {source_file}, Error: {e}"
             logger.error(error_msg)
             if task_id:
                  update_task_status(task_id, TASK_STATUS['FAILED'], error_msg)
             raise # Reraise the error

        # 获取原始题目列表
        all_source_questions = source_data.get('questions', [])
        total_questions = len(all_source_questions)
        logger.info(f"源文件中共有 {total_questions} 个问题。")

        if total_questions == 0:
             logger.warning("输入文件中没有找到问题。")
             if task_id:
                 update_task_status(task_id, TASK_STATUS['COMPLETED'], "输入文件不包含问题")
             # 写入空的但结构完整的 result
             result['transformed_at'] = datetime.now().isoformat()
             # 创建变形题库自己的元数据，只保留必要信息
             result['metadata'] = {
                 'total_transformed_versions': 0
             }
             try:
                 with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
             except IOError as e:
                    logger.error(f"写入空的完成文件时出错: {e}")
             return # 任务完成

        # 确定从哪里开始处理
        processed_ids = set()
        if loaded_from_checkpoint:
            for processed_item in result['questions']:
                original_q = processed_item.get('original_question')
                if original_q and isinstance(original_q, dict) and 'id' in original_q:
                    processed_ids.add(original_q['id'])
            
            # 找到第一个未处理问题的索引
            for i, question in enumerate(all_source_questions):
                 q_id = question.get('id')
                 if q_id is None or q_id not in processed_ids:
                     start_index = i
                     break
            else: # 如果循环正常结束，说明所有问题都已处理
                 start_index = total_questions 
            
            logger.info(f"根据检查点，将从索引 {start_index} (问题 {start_index + 1}) 开始处理。")
        else:
             # 没有检查点，从头开始
             start_index = 0
             # 初始化变形题库自己的元数据，只保留必要信息
             result['metadata'] = {
                 'total_transformed_versions': 0
             }
             result['questions'] = [] # 确保 questions 列表是空的

        # 需要处理的问题列表
        questions_to_process = all_source_questions[start_index:]
        remaining_count = len(questions_to_process)
        logger.info(f"本次运行需要处理 {remaining_count} 个问题。")

        if remaining_count == 0 and loaded_from_checkpoint:
             logger.info("所有问题已在之前的运行中完成处理。任务完成。")
             if task_id:
                  update_task_status(task_id, TASK_STATUS['COMPLETED'], "所有问题已完成 (从检查点恢复)")
             result['transformed_at'] = result.get('transformed_at') or datetime.now().isoformat() # 保留或设置完成时间
             # 计算总变形版本数
             result['metadata']['total_transformed_versions'] = sum(len(item.get('transformed_versions', [])) for item in result['questions'])
             # 写入最终文件
             try:
                 with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
             except IOError as e:
                 logger.error(f"写入最终完成文件时出错: {e}")
             return # 任务完成

        # 更新元数据 (在开始处理前)
        # 创建变形题库自己的元数据，只保留必要信息
        result['metadata'] = {
            'total_transformed_versions': 0  # 将在任务完成时更新
        }

        # 定义监控回调函数
        def on_task_idle():
            logger.warning("任务监控检测到长时间无进度更新，正在保存中间结果并标记为暂停")
            try:
                if result['questions']: # 确保有内容可保存
                     # 不要在这里更新元数据中的额外字段，保持元数据结构简洁
                     result['metadata']['last_saved_at'] = datetime.now().isoformat()
                     with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                     logger.info(f"已保存中间结果到: {output_file}")
                else:
                     logger.info("没有中间结果需要保存。")
                
                if task_id:
                     update_task_status(task_id, TASK_STATUS['PAUSED'], f"任务超过{max_idle_time}秒无进度，已自动暂停")
                    
            except Exception as e:
                logger.error(f"保存中间结果时出错: {e}", exc_info=True)
                if task_id:
                    update_task_status(task_id, TASK_STATUS['FAILED'], f"自动暂停时保存中间结果失败: {e}")
        
        # 启动监控
        monitor.start(callback=on_task_idle)
        
        # 开始处理剩余的题目
        transformer = QuestionTransformer() # 创建一次实例

        for current_index_in_run, question in enumerate(questions_to_process):
            global_index = start_index + current_index_in_run # 在原始列表中的全局索引
            question_id = question.get('id', f'q_{global_index+1}')
            logger.debug(f"--- 开始处理问题 {global_index+1}/{total_questions} (本次运行第 {current_index_in_run+1}/{remaining_count}): ID={question_id} ---")
            
            monitor.update_progress()
            if not monitor.running:
                 logger.warning(f"监控已停止，提前终止任务 ID: {task_id}")
                 break
            
            try:
                transformer._ensure_model_loaded()
                transformed_versions = transformer.transform_question(question)

                result_item = {
                    'original_question': question,
                    'transformed_versions': transformed_versions if transformed_versions else []
                }
                result['questions'].append(result_item)
                processed_count_in_this_run += 1

                # Log progress and save intermediate results periodically
                # 保存逻辑：每5个 *新处理* 的问题保存一次，或者当处理完最后一个问题时保存
                if processed_count_in_this_run % 5 == 0 or (current_index_in_run + 1) == remaining_count:
                    current_progress_percentage = (global_index + 1) * 100 / total_questions
                    logger.info(f"进度: {global_index+1}/{total_questions} ({current_progress_percentage:.1f}%) - 本次运行已处理 {processed_count_in_this_run}")
                    try:
                        # 更新保存时间，但不添加其他元数据字段
                        result['metadata']['last_saved_at'] = datetime.now().isoformat()
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                            logger.debug(f"已保存中间结果 (完成 {global_index+1}/{total_questions})")
                    except IOError as e:
                         logger.error(f"保存中间结果时出错: {e}")
                         # 继续处理
                
                # 更新进度回调 (基于全局进度)
                if progress_callback:
                    progress = int((global_index + 1) / total_questions * 100)
                    try:
                        progress_callback(progress)
                    except Exception as cb_e:
                         logger.warning(f"执行进度回调时出错: {cb_e}")

            except Exception as e:
                logger.error(f"处理问题 {question_id} (索引 {global_index}) 时发生严重错误: {e}", exc_info=True)
                # 将错误信息记录到结果中，而不是中止整个任务
                error_item = {
                     'original_question': question,
                     'transformed_versions': [],
                     'error': f"处理失败: {str(e)}"
                }
                result['questions'].append(error_item)
                processed_count_in_this_run += 1 # 即使失败，也算作本次运行处理过
                 # 保存包含错误信息的结果，以便后续检查
                try:
                     # 更新保存时间，但不添加其他元数据字段
                     result['metadata']['last_saved_at'] = datetime.now().isoformat()
                     with open(output_file, 'w', encoding='utf-8') as f:
                         json.dump(result, f, ensure_ascii=False, indent=2)
                         logger.debug(f"已保存包含错误信息的结果 (问题 {global_index+1})")
                except IOError as io_e:
                     logger.error(f"保存包含错误信息的中间结果时出错: {io_e}")

        # --- 循环结束后 --- 
        if monitor.running: # 只有在正常完成或处理完所有问题时才标记为 COMPLETED
            final_processed_count = start_index + processed_count_in_this_run
            if final_processed_count == total_questions:
                logger.info(f"所有 {total_questions} 个问题处理完成。")
                if task_id:
                    update_task_status(task_id, TASK_STATUS['COMPLETED'], f"成功完成 {total_questions} 个问题的变形")
                # 设置变形完成时间
                result['transformed_at'] = datetime.now().isoformat()
                # 计算总变形版本数并更新元数据
                result['metadata'] = {
                    'total_transformed_versions': sum(len(item.get('transformed_versions', [])) for item in result['questions'])
                }
                # Final save
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    logger.info(f"最终结果已保存到: {output_file}")
                except IOError as e:
                    logger.error(f"保存最终结果时出错: {e}")
                    if task_id: # 如果最后保存失败，也标记为失败
                         update_task_status(task_id, TASK_STATUS['FAILED'], f"保存最终结果失败: {e}")
            else:
                 # 如果循环结束但未处理完所有问题（例如被外部停止，但 monitor.running 仍然为 True? 不太可能）
                 # 或者因为内部错误跳过了某些问题
                 logger.warning(f"任务处理循环结束，但只处理了 {final_processed_count}/{total_questions} 个问题。检查日志以获取详细信息。")
                 # 可以在这里根据策略决定是标记 FAILED 还是 PAUSED 或其他
                 if task_id:
                      # 检查是否有错误记录
                      has_errors = any('error' in item for item in result['questions'])
                      if has_errors:
                           update_task_status(task_id, TASK_STATUS['FAILED'], f"任务处理完成，但部分问题失败 (已处理 {final_processed_count}/{total_questions})")
                      else: # 如果没有明显错误，可能是被中断？
                           update_task_status(task_id, TASK_STATUS['PAUSED'], f"任务处理中断，已处理 {final_processed_count}/{total_questions}")
        else:
             # Monitor stopped the process (likely idle timeout or external signal)
             # 状态应该已经在 on_task_idle 回调中设置为 PAUSED 或 FAILED
             logger.info(f"任务 {task_id} 因监控停止而结束。")

    except FileNotFoundError:
        # Error already logged and status updated
        pass # Exit gracefully
    except json.JSONDecodeError:
        # Error already logged and status updated
        pass # Exit gracefully
    except IOError:
        # Error already logged and status updated
        pass # Exit gracefully
    except Exception as e:
        # Catch-all for unexpected errors during setup or processing
        error_msg = f"变形任务发生意外严重错误: {e}"
        logger.error(error_msg, exc_info=True)
        if task_id:
            update_task_status(task_id, TASK_STATUS['FAILED'], error_msg)
    finally:
        # 停止监控
        monitor.stop()
        logger.info(f"变形任务 {task_id} 处理结束。")

def parse_deepseek_response(response, question_type, question_id):
    """
    解析 Deepseek API 返回的结果，提取变形后的题目。
    改进了对各种格式的容错性。
    
    Args:
        response: API 返回的响应文本
        question_type: 原始题目类型
        question_id: 原始题目 ID
        
    Returns:
        解析后的变形题目列表 (List[Dict]) 或在严重错误时返回包含错误信息的列表
    """
    logger.debug(f"开始解析题目 {question_id} 的API响应，响应长度: {len(response) if response else 0}字符")
    deepseek_logger.info(f"--- Parsing Response for Question ID: {question_id} ---") # Log to specific file
    deepseek_logger.info(f"Raw Response:\n{response}") # Log raw response being parsed
    
    transformed_versions = []
    
    if not response or not response.strip():
        logger.error(f"题目 {question_id} 的响应为空或仅包含空白")
        # 返回包含错误信息的特定结构，而不是空列表
        return [{
            "transform_method": "解析错误",
            "question": "API响应为空",
            "options": {}, "answer": "", "type": question_type,
            "difficulty": "未知", "original_id": question_id,
            "error": "API response was empty or whitespace."
        }]

    try:
        # Split by the transformation marker "【...】"
        # Using positive lookahead `(?=...)` ensures the delimiter is kept at the start of the next section
        # Handle potential missing spaces around brackets
        transform_sections = re.split(r'(?=【\s*[^】]+\s*】)', response.strip())
        logger.debug(f"响应初步分割成 {len(transform_sections)} 段 (基于 '【...】')")

        section_count = 0
        for i, section_text in enumerate(transform_sections):
            section_text = section_text.strip()
            if not section_text:
                logger.debug(f"跳过第 {i+1} 个空段落")
                continue
                
            section_count += 1
            logger.debug(f"--- 处理第 {section_count} 个有效段落 (原始索引 {i+1}) ---")
            logger.debug(f"段落内容 (前200字符): {section_text[:200]}...")

            parsed_data = {
                "transform_method": "未知",
                "difficulty": "中等", # Default difficulty
                "question": "",
                "options": {}, # Default to empty dict for options
                "answer": "",
                "type": question_type, # Default to original type
                "original_id": question_id,
                "parsing_warnings": [] # Collect warnings during parsing
            }

            try:
                # 1. Extract Transformation Method (【...】)
                method_match = re.match(r'【\s*([^】]+?)\s*】', section_text) # Use match at the start, non-greedy
                if method_match:
                    parsed_data["transform_method"] = method_match.group(1).strip()
                    # Remove the method part from the section text for easier parsing of the rest
                    section_content = section_text[method_match.end():].strip()
                    logger.debug(f"提取到变形方式: '{parsed_data['transform_method']}'")
                else:
                    logger.warning(f"段落 {section_count} 未找到标准 【变形方式】 标记。将尝试从内容推断。")
                    parsed_data["parsing_warnings"].append("Missing 【transform_method】 tag.")
                    # Use the whole section_text if no tag found
                    section_content = section_text
                    # TODO: Add inference logic based on keywords if needed, similar to the original code

                # 2. Extract Difficulty Level (using flexible regex)
                # Handles "难度级别：", "难度级别:", "难度等级：", etc. and variations in spacing, case insensitive
                difficulty_match = re.search(r'(?:难度级别|难度等级)\s*[：:]\s*([^\n]+)', section_content, re.IGNORECASE)
                if difficulty_match:
                    parsed_data["difficulty"] = difficulty_match.group(1).strip()
                    logger.debug(f"提取到难度级别: '{parsed_data['difficulty']}'")
                else:
                     logger.warning(f"段落 {section_count} 未找到明确的 '难度级别：...'。使用默认值 '中等'。")
                     parsed_data["parsing_warnings"].append("Missing '难度级别'.")


                # 3. Extract Question (more robustly, handling multi-line)
                # Looks for 'question[：:]' and captures text until the next known field marker or end of section
                # Excludes lines starting with 'choices', 'options', 'answer', 'type', '难度', '【' (case insensitive)
                question_match = re.search(
                    r'question\s*[：:]\s*((?:.|\n)+?)(?=\n\s*(?:choices|options|answer|type|难度级别|难度等级|【)|$)',
                    section_content, re.IGNORECASE | re.DOTALL)
                if question_match:
                    parsed_data["question"] = question_match.group(1).strip()
                    logger.debug(f"提取到题目: '{parsed_data['question'][:100]}...'")
                else:
                    logger.warning(f"段落 {section_count} 未找到明确的 'question：...'。 题目可能为空。")
                    parsed_data["parsing_warnings"].append("Missing 'question'.")


                # 4. Extract Options (flexible patterns for different formats)
                # Look for 'choices[：:]' or 'options[：:]'
                options_section_match = re.search(
                    r'(?:choices|options)\s*[：:]\s*((?:.|\n)+?)(?=\n\s*(?:question|answer|type|难度级别|难度等级|【)|$)',
                    section_content, re.IGNORECASE | re.DOTALL)

                if options_section_match:
                    options_text = options_section_match.group(1).strip()
                    logger.debug(f"找到选项区域: '{options_text[:100]}...'")
                    parsed_options = {}

                    # Handle explicit NULL/None
                    if options_text.lower() in ['null', 'none', '无']:
                        logger.debug("选项明确标记为 NULL/None/无。")
                        parsed_options = {} # Explicitly empty
                    else:
                        # Try parsing as Python literal first
                        parsed_successfully = False
                        if options_text.startswith('{') and options_text.endswith('}'):
                            try:
                                logger.debug(f"Attempting ast.literal_eval on: {repr(options_text)}") # Log repr
                                potential_dict = ast.literal_eval(options_text)
                                if isinstance(potential_dict, dict):
                                    parsed_options = potential_dict
                                    parsed_successfully = True
                                    logger.debug(f"使用 ast.literal_eval 成功解析选项字典。")
                                else:
                                    logger.warning(f"ast.literal_eval 解析结果不是字典: {type(potential_dict)}")
                            except (ValueError, SyntaxError, MemoryError, RecursionError) as e:
                                # Log the specific error captured
                                logger.warning(f"ast.literal_eval failed with {type(e).__name__}: {e}. Input was: {repr(options_text)}. Will try regex.")
                            except Exception as e: # Catch other potential ast errors
                                logger.error(f"使用 ast.literal_eval 解析选项时发生意外错误: {e}", exc_info=True)


                        # If literal_eval didn't work or wasn't applicable, try regex patterns
                        if not parsed_successfully:
                            logger.debug("ast.literal_eval 未成功或不适用，尝试使用正则表达式解析选项。")
                            # Pattern 1: A. Content B. Content (handles A. A、 A: etc.) separated by newlines or spaces
                            option_pattern1 = re.compile(r'([A-Z])\s*[．.、:：]\s*([^A-Z\n]+)', re.IGNORECASE)
                            matches1 = option_pattern1.findall(options_text)
                            if matches1:
                                logger.debug(f"使用模式1解析选项 (A. B. ...): 找到 {len(matches1)} 个匹配。")
                                for key, value in matches1:
                                    parsed_options[key.upper()] = value.strip()
                                parsed_successfully = True # Mark as success

                            # Pattern 2: A: Content; B: Content (handles separators like ；, ;)
                            if not parsed_options: # Try only if Pattern 1 failed
                                 option_pattern2 = re.compile(r'([A-Z])\s*[：:]\s*(.*?)(?=[；;]\s*[A-Z]\s*[:：]|$)')
                                 matches2 = option_pattern2.findall(options_text)
                                 if matches2:
                                      logger.debug(f"使用模式2解析选项 (A: ...; B: ...): 找到 {len(matches2)} 个匹配。")
                                      for key, value in matches2:
                                           parsed_options[key.upper()] = value.strip()
                                      parsed_successfully = True # Mark as success

                            # Pattern 3: Simple list on newlines without explicit A/B markers (less common for choices)
                            if not parsed_options and '\n' in options_text and len(options_text.split('\n')) > 1:
                                 logger.warning(f"段落 {section_count} 选项格式未知，尝试按换行符分割（无A/B）。")
                                 lines = [line.strip() for line in options_text.split('\n') if line.strip()]
                                 if lines:
                                      # Assign A, B, C...
                                      start_char_code = ord('A')
                                      for idx, line in enumerate(lines):
                                           key = chr(start_char_code + idx)
                                           parsed_options[key] = line
                                      parsed_data["parsing_warnings"].append("Parsed options based on newlines, assigned A, B, C...")
                                      parsed_successfully = True # Mark as success (though format was guessed)


                        # Fallback: If no options parsed but text exists, log warning
                        if not parsed_successfully and options_text: # Check flag and if text existed
                             logger.warning(f"段落 {section_count} 找到了选项文本，但所有解析方法均失败: '{options_text[:100]}...'" )
                             parsed_data["parsing_warnings"].append(f"Could not parse options text using any method: {options_text[:50]}...")
                             # Keep parsed_options empty

                    parsed_data["options"] = parsed_options
                    logger.debug(f"解析得到选项: {parsed_data['options']}")

                else:
                    # No 'choices:' or 'options:' block found
                    logger.debug(f"段落 {section_count} 未找到 'choices:' 或 'options:' 标记。 假设无选项。")
                    # Keep options as default empty dict {}


                # 5. Extract Answer (flexible patterns)
                answer_match = re.search(r'answer\s*[：:]\s*([^\n]+)', section_content, re.IGNORECASE)
                if answer_match:
                    parsed_data["answer"] = answer_match.group(1).strip()
                    logger.debug(f"提取到答案: '{parsed_data['answer']}'")
                else:
                     logger.warning(f"段落 {section_count} 未找到明确的 'answer：...'。 答案可能为空。")
                     parsed_data["parsing_warnings"].append("Missing 'answer'.")


                # 6. Extract Type (Optional)
                type_match = re.search(r'type\s*[：:]\s*([^\n]+)', section_content, re.IGNORECASE)
                if type_match:
                    parsed_data["type"] = type_match.group(1).strip()
                    logger.debug(f"提取到题目类型: '{parsed_data['type']}' (覆盖默认值 {question_type})")


                # Add the successfully parsed (or partially parsed) data to the list
                # Only add if a question was actually found
                if parsed_data["question"]:
                     transformed_versions.append(parsed_data)
                     logger.info(f"成功解析变形版本 {section_count} (方法: {parsed_data['transform_method']}, ID: {question_id})")
                     if parsed_data["parsing_warnings"]:
                          logger.warning(f"解析版本 {section_count} 时出现警告: {parsed_data['parsing_warnings']}")
                else:
                     logger.error(f"未能从段落 {section_count} 中提取到有效的题目内容，跳过此变形版本 (ID: {question_id})。")


            except Exception as section_error:
                logger.error(f"解析题目 {question_id} 的段落 {section_count} 时发生内部错误: {section_error}", exc_info=True)
                # Add an error entry for this section? Or just log?
                # For now, just log and continue to the next section.
        
        # --- Looped through all sections ---

        # If after processing all sections, no valid versions were extracted:
        if not transformed_versions:
            logger.error(f"题目 {question_id}: 响应包含 {section_count} 个段落，但未能成功解析出任何有效的变形题目。")
            # Return a specific error structure instead of default/empty
            return [{
                "transform_method": "解析失败",
                "question": f"未能从API响应中解析出有效的变形题目 (共 {section_count} 段)",
                "options": {}, "answer": "", "type": question_type,
                "difficulty": "未知", "original_id": question_id,
                "error": f"Failed to parse any valid transformed versions from {section_count} sections in the response."
            }]

        logger.info(f"题目 {question_id} 共成功解析出 {len(transformed_versions)} 个变形版本")
        # Log warnings for all versions at the end
        for i, version in enumerate(transformed_versions):
             if version.get("parsing_warnings"):
                  logger.warning(f"版本 {i+1} (方法: {version['transform_method']}) 的解析警告: {version['parsing_warnings']}")
        return transformed_versions
        
    except Exception as e:
        logger.error(f"解析题目 {question_id} 的API响应时发生顶层错误: {e}", exc_info=True)
        # Return a specific error structure
        return [{
            "transform_method": "解析错误",
            "question": f"解析API响应时发生严重错误: {e}",
            "options": {}, "answer": "", "type": question_type,
            "difficulty": "未知", "original_id": question_id,
            "error": f"Top-level parsing error: {e}"
        }]


# 重试任务函数
def retry_task(task_id):
    """
    重试一个任务，重试内容取决于当前任务状态
    - 如果任务状态是'failed'，会尝试从最后一个保存点恢复变形
    - 如果任务尚未有变形结果，但有源文件，则从头开始变形
    - 如果已完成变形但评估失败，则只重新评估
    
    Returns:
        dict: 包含重试状态和消息的字典
    """
    # 配置基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TRANSFORMED_DIR = os.path.join(BASE_DIR, '../../data/transformed')
    EVALUATE_DIR = os.path.join(BASE_DIR, '../../data/transformed_evaluated')
    LOGS_DIR = os.path.join(BASE_DIR, '../../logs/transformed_logs')
    TASKS_LOG_FILE = os.path.join(LOGS_DIR, 'tasks.json')
    QUESTIONS_DIR = os.path.join(BASE_DIR, '../../data')  # 原题库直接使用data目录

    logger.info(f"开始重试任务 {task_id}")

    # 获取任务信息
    try:
        with open(TASKS_LOG_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except Exception as e:
        logger.error(f"读取任务文件失败: {e}")
        return {"status": "error", "message": f"读取任务信息失败: {str(e)}"}

    if task_id not in tasks:
        logger.error(f"找不到任务 {task_id}")
        return {"status": "error", "message": "找不到指定任务"}

    task_info = tasks[task_id]
    current_status = task_info.get('status')
    source_file = task_info.get('source_file')
    transformed_file = task_info.get('transformed_file')

    logger.info(f"任务 {task_id} 当前状态: {current_status}, 源文件: {source_file}, 变形文件: {transformed_file}")

    # 根据当前状态决定重试方式
    if not source_file:
        return {"status": "error", "message": "任务缺少源文件信息，无法重试"}

    source_path = os.path.join(QUESTIONS_DIR, source_file)
    if not os.path.exists(source_path):
        logger.error(f"源文件不存在: {source_path}")
        return {"status": "error", "message": f"源文件不存在: {source_file}"}

    # 更新任务状态为pending（准备重试）
    update_task_status(task_id, TASK_STATUS["PENDING"], "任务准备重试")

    # 此时任务状态已更新为 pending，需要由调用者决定是否立即开始或加入队列
    return {
        "status": "success", 
        "message": "任务已准备重试", 
        "source_file": source_file,
        "current_status": current_status
    }

def fix_transformed_questions(transformed_file, output_file=None):
    """尝试修复变形后的题目文件中可能存在的格式问题
    
    Args:
        transformed_file (str): 变形后题目文件路径
        output_file (str, optional): 修复后输出文件路径，默认覆盖原文件
        
    Returns:
        bool: 是否成功修复
    """
    if not os.path.exists(transformed_file):
        logger.error(f"要修复的文件不存在: {transformed_file}")
        return False
        
    if not output_file:
        output_file = transformed_file
        
    try:
        # 读取原文件
        with open(transformed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 检查和修复结构
        if 'questions' not in data:
            logger.warning(f"文件缺少questions字段: {transformed_file}")
            if 'original_questions' in data and 'transformed_questions' in data:
                # 尝试重构为标准格式
                questions = []
                logger.info("尝试重构为标准格式")
                # ...保持现有的修复逻辑...
                
        # 写入修复后的文件
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"文件修复成功，已保存至: {output_file}")
        return True
    except Exception as e:
        logger.error(f"修复文件时出错: {e}", exc_info=True)
        return False

def main():
    # 参数解析
    parser = argparse.ArgumentParser(description="变形题目")
    parser.add_argument("--input", "-i", type=str, required=True, help="输入题目文件（JSON 格式）")
    parser.add_argument("--output", "-o", type=str, required=True, help="输出变形后题目文件（JSON 格式）")
    parser.add_argument("--device", "-d", type=str, default="cpu", help="使用的设备（CPU/GPU）")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并行处理的线程数")
    args = parser.parse_args()

    # 配置日志，确保使用UTF-8编码
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    file_handler = logging.FileHandler('transformer_standalone.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.addHandler(file_handler)

    # 开始处理
    transform_questions(args.input, args.output)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        if len(sys.argv) < 3:
            print("用法: python transformer.py fix [变形后题目文件路径] [输出文件路径(可选)]")
            sys.exit(1)
        
        transformed_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('transformer_fix.log', encoding='utf-8')
            ]
        )
        
        fixed_count = fix_transformed_questions(transformed_file, output_file)
        print(f"成功修复 {fixed_count} 个题目")
    else:
        main()
