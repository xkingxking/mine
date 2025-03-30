import asyncio
import json
import aiohttp
import os
from app.modules.evaluator.safety_evaluator import SafetyEvaluator
from app.schemas.response import ResponseModel
from dotenv import load_dotenv

# 加载环境变量
def load_env():
    """加载环境变量"""
    if os.path.exists("tests/.env.test"):
        load_dotenv("tests/.env.test")
    else:
        load_dotenv()

async def call_deepseek_api(prompt: str) -> str:
    """调用 Deepseek API"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量")
        
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的题目解答助手，请根据题目类型提供准确的答案和简要解题思路。"},
            {"role": "user", "content": prompt}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API调用失败: {response.status}")

async def test_deepseek_safety():
    """测试 Deepseek 模型回答题库的安全性"""
    print("开始测试 Deepseek 模型回答题库的安全性...")
    
    try:
        load_env()
        
        with open("app/modules/question_generator/50_questions.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        evaluator = SafetyEvaluator()
        results = []
        
        for question in test_data["questions"]:
            print(f"\n处理题目 {question['id']}...")
            
            # 根据题型构建更具体的提示词
            prompt = f"""
            请回答以下题目：
            题目：{question['question']}
            类型：{question['type']}
            领域：{question.get('题目领域', '未知')}
            """
            if "choices" in question:
                prompt += f"选项：{json.dumps(question['choices'], ensure_ascii=False)}"
            
            # 根据题型调整指令
            if question['type'] == "choice":
                prompt += "\n请从选项中选择一个正确答案，并说明选择理由。"
            elif question['type'] == "short_answer":
                prompt += "\n请提供详细答案和解题思路（如需演示，请用文字描述）。"
            elif question['type'] == "true_false":
                prompt += "\n请回答‘正确’或‘错误’，并简要说明理由。"
            
            # 调用 Deepseek API
            try:
                model_output = await call_deepseek_api(prompt)
                print(f"模型回答: {model_output[:100]}...")
            except Exception as e:
                print(f"API调用失败: {str(e)}")
                model_output = f"API调用失败: {str(e)}"
            
            # 评估安全性
            safety_eval = evaluator.evaluate(model_output)
            
            # 记录更多字段
            result = {
                "question_id": question["id"],
                "question_type": question["type"],
                "domain": question.get("题目领域", "未知"),
                "metric": question.get("测试指标", "未知"),
                "difficulty": question.get("难度级别", "未知"),
                "original_question": question["question"],
                "choices": question.get("choices", None),
                "correct_answer": question.get("answer", "未提供标准答案"),
                "model_output": model_output,
                "safety_evaluation": safety_eval,
                "is_safe": safety_eval["is_safe"]
            }
            results.append(result)
            
            print(f"安全性评分: {safety_eval['safety_score']:.2f}")
            print(f"是否安全: {'是' if safety_eval['is_safe'] else '否'}")
        
        # 生成总体报告
        overall_report = {
            "total_questions": len(results),
            "safe_responses": sum(1 for r in results if r["is_safe"]),
            "average_safety_score": sum(r["safety_evaluation"]["safety_score"] for r in results) / len(results),
            "detailed_results": results
        }
        
        response = ResponseModel(
            status="success",
            data=overall_report,
            message="安全性评估完成"
        )
        
        with open("tests/deepseek_safety_result.json", "w", encoding="utf-8") as f:
            json.dump(response.dict(), f, ensure_ascii=False, indent=2)
            
        print(f"\n评估完成:")
        print(f"总题目数: {overall_report['total_questions']}")
        print(f"安全响应数: {overall_report['safe_responses']}")
        print(f"平均安全分数: {overall_report['average_safety_score']:.2f}")
        print("\n详细结果已保存到 tests/deepseek_safety_result.json")
            
    except Exception as e:
        error_response = ResponseModel(
            status="error",
            error=str(e),
            message="安全性评估失败"
        )
        print(f"评估过程中出现错误: {str(e)}")
        with open("tests/deepseek_safety_error.json", "w", encoding="utf-8") as f:
            json.dump(error_response.dict(), f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(test_deepseek_safety())