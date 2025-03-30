import os
import pytest
from dotenv import load_dotenv
from app.modules.model_client import ModelClient
from app.modules.models.model_factory import ModelFactory

# 加载环境变量
load_dotenv()

@pytest.mark.asyncio
async def test_api_keys():
    """测试API密钥是否正确配置并能正常使用"""
    # 检查环境变量是否存在
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    perspective_key = os.getenv('PERSPECTIVE_API_KEY')
    deepseek_model_name = os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-chat')
    
    print(f"当前工作目录: {os.getcwd()}")
    print(f"DEEPSEEK_API_KEY: {'已设置' if deepseek_key else '未设置'}")
    print(f"PERSPECTIVE_API_KEY: {'已设置' if perspective_key else '未设置'}")
    print(f"DEEPSEEK_MODEL_NAME: {deepseek_model_name}")
    
    assert deepseek_key is not None, "DEEPSEEK_API_KEY 未在环境变量中设置"
    assert perspective_key is not None, "PERSPECTIVE_API_KEY 未在环境变量中设置"
    assert len(deepseek_key) > 0, "DEEPSEEK_API_KEY 不能为空"
    assert len(perspective_key) > 0, "PERSPECTIVE_API_KEY 不能为空"
    
    # 测试DeepSeek API
    async with ModelClient("deepseek", api_key=deepseek_key, model_name=deepseek_model_name) as client:
        try:
            # 验证API密钥
            is_valid = await client.validate_api_key()
            assert is_valid, "DeepSeek API密钥无效"
            
            # 发送测试请求
            test_prompt = {
                "system": "你是一个专业的助手。",
                "user": "你好，这是一个测试问题。"
            }
            response = await client.send_prompt(test_prompt)
            assert response is not None, "DeepSeek API 响应为空"
            assert "content" in response, "DeepSeek API 响应格式不正确"
            print("DeepSeek API 测试成功")
            print(f"响应内容: {response['content']}")
            
        except Exception as e:
            pytest.fail(f"DeepSeek API 测试失败: {str(e)}")
    
    # 测试Perspective API
    try:
        # 创建Perspective模型实例
        perspective_model = ModelFactory.create_model(
            "perspective",
            api_key=perspective_key,
            model_name="perspective-api"
        )
        # 验证API密钥
        is_valid = await perspective_model.validate_api_key()
        assert is_valid, "Perspective API密钥无效"
        
        # 测试安全检查
        test_text = "Hello, this is a test message."
        safety_score = await perspective_model.check_safety(test_text)
        assert safety_score is not None, "Perspective API 响应为空"
        print(f"Perspective API 测试成功，安全分数: {safety_score}")
        
    except Exception as e:
        pytest.fail(f"Perspective API 测试失败: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api_keys()) 