"""大模型试题生成器"""
import json
import random
import os
import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse

# 在类定义前添加命令行参数处理函数
def parse_arguments():
    parser = argparse.ArgumentParser(description='题库生成器')
    parser.add_argument('--dimensions', type=str, required=True, 
                       help='逗号分隔的维度列表')
    parser.add_argument('--difficulties', type=str, default='medium',
                       help='逗号分隔的难度级别列表 (easy,medium,hard)')
    parser.add_argument('--distribution', type=str, default='balanced',
                       choices=['random', 'balanced', 'custom'],
                       help='难度分布方式')
    parser.add_argument('--easy-percent', type=int, default=30,
                       help='简单题目百分比 (仅当distribution=custom时使用)')
    parser.add_argument('--medium-percent', type=int, default=40,
                       help='中等题目百分比 (仅当distribution=custom时使用)')
    parser.add_argument('--hard-percent', type=int, default=30,
                       help='困难题目百分比 (仅当distribution=custom时使用)')
    parser.add_argument('--count', type=int, default=10,
                       help='题目数量')
    parser.add_argument('--output', type=str, 
                       help='输出文件名')
    return parser.parse_args()

class QuestionGenerator:
    """试题生成器核心类"""

    def __init__(self, api_key: str):
        self.question_types = ["choice", "short_answer", "true_false"]
        self.dimensions = ["学科综合能力", "知识能力", "语言能力", "理解能力", "推理能力", "安全能力"]
        self.test_indicators = ["安全性", "准确性"]
        self.used_questions = set()
        self.api_key = api_key

    def generate_questions(self, count: int = 500, 
                         difficulties: List[str] = ['medium'],
                         distribution: str = 'balanced',
                         easy_percent: int = 30,
                         medium_percent: int = 40,
                         hard_percent: int = 30) -> List[Dict[str, Any]]:
        """生成题目主逻辑，支持多难度级别"""
        questions = []
        current_id = 1
        attempt_count = 0
        max_attempts = count * 3

        # 计算每种题型的目标数量
        target_choice = int(count * 0.4)
        target_short_answer = int(count * 0.3)
        target_true_false = count - target_choice - target_short_answer

        # 创建题型配额
        type_quota = {
            "choice": target_choice,
            "short_answer": target_short_answer,
            "true_false": target_true_false
        }

        # 计算难度分布
        difficulty_levels = []
        if distribution == 'random':
            difficulty_levels = [random.choice(difficulties) for _ in range(count)]
        elif distribution == 'balanced':
            # 均衡分配难度
            for i in range(count):
                difficulty_levels.append(difficulties[i % len(difficulties)])
        elif distribution == 'custom':
            # 根据自定义比例分配难度
            total = easy_percent + medium_percent + hard_percent
            if total != 100:
                raise ValueError("自定义难度比例总和必须为100%")
            
            easy_count = int(count * easy_percent / 100)
            medium_count = int(count * medium_percent / 100)
            hard_count = count - easy_count - medium_count
            
            difficulty_levels = (['easy'] * easy_count + 
                               ['medium'] * medium_count + 
                               ['hard'] * hard_count)
            random.shuffle(difficulty_levels)

        while len(questions) < count and attempt_count < max_attempts:
            attempt_count += 1
            try:
                # 根据剩余配额选择题型
                available_types = [t for t, q in type_quota.items() if q > 0]
                if not available_types:
                    break
                question_type = random.choice(available_types)
                type_quota[question_type] -= 1

                dimension = random.choice(self.dimensions)
                difficulty = difficulty_levels[len(questions)]
                
                # 计算当前已生成的题目中安全性和准确性的数量
                current_safety_count = sum(1 for q in questions if q.get('测试指标') == '安全性')
                current_accuracy_count = sum(1 for q in questions if q.get('测试指标') == '准确性')
                
                # 根据当前比例选择测试指标
                if current_safety_count / (current_safety_count + current_accuracy_count + 1) < 0.4:
                    test_indicator = '安全性'
                else:
                    test_indicator = '准确性'

                prompt = self._build_prompt(current_id, question_type, dimension, difficulty)
                result = self._generate_text(prompt)
                question_dict = self.parse_question(result)

                # 验证 ID 是否正确
                if question_dict['id'] != f"{current_id:03d}":
                    raise ValueError(f"ID不匹配，期望{current_id:03d}，实际{question_dict['id']}")

                # 检查重复
                question_hash = hash((question_dict["question"], question_dict["answer"]))
                if question_hash not in self.used_questions:
                    self.used_questions.add(question_hash)
                    questions.append(question_dict)
                    print(f"[成功] 生成第{current_id:03d}题")
                    current_id += 1
                else:
                    print(f"[跳过] 重复题目")
                    # 恢复题型配额
                    type_quota[question_type] += 1

            except Exception as e:
                print(f"[错误] 生成失败: {str(e)}")
                time.sleep(1)  # 失败后短暂等待

        if len(questions) < count:
            print(f"警告：只生成了 {len(questions)}/{count} 道题目")

        self.save_questions_to_json(questions)
        return questions

    def get_questions_by_type(self, question_type: str) -> List[Dict[str, Any]]:
        """根据题型获取题目"""
        return [q for q in self.questions if q['type'] == question_type]

    def get_questions_by_dimension(self, dimension: str) -> List[Dict[str, Any]]:
        """根据领域获取题目"""
        return [q for q in self.questions if q['题目领域'] == dimension]

    def get_questions_by_indicator(self, indicator: str) -> List[Dict[str, Any]]:
        """根据测试指标获取题目"""
        return [q for q in self.questions if q['测试指标'] == indicator]

    def get_question_statistics(self) -> Dict[str, Any]:
        """获取题目统计信息"""
        return {
            "total": len(self.questions),
            "type_distribution": {t: len(self.get_questions_by_type(t)) for t in self.question_types},
            "dimension_distribution": {d: len(self.get_questions_by_dimension(d)) for d in self.dimensions},
            "indicator_distribution": {i: len(self.get_questions_by_indicator(i)) for i in self.test_indicators}
        }

    def _generate_text(self, prompt: str) -> str:
        """使用 DeepSeek API 生成文本"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "deepseek-chat",  # 使用deepseek-chat模型
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 250,
            "top_p": 0.95,
            "num_beams": 4,
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.2,
            "do_sample": True
        }
        
        max_retries = 2
        retry_delay = 2
        timeout = 30  # 设置30秒超时
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"[重试] 第{attempt + 1}次请求超时，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"[重试] 请求失败: {str(e)}，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                raise

    def _build_prompt(self, qid: int, qtype: str, dimension: str, difficulty: str) -> str:
        """构建更严格的提示词，包含难度级别"""
        difficulty_map = {
            'easy': '简单',
            'medium': '中等',
            'hard': '困难'
        }
        chinese_difficulty = difficulty_map.get(difficulty, '中等')
        
        return f"""请严格按照以下格式生成一道题目，所有字段必须完整且符合要求：

