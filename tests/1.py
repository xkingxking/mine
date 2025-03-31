import requests

url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
params = {
    "key": "AIzaSyB5ut4szJ7itMv4NFCleLF87EcVvoGgKI4"
}
data = {
    "comment": {"text": "Hello world"},
    "requestedAttributes": {"TOXICITY": {}}
}
response = requests.post(url, params=params, json=data)
print("状态码:", response.status_code)
print("响应内容:")
print(response.json())