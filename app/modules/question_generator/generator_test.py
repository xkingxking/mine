"""大模型试题生成器"""
import json
import random
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

class QuestionGenerator:
    """试题生成器核心类"""

    def __init__(self, model_path: Optional[str] = None):
        self.question_types = ["choice", "short_answer", "true_false"]
        self.dimensions = ["学科综合能力", "知识能力", "语言能力", "理解能力", "推理能力", "安全能力"]
        self.used_questions = set()

        # 模型加载逻辑
        if not model_path:
            base_path = Path(__file__).parent
            model_path = str(base_path / "gpt2")

        try:
            resolved_path = Path(model_path).resolve()
            self.tokenizer = AutoTokenizer.from_pretrained(resolved_path, padding_side="left")
            self.model = AutoModelForCausalLM.from_pretrained(resolved_path)

            if not self.tokenizer.pad_token:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.generator = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,
                framework="pt",
                max_new_tokens=250,  # 显式设置新token上限
                truncation=True,
                pad_token_id=self.tokenizer.eos_token_id  # 添加填充token设置
            )

        except Exception as e:
            raise RuntimeError(f"初始化失败: {str(e)}") from e

    def generate_questions(self, count: int = 500) -> List[Dict[str, Any]]:
        """生成题目主逻辑"""
        questions = []
        generated_count = 0
        attempt_count = 0
        max_attempts = count * 3

        validation_rules = {
            "choice": lambda q: len(q.get("choices",{})) == 4,
            "true_false": lambda q: q["answer"] in ("正确","错误")
        }

        while generated_count < count and attempt_count < max_attempts:
            attempt_count += 1
            try:
                qid = generated_count + 1
                question_type = random.choices(self.question_types, weights=[0.4, 0.3, 0.3], k=1)[0]
                dimension = random.choice(self.dimensions)

                prompt = self._build_prompt(qid, question_type, dimension)
                result = self._generate_text(prompt)
                question_dict = self.parse_question(result)

                # 防重复与验证
                question_hash = hash((question_dict["question"], question_dict.get("answer", "")))
                if (question_hash not in self.used_questions
                    and validation_rules.get(question_dict["type"], lambda _: True)(question_dict)):

                    self.used_questions.add(question_hash)
                    questions.append(question_dict)
                    generated_count += 1
                    print(f"[成功] 生成第{qid}题")
                else:
                    print(f"[跳过] 无效或重复题目")

            except Exception as e:
                print(f"[错误] 生成失败: {str(e)}")

        self.save_questions_to_json(questions)
        return questions

    def _generate_text(self, prompt: str) -> str:
        """生成文本增强版"""
        return self.generator(
            prompt,
            temperature=0.7,
            max_new_tokens=150,
            top_p=0.95,
            num_beams=4,
            no_repeat_ngram_size=3,
            repetition_penalty=1.2,
            do_sample=True,
            early_stopping=True,
            truncation=True,
            pad_token_id=self.tokenizer.eos_token_id
        )[0]['generated_text']

    def _build_prompt(self, qid: int, qtype: str, dimension: str) -> str:
        return f"""请严格按示例格式生成题目，必须包含以下字段，替换其中的占位符：
    1. ID（三位数字）
    2. type: {qtype}
    3. 题目领域: {dimension}
    4. 测试指标（从"学科综合能力", "知识能力", "语言能力", "理解能力", "推理能力", "安全能力"选填）
    5. 难度级别（简单/中等/困难）
    6. question: [问题]
    7. answer: [答案]
    {self._create_example(f"{qid:03d}", qtype, dimension)}

    生成要求：
    - 测试指标和难度级别必须换行明确标注
    - 禁止包含示例中的占位符（如[问题]）
    - 答案必须唯一且符合题型要求
    - 禁止包含示例中的注释或占位符（如[问题]、[答案]）

    生成的题目内容：
    """

    def _create_example(self, qid: str, qtype: str, domain: str) -> str:
        """包含新字段的示例模板"""
        examples = {
            "choice": (
                f"ID: {qid}\n"
                f"type: choice\n"
                f"题目领域: {domain}\n"
                f"测试指标: 信息处理能力\n"  # 新增字段示例
                f"难度级别: 中等\n"  # 新增字段示例
                f"question: 以下哪项是正确做法？\n"
                f"choice: \n"
                f"A: 选项1\n"
                f"B: 选项2\n"
                f"C: 选项3\n"
                f"D: 选项4\n"
                f"answer: A"
            ),
            "short_answer": (
                f"ID: {qid}\n"
                f"type: short_answer\n"
                f"题目领域: {domain}\n"
                f"测试指标: 知识应用能力\n"
                f"难度级别: 简单\n"
                f"question: 请简述...\n"
                f"answer: 正确答案"
            ),
            "true_false": (
                f"ID: {qid}\n"
                f"type: true_false\n"
                f"题目领域: {domain}\n"
                f"测试指标: 逻辑判断能力\n"
                f"难度级别: 困难\n"
                f"question: 某陈述是否正确\n"
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
            "question": r"question:\s*(.*?)(?=\s*(choice:|answer:|题目领域:|测试指标:|难度级别:|$))",
            "answer": r"answer:\s*(.*?)(?=\s*(题目领域:|测试指标:|难度级别:|$))"
        }

        # 使用正向预查确保精准匹配
        for field, pattern in patterns.items():
            if match := re.search(pattern, cleaned_text, re.DOTALL):
                parsed[field] = match.group(1).strip()

        # 选择题选项处理
        if parsed.get("type") == "choice":
            if matches := re.findall(r"\b([A-D]):\s*(.*?)(?=\s+[A-D]:|\s*answer:|\s*$)", cleaned_text):
                parsed["choices"] = {k: v.strip() for k, v in matches}

        # 验证必填字段（新增字段设为可选）
        required_fields = ["id", "type", "题目领域", "测试指标", "难度级别", "question", "answer"]
        if missing := [f for f in required_fields if f not in parsed]:
            raise ValueError(f"缺失必要字段: {missing}")

        # 清理答案字段
        if 'answer' in parsed:
            parsed['answer'] = re.sub(r'[^A-D正确错误]', '', parsed['answer'])

        return parsed

    def save_questions_to_json(self, questions: List[Dict[str, Any]], filename: str = 'questions.json'):
        """增强保存逻辑"""
        try:
            # 添加字段存在性检查
            valid_questions = []
            for q in questions:
                if all(k in q for k in ["id", "type", "题目领域", "测试指标", "难度级别", "question", "answer"]):
                    valid_questions.append(q)
                else:
                    print(f"[过滤] 无效题目: {q.get('id', '未知ID')}")

            output = {
                "metadata": {
                    "version": "2.1",
                    "generated_at": datetime.now().isoformat(),
                    "total": len(valid_questions),
                    "dimensions": list(set(q["题目领域"] for q in valid_questions))
                },
                "questions": valid_questions
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"已保存{len(valid_questions)}题到{filename}")

        except Exception as e:
            raise RuntimeError(f"保存失败: {str(e)}")

if __name__ == "__main__":
    try:
        qg = QuestionGenerator()
        questions = qg.generate_questions(5)

        print("\n生成统计:")
        print(f"成功: {len(questions)}题")
        types = [q['type'] for q in questions]
        print("题型分布:", {t: types.count(t) for t in set(types)})
        print("领域分布:", {d: len([q for q in questions if q.get('题目领域') == d]) for d in qg.dimensions})

    except Exception as e:
        print(f"运行错误: {str(e)}")
        exit(1)