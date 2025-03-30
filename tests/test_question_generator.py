import asyncio
from app.modules.generator.question_generator import QuestionGenerator
from app.schemas.question import Question

async def test_generate_questions():
    """测试题目生成功能"""
    print("开始测试题目生成...")
    
    # 初始化生成器
    generator = QuestionGenerator()
    
    try:
        # 测试单题生成
        print("\n1. 测试单题生成:")
        questions = await generator.generate(
            prompt="Python编程基础",
            count=1
        )
        print(f"生成题目数量: {len(questions)}")
        print(f"题目内容: {questions[0].content}")
        print(f"题目类型: {questions[0].type}")
        print(f"题目难度: {questions[0].difficulty}")
        
        # 测试批量生成
        print("\n2. 测试批量生成:")
        questions = await generator.generate_questions(count=3)
        print(f"生成题目数量: {len(questions)}")
        for i, q in enumerate(questions, 1):
            print(f"\n题目 {i}:")
            print(f"内容: {q.get('content', 'N/A')}")
            print(f"类型: {q.get('type', 'N/A')}")
            print(f"难度: {q.get('difficulty', 'N/A')}")
            
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_generate_questions()) 