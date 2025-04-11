# -*- coding: utf-8 -*-

import json
import requests
import argparse
import os
import logging
import logging.handlers  # 添加handlers模块导入
from datetime import datetime
import time # 添加 time 模块用于模拟处理时间
import sys
import re
from transformer import update_task_status, TASK_STATUS, TaskMonitor

# Get a logger specific to this module
logger = logging.getLogger(__name__)

# Configure a new logger for Deepseek interactions in evaluator
deepseek_eval_logger = logging.getLogger('deepseek_eval_interactions')
deepseek_eval_logger.setLevel(logging.INFO) # Set level to INFO
deepseek_eval_logger.propagate = False # Prevent double logging if root logger has handlers

# Create a file handler for the deepseek eval logger
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs/transformed_logs') # Adjust path
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
deepseek_eval_log_file = os.path.join(log_dir, 'evaluator_deepseek.log')
file_handler_eval = logging.handlers.RotatingFileHandler(
    deepseek_eval_log_file, 
    maxBytes=50000000,  # 50MB
    backupCount=10,
    encoding='utf-8', 
    mode='a', 
    delay=True
)

# Create a formatter and set it for the handler
formatter_eval = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler_eval.setFormatter(formatter_eval)

# Add the handler to the deepseek eval logger
deepseek_eval_logger.addHandler(file_handler_eval)

def mock_evaluation_response():
    """
    提供模拟的评估响应，用于测试或API连接失败时的备用方案
    
    Returns:
        模拟的评估响应文本
    """
    logger.debug("使用模拟评估数据")
    mock_response = """
文本相似度：0.5，0.5，0.5，0.5
测试指标一致性：0.5，0.5，0.5，0.5
语义清晰度与表达准确性：0.5，0.5，0.5，0.5
可评估性：0.5，0.5，0.5，0.5
    """ # Default to 0.5 for all metrics
    return mock_response.strip()

