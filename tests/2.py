import os
from openai import OpenAI

client = OpenAI(
    # 从环境变量中读取您的方舟API Key
    api_key="4727e524-c46f-4ac5-a278-2aaf9cea3273", 
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
completion = client.chat.completions.create(
    # 将推理接入点 <Model>替换为 Model ID
    model="doubao-1.5-pro-32k-250115",
    messages=[
        {"role": "user", "content": "你好，你是豆包吗？"}
    ]
)
print(completion.choices[0].message)