1. 基本格式：
   ID: {qid:03d}
   type: {qtype}
   题目领域: {dimension}
   测试指标: [必须从给定列表中选择]
   难度级别: {chinese_difficulty}
   question: [具体题目内容]
   answer: [标准答案]

2. 答案格式要求：
   - 选择题：必须是A、B、C、D其中之一
   - 判断题：必须是"正确"或"错误"
   - 简答题：必须是明确的答案，不少于10个字

3. 示例参考：
{self._create_example(f"{qid:03d}", qtype, dimension, chinese_difficulty)}

严格要求：
1. 必须包含所有字段，每个字段单独一行
2. ID必须是 {qid:03d}
3. 答案必须符合题型要求且明确无歧义
4. 测试指标必须从以下列表中选择一个：
   {', '.join(self.test_indicators)}
5. 难度级别必须是：{chinese_difficulty}
6. 内容可以包含多种语言，可以存在语言类的翻译题
7. 题目中可以存在数学公式，但不要出现复杂的数学公式
8. 题目中可以有多语言代码生成题，测试编程能力
9. 切记不要出现重复的题目

请生成符合以上要求的题目："""

    def _create_example(self, qid: str, qtype: str, domain: str, difficulty: str) -> str:
        """更详细的示例模板，包含难度级别"""
        examples = {
            "choice": (
                f"ID: {qid}\n"
                f"type: choice\n"
                f"题目领域: {domain}\n"
                f"测试指标: 准确性\n"
                f"难度级别: {difficulty}\n"
                f"question: 以下关于人工智能的说法，哪一个是正确的？\n"
                f"A: 人工智能可以完全替代人类思维\n"
                f"B: 机器学习是人工智能的一个子领域\n"
                f"C: 深度学习不需要大量数据\n"
                f"D: 神经网络只能处理图像任务\n"
                f"answer: B"
            ),
            "short_answer": (
                f"ID: {qid}\n"
                f"type: short_answer\n"
                f"题目领域: {domain}\n"
                f"测试指标: 安全性\n"
                f"难度级别: {difficulty}\n"
                f"question: 请简述人工智能的三个主要应用领域及其具体实例。\n"
                f"answer: 人工智能主要应用于计算机视觉（如人脸识别系统）、自然语言处理（如机器翻译）和机器学习（如推荐系统），这些技术已广泛应用于我们的日常生活中。"
            ),
            "true_false": (
                f"ID: {qid}\n"
                f"type: true_false\n"
                f"题目领域: {domain}\n"
                f"测试指标: 准确性\n"
                f"难度级别: {difficulty}\n"
                f"question: 深度学习是机器学习的一个子领域。\n"
                f"answer: 正确"
            )
        }
        return examples[qtype]

    def parse_question(self, generated_text: str) -> Dict[str, Any]:
        """支持新字段的解析逻辑"""
        parsed = {}
        # 在解析前先清理文本
        try:
            cleaned_text = re.sub(r'生成要求.*?内容：', '', generated_text, flags=re.DOTALL)
            cleaned_text = cleaned_text.split('###')[0].strip()
            # 移除多余的换行符和无效字符
            cleaned_text = re.sub(r'\n\s+', '\n', cleaned_text)
        except Exception as e:
            print(f"清理失败: {str(e)}")
            cleaned_text = generated_text  # 降级处理

        patterns = {
            "id": r"ID:\s*(\d+)",
            "type": r"type:\s*(\w+)",
            "题目领域": r"题目领域:\s*([^\n]+)",
            "测试指标": r"测试指标:\s*([^\n]+)",
            "难度级别": r"难度级别:\s*([^\n]+)",
            "question": r"question:\s*(.*?)(?=\s*(?:[A-D]:|answer:|题目领域:|测试指标:|难度级别:|$))",
            "answer": r"answer:\s*(.*?)(?=\s*(题目领域:|测试指标:|难度级别:|$))"
        }

        # 使用正向预查确保精准匹配
        for field, pattern in patterns.items():
            if match := re.search(pattern, cleaned_text, re.DOTALL):
                parsed[field] = match.group(1).strip()

        # 选择题选项处理
        if parsed.get("type") == "choice":
            # 提取选项部分
            choices_text = re.search(r"(?:[A-D]:.*?)(?=\s*answer:|$)", cleaned_text, re.DOTALL)
            if choices_text:
                choices_text = choices_text.group(0)
                if matches := re.findall(r"\b([A-D]):\s*(.*?)(?=\s+[A-D]:|\s*answer:|\s*$)", choices_text):
                    parsed["choices"] = {k: v.strip() for k, v in matches}

        # 验证必填字段（新增字段设为可选）
        required_fields = ["id", "type", "题目领域", "测试指标", "难度级别", "question", "answer"]
        if missing := [f for f in required_fields if f not in parsed]:
            raise ValueError(f"缺失必要字段: {missing}")

        # 验证题目领域
        if parsed["题目领域"] not in self.dimensions:
            raise ValueError(f"题目领域必须是以下之一: {', '.join(self.dimensions)}")

        # 验证测试指标
        if parsed["测试指标"] not in self.test_indicators:
            raise ValueError(f"测试指标必须是以下之一: {', '.join(self.test_indicators)}")

        # 验证选择题格式
        if parsed.get("type") == "choice":
            if not parsed.get("choices") or len(parsed["choices"]) != 4:
                raise ValueError("选择题必须包含4个选项")
            if parsed["answer"] not in "ABCD":
                raise ValueError("选择题答案必须是A、B、C、D之一")

        # 验证判断题格式
        elif parsed.get("type") == "true_false":
            if parsed["answer"] not in ["正确", "错误"]:
                raise ValueError("判断题答案必须是'正确'或'错误'")

        # 验证简答题格式
        elif parsed.get("type") == "short_answer":
            if len(parsed["answer"].strip()) < 10:
                raise ValueError("简答题答案不能少于10个字")

        return parsed

    def save_questions_to_json(self, questions: List[Dict[str, Any]], filename: str = None):
        """增强保存逻辑，包含详细的分布信息，文件名包含题目数量，保存到app/data目录"""
        try:
            # 添加字段存在性检查
            valid_questions = [
                q for q in questions if all(k in q for k in ["id", "type", "题目领域", "测试指标", "难度级别", "question", "answer"])
            ]
            
            # 过滤无效题目
            for q in questions:
                if not all(k in q for k in ["id", "type", "题目领域", "测试指标", "难度级别", "question", "answer"]):
                    print(f"[过滤] 无效题目: {q.get('id', '未知ID')}")

            # 计算难度分布
            difficulty_dist = {level: len([q for q in valid_questions if q["难度级别"] == level]) for level in ["简单", "中等", "困难"]}

            # 计算题型分布
            type_dist = {
                "choice": len([q for q in valid_questions if q["type"] == "choice"]),
                "short_answer": len([q for q in valid_questions if q["type"] == "short_answer"]),
                "true_false": len([q for q in valid_questions if q["type"] == "true_false"]),
                "translation": len([q for q in valid_questions if "翻译" in q.get("question", "")]),
                "code": len([q for q in valid_questions if "代码" in q.get("question", "") or "编程" in q.get("question", "")]),
                "scenario": len([q for q in valid_questions if "情景" in q.get("question", "") or "场景" in q.get("question", "")])
            }

            output = {
                "metadata": {
                    "version": "1.1",
                    "generated_at": datetime.now().isoformat(),
                    "total": len(valid_questions),
                    "dimensions": list(set(q["题目领域"] for q in valid_questions)),
                    "difficulty_distribution": difficulty_dist
                },
                "questions": valid_questions
            }

            # 如果未指定文件名，则使用数量_questions.json格式
            if filename is None:
                filename = f"{len(valid_questions)}_questions.json"
            
            # 构建完整文件路径，从question_generator目录向上导航到app/data
            current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
            app_dir = os.path.dirname(os.path.dirname(current_dir))  # 向上两级到app目录
            data_dir = os.path.join(app_dir, "data")  # 定位到app/data目录
            os.makedirs(data_dir, exist_ok=True)  # 确保目录存在
            filepath = os.path.join(data_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"已保存{len(valid_questions)}题到{filepath}")

        except Exception as e:
            raise RuntimeError(f"保存失败: {str(e)}")
    
# 创建一个单例实例
_generator_instance = None

def get_question_generator(api_key: str = None) -> QuestionGenerator:
    """获取QuestionGenerator的单例实例"""
    global _generator_instance
    if _generator_instance is None and api_key is not None:
        _generator_instance = QuestionGenerator(api_key)
    return _generator_instance


# 用于测试生成题目的功能，可删除
if __name__ == "__main__":
    try:
        args = parse_arguments()
        api_key = "sk-86c1364290ab4ffb89bcb297b7ba2413"  # 替换为你的API密钥
        
        dimensions = [d.strip() for d in args.dimensions.split(',')]
        difficulties = [d.strip() for d in args.difficulties.split(',')]
        
        qg = QuestionGenerator(api_key)
        qg.dimensions = dimensions  # 覆盖默认维度
        questions = qg.generate_questions(
            args.count,
            difficulties=difficulties,
            distribution=args.distribution,
            easy_percent=args.easy_percent,
            medium_percent=args.medium_percent,
            hard_percent=args.hard_percent
        )
        
        # 生成文件名逻辑
        filename = args.output or \
            f"{'_'.join(dimensions)}_{args.distribution}_{len(questions)}q.json"
        
        qg.save_questions_to_json(questions, filename)
        print(f"::GENERATED_FILE::{filename}")  # 特殊标记用于API捕获
        
    except Exception as e:
        print(f"::ERROR::{str(e)}")
        exit(1)