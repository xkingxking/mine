# -*- coding: utf-8 -*-

import json
import os
import re
from typing import List, Dict, Any
import requests
import logging

logging.basicConfig(
    filename='transformer.log',         # 日志文件名
    level=logging.DEBUG,        # 日志级别
    format='%(asctime)s %(levelname)s: %(message)s'  # 输出格式，包含时间戳
)


# 各题型基础 prompt 模板
BASE_PROMPT_TEMPLATES = {
    "choice": (
        "请按照如下格式返回你的所有结果，不要有任何多余的输出（任何都不需要，包括多余的括号），只需要按照格式连续的输出通过我要求的所有变形方式生成的题干、选项和答案。格式如下，括号范围是你填写内容的范围：\n"
        "“【（变形方式）】\n"
        "难度级别：（请在此处输出你认为你变形后的题目的难度，分为简单/中等/困难）\n"
        "question：（请在此处输出你变形后的题干）\n"
        "choices：（请在此处输出你变形后的选项）\n"
        "answer：（请在此处输出题目的答案，请以选项的标号表示，如A/B/C/D等）”\n"
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
        "answer：（请在此处输出题目的答案）”\n"
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
        "answer：（请在此处输出题目的答案）”\n"
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
        "answer：（请在此处输出题目的答案，如果有选项选择请以选项的标号表示，如A/B/C/D等）”\n"
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
        "answer：（请在此处输出题目的答案）”\n"
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
        "answer：（请在此处输出题目的答案）”\n"
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
            api_key = os.environ.get("DEEPSEEK_API_KEY")
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
                    "max_tokens": 2048
                }
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=10)
                    logging.debug(f"API请求返回状态码：{response.status_code}")
                    if response.status_code == 200:
                        logging.debug("Deepseek API 连接成功。")
                    response.raise_for_status()
                    res_json = response.json()
                    content = res_json["choices"][0]["message"]["content"]
                    return content
                except Exception as e:
                    logging.error(f"Deepseek API 连接失败：{e}")
                    raise e

            self._pipeline = chat_completion

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
        对单个题目应用变形：
        - 根据题目类型选择对应的基础 prompt 模板，并填充题目内容。
        - 根据题型调用各具体变形方法 prompt 函数，拼接各个变形方法的 prompt。
        - 最后追加通用变形方法 prompt。
        - 调用 Deepseek API 进行变形，并解析返回结果生成各变形后的题目列表，
          每个变形后的题目中添加 original_id 和 transform_method 字段。
        """
        results = []
        q_type = question.get("type", "choice")
        # 获取对应基础 prompt 模板
        template = BASE_PROMPT_TEMPLATES.get(q_type)
        if not template:
            raise ValueError(f"不支持的题型: {q_type}")

        # 处理 choices 字段：如果为选择题或场景题，则将选项字典转换为“；”连接的字符串；否则填 "None"
        if q_type in ["choice", "scenario"]:
            choices = question.get("choices")
            if choices and isinstance(choices, dict):
                choices_str = "；".join(choices.values())
            else:
                choices_str = "None"
        else:
            choices_str = "None"

        # 构造 prompt 参数字典
        prompt_params = {
            "题目领域": question.get("题目领域", ""),
            "测试指标": question.get("测试指标", ""),
            "难度级别": question.get("难度级别", ""),
            "question": question.get("question", ""),
            "choices": choices_str,
            "answer": question.get("answer", "")
        }

        # 基础 prompt（包含题目信息）
        base_prompt = template.format(**prompt_params)

        # 调用对应题型的变形方法函数，拼接各个方法的 prompt
        method_funcs = TRANSFORMATION_PROMPTS.get(q_type, [])
        method_prompts = "\n".join([func() for func in method_funcs])

        # 拼接完整的 prompt：基础 prompt + 变形方法 prompt + 通用变形方法 prompt
        full_prompt = base_prompt + "\n" + method_prompts + "\n" + COMMON_PROMPT

        # print("Debug - Full unified prompt:")
        # print(full_prompt)

        self._ensure_model_loaded()
        api_response = self._pipeline(full_prompt)
        raw_output = api_response.strip()
        # print("Debug - Unified model output:")
        # print(raw_output)

        # 按 "【" 标记分割各变形结果
        sections = re.split(r"(?=【)", raw_output)
        for section in sections:
            section = section.strip()
            if not section:
                continue
            parsed = self.parse_transformed_section(section)
            # 若返回中未包含 type 信息，则默认保持原题型
            if "type" not in parsed:
                parsed["type"] = q_type
            # 如果 options 字段为空或为 "None"，则置为 None
            if "options" in parsed and (parsed["options"] is None or parsed["options"].strip().lower() == "none"):
                parsed["options"] = None
            # 添加原题 id 字段（使用 original_id）
            parsed["original_id"] = question.get("id", "")
            results.append(parsed)
        return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="自动题目变形")
    parser.add_argument("--input", "-i", type=str, required=True, help="输入题目文件（JSON 格式）")
    parser.add_argument("--output", "-o", type=str, required=True, help="输出变形题目文件（JSON 格式）")
    parser.add_argument("--workers", "-w", type=int, default=1, help="并行处理的线程数")
    args = parser.parse_args()

    questions = []
    # 根据文件后缀判断读取方式
    if args.input.endswith(".json"):
        with open(args.input, 'r', encoding='utf-8') as fin:
            data = json.load(fin)
            q_list = data.get("questions", [])
            for q in q_list:
                # 添加 original_id 字段，使用原题 id
                q["original_id"] = q.get("id", "")
                questions.append(q)
    else:
        # 若为 jsonl 格式
        with open(args.input, 'r', encoding='utf-8') as fin:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    q = json.loads(line)
                except json.JSONDecodeError:
                    continue
                q["original_id"] = q.get("id", "")
                questions.append(q)

    transformer = QuestionTransformer()
    output_results = []

    if args.workers and args.workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results_by_index = {}

        def process_question(q):
            return transformer.transform_question(q)

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_index = {executor.submit(process_question, q): q.get("id", "") for q in questions}
            for future in as_completed(future_to_index):
                orig_id = future_to_index[future]
                try:
                    res_list = future.result()
                except Exception as e:
                    res_list = [{"original_id": orig_id, "transform_method": "未知", "error": str(e)}]
                results_by_index[orig_id] = res_list
        # 按原题 id 顺序输出
        for q in questions:
            orig_id = q.get("id", "")
            for item in results_by_index.get(orig_id, []):
                output_results.append(item)
    else:
        for q in questions:
            res_list = transformer.transform_question(q)
            output_results.extend(res_list)

    with open(args.output, 'w', encoding='utf-8') as fout:
        for item in output_results:
            fout.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
