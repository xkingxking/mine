# 请先安装 OpenAI SDK: `pip3 install openai httpx-socks`

from openai import OpenAI
import httpx
from httpx_socks import SyncProxyTransport

# 可用的 GPT-3.5 模型列表
AVAILABLE_MODELS = [
    "gpt-3.5-turbo",          # 最常用的模型，性价比高
    "gpt-3.5-turbo-0125",     # 2024年1月25日更新的版本
    "gpt-3.5-turbo-1106",     # 2023年11月6日更新的版本
    "gpt-3.5-turbo-16k",      # 支持16k上下文的版本
    "gpt-3.5-turbo-instruct"  # 专门用于指令跟随的版本
]

# 配置代理
proxy_url = "socks5://127.0.0.1:7890"  # 替换为您的代理地址
transport = SyncProxyTransport.from_url(proxy_url)
http_client = httpx.Client(transport=transport)

# 使用 OpenAI 的官方 API URL
client = OpenAI(
    api_key="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",  # 替换为您的 OpenAI API 密钥
    base_url="https://api.openai.com/v1",  # OpenAI 官方 API URL
    http_client=http_client  # 使用配置了代理的 http_client
)

# 选择要使用的模型
selected_model = AVAILABLE_MODELS[0]  # 默认使用第一个模型

response = client.chat.completions.create(
    model=selected_model,  # 使用选择的模型
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "你好"},
    ],
    stream=False
)

print(f"使用的模型: {selected_model}")
print("模型响应:")
print(response.choices[0].message.content)