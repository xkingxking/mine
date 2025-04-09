import os
from http import HTTPStatus
import dashscope


def call_with_messages():
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': '你好'}]
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-6b71622d6d294a2181dc6f47a0eba161",
        model='baichuan2-turbo', # 此处以baichuan2-turbo为例，可按需更换模型名称。模型列表：https://www.alibabacloud.com/help/zh/model-studio/getting-started/models
        messages=messages,
    )
    if response.status_code == HTTPStatus.OK:
        print(response)
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))

if __name__ == '__main__':
    call_with_messages()