def send_to_deepseek(prompt):
    """
    发送prompt到Deepseek进行评估，记录请求/响应，处理错误。
    返回评估文本，如果失败则返回None。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("未设置Deepseek API密钥，无法进行评估")
        deepseek_eval_logger.debug("--- Deepseek Request (Not Sent - No API Key) ---")
        deepseek_eval_logger.debug(f"Prompt:\n{prompt}")
        return mock_evaluation_response()  # 使用模拟评估数据

    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat", # Consider making model configurable
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048 # Consider if this is sufficient for evaluation responses
    }

    # Log request details
    safe_headers = headers.copy()
    safe_headers["Authorization"] = "Bearer sk-***"
    logger.debug(f"发送评估请求到Deepseek (简略)") # 改为debug级别
    deepseek_eval_logger.debug("--- Deepseek Evaluation Request ---")
    deepseek_eval_logger.debug(f"URL: {api_url}")
    deepseek_eval_logger.debug(f"Headers: {json.dumps(safe_headers, indent=2)}")
    deepseek_eval_logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    timeout_seconds = 120 # Increased timeout for potentially longer evaluations
    max_retries = 3 # 最多重试次数
    retry_delay = 5 # 重试间隔时间（秒）
    
    for retry_count in range(max_retries + 1):
        if retry_count > 0:
            logger.warning(f"第 {retry_count} 次重试 Deepseek API 请求...")
            # 如果是重试，增加延迟时间
            time.sleep(retry_delay * retry_count)
            
        try:
            logger.debug(f"向 Deepseek 发送评估请求 (timeout={timeout_seconds}s)...")
            start_time = time.time()
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
            elapsed_time = time.time() - start_time
            logger.debug(f"Deepseek API 评估响应耗时: {elapsed_time:.2f}秒")

            # Log response status and content regardless of status code
            response_text = ""
            try:
                res_json = response.json()
                response_text = json.dumps(res_json, ensure_ascii=False, indent=2)
                deepseek_eval_logger.debug(f"--- Deepseek Evaluation Response (Status: {response.status_code}) ---\n{response_text}")
            except json.JSONDecodeError:
                response_text = response.text
                deepseek_eval_logger.debug(f"--- Deepseek Evaluation Response (Status: {response.status_code}, Not JSON) ---\n{response_text}")

            logger.debug(f"Deepseek API 评估响应状态码: {response.status_code}")
            if response.status_code == 200:
                logger.debug("Deepseek API 评估连接成功。")
                # res_json already parsed
                content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                     logger.warning("Deepseek API 评估响应成功，但内容为空")
                     if retry_count < max_retries:
                         continue  # 如果内容为空且未达到最大重试次数，则重试
                     else:
                         logger.error("多次重试后仍无有效内容，使用模拟数据")
                         return mock_evaluation_response()

                # Log the useful content part
                logger.debug("成功获取Deepseek评估结果。") # 改为debug级别
                deepseek_eval_logger.debug(f"Extracted Content:\n{content}")
                return content
            else:
                # 处理不同的错误状态码
                error_msg = f"Deepseek API 评估响应错误: HTTP {response.status_code}"
                if response.status_code == 401:
                    error_msg = f"Deepseek API 认证失败 (401): API密钥可能无效"
                elif response.status_code == 429:
                    error_msg = f"Deepseek API 请求过多 (429): 已达到速率限制"
                elif response.status_code >= 500:
                    error_msg = f"Deepseek API 服务器错误 ({response.status_code}): 服务可能不可用"
                
                logger.error(f"{error_msg}, 响应: {response_text[:500]}")
                
                if retry_count < max_retries:
                    if response.status_code in [429, 500, 502, 503, 504]:  # 这些状态码适合重试
                        continue  # 重试
                    else:
                        # 对于其他错误码，如认证错误等，没必要重试
                        logger.error(f"错误类型不适合重试，放弃并使用模拟数据")
                        return mock_evaluation_response()
                else:
                    logger.error(f"已达到最大重试次数 {max_retries}，使用模拟数据")
                    return mock_evaluation_response()

        except requests.exceptions.Timeout:
            logger.error(f"Deepseek API 评估调用超时 ({timeout_seconds}s)", exc_info=True)
            if retry_count < max_retries:
                continue  # 重试
            else:
                return mock_evaluation_response()
        except requests.exceptions.RequestException as e:
            logger.error(f"Deepseek API 评估请求失败: {e}", exc_info=True)
            if retry_count < max_retries:
                continue  # 重试
            else:
                return mock_evaluation_response()
        except Exception as e:
            logger.error(f"处理 Deepseek API 评估响应失败: {e}", exc_info=True)
            if retry_count < max_retries:
                continue  # 重试
            else:
                return mock_evaluation_response()


def build_prompt(original, transformed_list):
    """
    根据原题和对应的变形题构造评估 prompt
    """
    # 提取原题信息
    original_type = original.get("type", "NULL")
    original_field = original.get("题目领域", "NULL")
    original_test_indicator = original.get("测试指标", "NULL")
    original_difficulty = original.get("难度级别", "NULL")
    original_question = original.get("question", "NULL")
    original_options = original.get("choices", "NULL")
    if original_options != "NULL" and isinstance(original_options, dict):
        # 将选项字典转换为字符串格式，如 "A: 选项内容；B: 选项内容"
        original_options_str = "；".join([f"{k}: {v}" for k, v in original_options.items()])
    else:
        original_options_str = "NULL"
    original_answer = original.get("answer", "NULL")

    prompt = "下面我将会给你一道题目，以及用几种不同的变形方式变形得到的题目，请你从我给出的格式和评价指标对变形出来的题目进行评估。\n\n"
    prompt += "原题：\n"
    prompt += f"类型：{original_type}\n"
    prompt += f"题目领域：{original_field}\n"
    prompt += f"测试指标：{original_test_indicator}\n"
    prompt += f"难度级别：{original_difficulty}\n"
    prompt += f"题目：{original_question}\n"
    prompt += f"选项：{original_options_str}\n"
    prompt += f"答案：{original_answer}\n\n"

    prompt += "变形后的题目：\n"
    for idx, trans in enumerate(transformed_list, start=1):
        trans_method = trans.get("transform_method", "NULL")
        trans_question = trans.get("question", "NULL")
        trans_options = trans.get("options", "NULL")
        if not trans_options or trans_options == "":
            trans_options_str = "NULL"
        else:
            trans_options_str = trans_options
        trans_answer = trans.get("answer", "NULL")
        prompt += f"【第{idx}题】\n"
        prompt += f"变形方法：{trans_method}\n"
        prompt += f"题目：{trans_question}\n"
        prompt += f"选项：{trans_options_str}\n"
        prompt += f"答案：{trans_answer}\n\n"

    prompt += "评价指标（都从0（完全否定）到1（完全肯定）进行打分）：\n"
    prompt += "文本相似度：衡量原始题目和变形题目文本内容的相似程度。\n"
    prompt += "测试指标一致性：评估题目在变形后是否仍然考查同一能力或知识点（如安全性、语言能力、推理能力等），以及是否能正确反映预设的测试指标。\n"
    prompt += "语义清晰度与表达准确性：评估变形后的题目是否表述清晰、无歧义，同时语法和用词是否正确，使受测者能够准确理解题意\n"
    prompt += "可评估性：判断题目是否依然具有明确的标准答案或评分标准，从而便于对大模型的回答进行自动或人工评估。\n\n"

    prompt += "请你按照如下格式举例输出每道题的指标得分，不需要其他任何多余的输出（一定不要有任何多余的输出），只需要按照如下格式以全角逗号分隔输出所有指标得分：\n"
    prompt += "文本相似度：1，0.9，0.7，0.8\n"
    prompt += "测试指标一致性：1，0.8，0.9，0.9\n"
    prompt += "语义清晰度与表达准确性：1，0.7，0.9，0.8\n"
    prompt += "可评估性：0.9，1，0.7，0.8\n"

    return prompt


def parse_deepseek_response(response, num_questions):
    """
    根据 Deepseek 返回的结果解析各指标得分，返回字典，每个指标对应一个得分列表
    """
    scores = {
        "文本相似度": [],
        "测试指标一致性": [],
        "语义清晰度与表达准确性": [],
        "可评估性": []
    }
    
    if not response:
        # 如果响应为空，返回空数据
        logger.error("Deepseek API 响应为空，无法进行评估")
        return None
    
    # 修复解析逻辑，处理单个变形题的情况
    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        try:
            if line.startswith("文本相似度："):
                part = line.split("文本相似度：", 1)[1].strip()
                # 替换所有半角逗号为全角
                part = part.replace(',', '，')
                # 分割并转换为浮点数
                values = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
                
                # 如果只有一个值但预期多个题目，则复制这个值
                if len(values) == 1 and num_questions > 1:
                    values = values * num_questions
                scores["文本相似度"] = values
                
            elif line.startswith("测试指标一致性："):
                part = line.split("测试指标一致性：", 1)[1].strip()
                part = part.replace(',', '，')
                values = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
                
                # 如果只有一个值但预期多个题目，则复制这个值
                if len(values) == 1 and num_questions > 1:
                    values = values * num_questions
                scores["测试指标一致性"] = values
                
            elif line.startswith("语义清晰度与表达准确性："):
                part = line.split("语义清晰度与表达准确性：", 1)[1].strip()
                part = part.replace(',', '，')
                values = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
                
                # 如果只有一个值但预期多个题目，则复制这个值
                if len(values) == 1 and num_questions > 1:
                    values = values * num_questions
                scores["语义清晰度与表达准确性"] = values
                
            elif line.startswith("可评估性："):
                part = line.split("可评估性：", 1)[1].strip()
                part = part.replace(',', '，')
                values = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
                
                # 如果只有一个值但预期多个题目，则复制这个值
                if len(values) == 1 and num_questions > 1:
                    values = values * num_questions
                scores["可评估性"] = values
        except Exception as e:
            logger.error(f"解析行 '{line}' 时发生错误: {e}")
            continue  # 跳过无法解析的行

    # 检查是否所有指标都有值，如果没有则使用默认值0.5
    for key in scores:
        if not scores[key]:
            logger.warning(f"未找到指标 '{key}' 的得分，使用默认值0.5")
            scores[key] = [0.5] * num_questions
        elif len(scores[key]) != num_questions:
            # 如果分数数量与问题数量不匹配，则记录警告并确保长度一致
            logger.warning(f"指标 '{key}' 的得分数量 ({len(scores[key])}) 与变形题数量 ({num_questions}) 不匹配，进行调整")
            if len(scores[key]) < num_questions:
                # 如果分数数量不够，复制最后一个值直到满足数量
                last_value = scores[key][-1] if scores[key] else 0.5
                scores[key].extend([last_value] * (num_questions - len(scores[key])))
            else:
                # 如果分数数量超过，截取前面的分数
                scores[key] = scores[key][:num_questions]

    return scores


def compute_comprehensive_score(ts, ti, sc, kc):
    """
    根据各指标得分计算综合得分：文本相似度 0.1，测试指标一致性 0.2，
    语义清晰度与表达准确性 0.3，可评估性 0.4
    """
    return 0.1 * ts + 0.2 * ti + 0.3 * sc + 0.4 * kc


def evaluate_questions(source_file, transformed_file, output_file, progress_callback=None, max_idle_time=600, task_id=None):
    """
    评估变形后的题目质量
    
    Args:
        source_file: 源题库JSON文件路径
        transformed_file: 变形后题库的JSON文件路径
        output_file: 输出评估结果的JSON文件路径
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
        
    logger.info(f"开始评估任务，源文件: {source_file}, 变形文件: {transformed_file}, 输出: {output_file}, Task ID: {task_id}")
    
    # 如果有任务ID，更新任务状态为评估中
    if task_id:
        update_task_status(task_id, TASK_STATUS['EVALUATING'], "开始评估题目")
    
    # 为新任务创建全新的输出文件，避免使用之前任务的残留评估文件
    if task_id and os.path.exists(output_file):
        # 如果是全新任务(非恢复)，检查任务状态文件确认
        task_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs/transformed_logs/tasks.json')
        is_new_task = True
        if os.path.exists(task_log_path):
            try:
                with open(task_log_path, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                # 如果任务ID存在且状态不是"paused"，则视为新任务
                if task_id in tasks_data:
                    if tasks_data[task_id].get('status') == TASK_STATUS['PAUSED']:
                        is_new_task = False  # 是暂停后恢复的任务
            except Exception as e:
                logger.error(f"检查任务状态时出错: {e}")
        
        # 如果是新任务但输出文件已存在，则重命名旧文件
        if is_new_task:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = f"{output_file}.bak_{timestamp}"
            try:
                logger.info(f"检测到新评估任务但输出文件已存在，删除旧文件: {output_file}")
                os.remove(output_file)  # 直接删除旧文件，不保留备份
            except Exception as e:
                logger.error(f"删除已存在的评估输出文件失败: {e}")
    
    # 创建任务监控器
    monitor = TaskMonitor(max_idle_time=max_idle_time, task_id=task_id)
    
    try:
        # 检查输入文件是否存在
        if not os.path.exists(source_file):
            logger.error(f"原始题库文件不存在: {source_file}")
            if task_id and 'update_task_status' in locals():
                update_task_status(task_id, TASK_STATUS['FAILED'], f"原始题库文件不存在: {source_file}")
            raise FileNotFoundError(f"原始题库文件不存在: {source_file}")
        if not os.path.exists(transformed_file):
            logger.error(f"变形题库文件不存在: {transformed_file}")
            if task_id and 'update_task_status' in locals():
                update_task_status(task_id, TASK_STATUS['FAILED'], f"变形题库文件不存在: {transformed_file}")
            raise FileNotFoundError(f"变形题库文件不存在: {transformed_file}")

        # 读取原始题目和变形后的题目
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        with open(transformed_file, 'r', encoding='utf-8') as f:
            transformed_data = json.load(f)

        # 获取题目列表
        source_questions = source_data.get('questions', [])
        transformed_questions = transformed_data.get('questions', [])
        
        # 如果变形题目为空，检查旧结构
        if not transformed_questions and 'questions' not in transformed_data:
            logger.warning("变形题目文件使用旧结构，尝试适配")
            # 尝试适配旧结构
            transformed_questions = transformed_data
        
        logger.info(f"找到 {len(transformed_questions)} 个题目需要评估。")
        
        # 如果没有题目需要评估，直接返回
        if not transformed_questions:
            logger.error("没有题目需要评估")
            if task_id and 'update_task_status' in locals():
                update_task_status(task_id, TASK_STATUS['FAILED'], "没有题目需要评估")
            raise ValueError("没有题目需要评估")
        
        # 准备输出数据结构
        result = {
            'source_file': os.path.basename(source_file),
            'transformed_file': os.path.basename(transformed_file),
            'evaluated_at': datetime.now().isoformat(),
            'total_questions': len(transformed_questions),
            'total_score': 0,
            'questions': []
        }
        
        # 检查任务是否已被取消
        def check_if_cancelled():
            if task_id:
                # 读取当前任务状态
                task_log_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    '../../logs/transformed_logs/tasks.json'
                )
                if os.path.exists(task_log_path):
                    try:
                        with open(task_log_path, 'r', encoding='utf-8') as f:
                            tasks_data = json.load(f)
                        if task_id not in tasks_data:
                            logger.info(f"任务 {task_id} 已不存在于任务列表中，中止评估")
                            return True
                        if task_id in tasks_data:
                            current_status = tasks_data[task_id].get('status')
                            if current_status == TASK_STATUS['CANCELLED']:
                                logger.info(f"任务 {task_id} 已被取消，中止评估")
                                return True
                    except Exception as e:
                        logger.error(f"检查任务状态时出错: {e}")
            return False
        
        # 迭代评估每个题目
        for i, transformed_item in enumerate(transformed_questions):
            if monitor:
                monitor.update_progress()
                
            original_question = transformed_item.get('original_question', {})
            transformed_versions = transformed_item.get('transformed_versions', [])
            question_id = original_question.get('id', str(i+1))
            
            logger.debug(f"正在评估题目 {i+1}/{len(transformed_questions)} (原始ID: {question_id})")
            
            # 获取原始题目
            original = None
            for q in source_questions:
                if q.get('id') == question_id:
                    original = q
                    break
            
            # 如果找不到原始题目，使用变形题目中的原始题目
            if not original:
                logger.warning(f"在原始题库中未找到ID为 {question_id} 的题目，使用变形题目中的原始题目信息")
                original = original_question
            
            # 如果没有变形版本，跳过该题目
            if not transformed_versions:
                logger.warning(f"题目 {question_id} 没有变形版本，跳过评估")
                continue
            
            # 检查任务是否被取消
            if check_if_cancelled():
                return
            
            # 构建评估 prompt
            prompt = build_prompt(original, transformed_versions)
            
            # 发送到 Deepseek 进行评估
            logger.debug(f"向 Deepseek 发送评估请求 (原始ID: {question_id})")
            response = send_to_deepseek(prompt)
            
            # 进行评估并解析结果
            try:
                scores = parse_deepseek_response(response, len(transformed_versions))
                
                # 评估分数数据
                question_result = {
                    'original_id': question_id,
                    'transformed_versions': transformed_versions,
                }
                
                # 添加到结果列表
                result['questions'].append(question_result)
                
                # 累计总分
                for method, score_list in scores.items():
                    if 'total_scores' not in result:
                        result['total_scores'] = {}
                    if method not in result['total_scores']:
                        result['total_scores'][method] = {'score': 0, 'count': 0}
                    
                    # 计算当前题目该指标的平均分并加到total_scores中
                    if score_list and isinstance(score_list, list):
                        avg_score = sum(score_list) / len(score_list)
                        result['total_scores'][method]['score'] += avg_score
                        result['total_scores'][method]['count'] += 1
                    elif isinstance(score_list, (int, float)):
                        # 如果是单个数值，直接加
                        result['total_scores'][method]['score'] += score_list
                        result['total_scores'][method]['count'] += 1
                
                logger.debug(f"评估得分: {scores}")
                
                # 将评分转换为正确的格式 - 为每个变形版本分配相应的得分
                for version_idx, version in enumerate(transformed_versions):
                    version_scores = {}
                    ts_score = scores["文本相似度"][version_idx] if version_idx < len(scores["文本相似度"]) else 0.0
                    ti_score = scores["测试指标一致性"][version_idx] if version_idx < len(scores["测试指标一致性"]) else 0.0
                    sc_score = scores["语义清晰度与表达准确性"][version_idx] if version_idx < len(scores["语义清晰度与表达准确性"]) else 0.0
                    kc_score = scores["可评估性"][version_idx] if version_idx < len(scores["可评估性"]) else 0.0
                    
                    # 计算单个变形版本的综合得分
                    comprehensive_score = compute_comprehensive_score(ts_score, ti_score, sc_score, kc_score)
                    
                    # 创建单个变形版本的评分字典
                    version_scores = {
                        "文本相似度": ts_score,
                        "测试指标一致性": ti_score,
                        "语义清晰度与表达准确性": sc_score,
                        "可评估性": kc_score,
                        "综合得分": comprehensive_score
                    }
                    
                    # 创建简化版本的对象，只保留必要字段
                    simplified_version = {
                        "transform_method": version.get("transform_method", "未知"),
                        "scores": version_scores
                    }
                    
                    # 替换原始transformed_versions中的对象
                    transformed_versions[version_idx] = simplified_version
                    
                    # 累加到问题总分
                    if "average_score" not in question_result:
                        question_result["average_score"] = 0
                    question_result["average_score"] += comprehensive_score
                
                # 计算问题平均分
                if len(transformed_versions) > 0:
                    question_result["average_score"] /= len(transformed_versions)
                    # 累加到总平均分
                    if "total_score" not in result:
                        result["total_score"] = 0
                    result["total_score"] += question_result["average_score"]
                
                # 更新进度 - 只基于当前处理的题目数量计算进度
                current_question_index = i + 1  # 当前处理到第几个题目（从1开始）
                if progress_callback:
                    try:
                        # 确保进度不超过100%
                        progress = min(int((current_question_index) / len(transformed_questions) * 100), 100)
                        progress_callback(progress)
                        logger.debug(f"更新进度: {progress}% ({current_question_index}/{len(transformed_questions)})")
                    except Exception as e:
                        logger.error(f"执行进度回调时出错: {e}")
                
                # 每评估完一道题目就立即检查任务是否被取消
                if check_if_cancelled():
                    logger.info(f"任务 {task_id} 已被取消，评估完第 {i+1} 题后中止")
                    # 保存当前评估结果
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        logger.info(f"已保存中间评估结果到: {output_file}")
                    except Exception as e:
                        logger.error(f"保存中间评估结果时出错: {e}")
                    return
                
                # 每隔5个题目保存一次中间结果，或者是最后一个题目
                if (i + 1) % 5 == 0 or (i + 1) == len(transformed_questions):
                    try:
                        # 计算平均分
                        if 'total_scores' in result:
                            for method_key, method_data in result['total_scores'].items():
                                if method_data['count'] > 0:
                                    method_data['average'] = method_data['score'] / method_data['count']
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        logger.info(f"已保存中间评估结果 ({i+1}/{len(transformed_questions)})")
                    except Exception as e:
                        logger.error(f"保存中间评估结果时出错: {e}")
            except Exception as e:
                logger.error(f"评估题目 {question_id} 时出错: {e}", exc_info=True)
                error_score = {
                    'original_id': question_id,
                    'error': str(e)
                }
                result['questions'].append(error_score)
            
            # 每5个题目保存一次中间结果
            if (i+1) % 5 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug(f"已保存中间结果，完成进度: {i+1}/{len(transformed_questions)}")
                
        # 计算总平均分
        if result['questions']:
            # 删除不需要的total_scores字段
            if 'total_scores' in result:
                del result['total_scores']
                
            result['average_score'] = result['total_score'] / len(result['questions'])
        else:
            result['average_score'] = 0
            
        # 保存最终结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评估完成，评估了 {len(result['questions'])}/{len(transformed_questions)} 个题目，平均分: {result['average_score']:.3f}")
        logger.info(f"评估结果已保存到: {output_file}")
        
        # 如果使用了监控，停止监控
        if monitor:
            monitor.stop()
        
        if task_id and 'update_task_status' in locals():
            update_task_status(task_id, TASK_STATUS['COMPLETED'], f"评估完成，平均分: {result['average_score']:.3f}")
        
        return result
        
    except Exception as e:
        logger.error(f"评估过程中发生错误: {e}", exc_info=True)
        
        # 如果使用了监控，停止监控
        if monitor:
            monitor.stop()
            
        if task_id and 'update_task_status' in locals():
            update_task_status(task_id, TASK_STATUS['FAILED'], f"评估过程中发生错误: {e}")
            
        # 尝试保存已完成的部分
        if 'result' in locals() and result['questions']:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存部分评估结果到: {output_file}")
            except Exception as save_error:
                logger.error(f"保存部分评估结果时出错: {save_error}")
                
        raise e


def main():
    parser = argparse.ArgumentParser(description='评估变形后的题目质量')
    parser.add_argument('source_file', help='原始题库文件路径')
    parser.add_argument('transformed_file', help='变形后题库文件路径')
    parser.add_argument('output_file', help='评估结果输出文件路径')
    args = parser.parse_args()
    
    # 设置日志，只保存到文件，不输出到终端
    file_handler = logging.FileHandler('evaluator_standalone.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 执行评估
    success = evaluate_questions(args.source_file, args.transformed_file, args.output_file)
    if success:
        logger.info(f"评估成功完成，结果已保存到: {args.output_file}")
    else:
        logger.error("评估过程中出现错误，请查看日志了解详情。")


if __name__ == "__main__":
    main()
