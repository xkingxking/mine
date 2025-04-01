# -*- coding: utf-8 -*-

import json
import requests
import argparse
import os
import logging

logging.basicConfig(
    filename='evaluator.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def send_to_deepseek(prompt):
    """
    将构造好的 prompt 发送给 Deepseek，并返回其返回的结果文本。
    Deepseek 的 API key 从环境变量 DEEPSEEK_API_KEY 获取，并在请求头中携带该 key。
    使用官方接口：https://api.deepseek.com/v1/chat/completions
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未设置 Deepseek 的 API key，请设置环境变量 DEEPSEEK_API_KEY")

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
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        logging.debug(f"API请求返回状态码：{response.status_code}")
        if response.status_code == 200:
            logging.debug("Deepseek API 连接成功。")
        response.raise_for_status()
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        logging.error(f"Deepseek API 连接失败：{e}")
        return ""


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
    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        try:  # 添加异常处理
            if line.startswith("文本相似度："):
                part = line.split("文本相似度：", 1)[1].strip()
                # 替换所有半角逗号为全角
                part = part.replace(',', '，')
                scores["文本相似度"] = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
            elif line.startswith("测试指标一致性："):
                part = line.split("测试指标一致性：", 1)[1].strip()
                part = part.replace(',', '，')
                scores["测试指标一致性"] = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
            elif line.startswith("语义清晰度与表达准确性："):
                part = line.split("语义清晰度与表达准确性：", 1)[1].strip()
                part = part.replace(',', '，')
                scores["语义清晰度与表达准确性"] = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
            elif line.startswith("可评估性："):
                part = line.split("可评估性：", 1)[1].strip()
                part = part.replace(',', '，')
                scores["可评估性"] = [float(x.strip()) for x in part.split("，") if x.strip() != ""]
        except Exception as e:
            logging.error(f"解析行 '{line}' 时发生错误: {e}")
            continue  # 跳过无法解析的行

    # 验证每个指标的数量是否匹配变形题数量
    for key in scores:
        if len(scores[key]) != num_questions:
            logging.warning(f"指标 '{key}' 的得分数量 ({len(scores[key])}) 与变形题数量 ({num_questions}) 不匹配")

    return scores


def compute_comprehensive_score(ts, ti, sc, kc):
    """
    根据各指标得分计算综合得分：文本相似度 0.1，测试指标一致性 0.2，
    语义清晰度与表达准确性 0.3，可评估性 0.4
    """
    return 0.1 * ts + 0.2 * ti + 0.3 * sc + 0.4 * kc


def main():
    parser = argparse.ArgumentParser(description="自动题目评估")
    parser.add_argument("--original", "-ori", type=str, required=True, help="输入原题目文件（JSON 格式）")
    parser.add_argument("--transformed", "-t", type=str, required=True, help="输入变形题目文件（JSON 格式）")
    parser.add_argument("--output", "-o", type=str, required=True, help="输出评估结果文件（JSON 格式）")
    parser.add_argument("--workers", "-w", type=int, default=1, help="并行处理的线程数")
    args = parser.parse_args()

    # 读取原题库
    with open(args.original, "r", encoding="utf-8") as f:
        original_data = json.load(f)
    original_questions = original_data.get("questions", [])

    # 读取变形题库（支持 JSON 数组或逐行 JSON 格式）
    transformed_questions = []
    with open(args.transformed, "r", encoding="utf-8") as f:
        try:
            transformed_questions = json.load(f)
        except Exception:
            f.seek(0)
            for line in f:
                if line.strip():
                    transformed_questions.append(json.loads(line.strip()))

    # 按原题 id 对变形题进行分组
    transformed_group = {}
    for tq in transformed_questions:
        original_id = tq.get("original_id")
        if original_id not in transformed_group:
            transformed_group[original_id] = []
        transformed_group[original_id].append(tq)

    evaluation_results = []
    all_comprehensive_scores = []

    # 针对每一道原题及其对应的变形题构造 prompt 并调用 Deepseek 进行评估
    for original in original_questions:
        orig_id = original.get("id")
        if orig_id in transformed_group:
            transformed_list = transformed_group[orig_id]
            prompt = build_prompt(original, transformed_list)

            # 调用 Deepseek 接口发送 prompt，获取返回结果
            response = send_to_deepseek(prompt)
            if not response:
                print(f"原题 ID {orig_id} 的评估未获得返回结果，跳过。")
                continue

            num_transformed = len(transformed_list)
            scores = parse_deepseek_response(response, num_transformed)
            # 针对每个变形题，计算综合得分，并记录详细信息
            for i in range(num_transformed):
                ts = scores["文本相似度"][i] if i < len(scores["文本相似度"]) else 0
                ti = scores["测试指标一致性"][i] if i < len(scores["测试指标一致性"]) else 0
                sc = scores["语义清晰度与表达准确性"][i] if i < len(scores["语义清晰度与表达准确性"]) else 0
                kc = scores["可评估性"][i] if i < len(scores["可评估性"]) else 0
                comprehensive = compute_comprehensive_score(ts, ti, sc, kc)
                result = {
                    "original_id": orig_id,
                    "transform_method": transformed_list[i].get("transform_method", "NULL"),
                    "文本相似度": ts,
                    "测试指标一致性": ti,
                    "语义清晰度与表达准确性": sc,
                    "可评估性": kc,
                    "综合得分": comprehensive
                }
                evaluation_results.append(result)
                all_comprehensive_scores.append(comprehensive)

    # 将详细评估结果存储到输出文件
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, ensure_ascii=False, indent=4)

    # 计算所有变形题的平均综合得分
    if all_comprehensive_scores:
        avg_score = sum(all_comprehensive_scores) / len(all_comprehensive_scores)
    else:
        avg_score = 0
    print("平均综合得分：", avg_score)


if __name__ == "__main__":
    main()
