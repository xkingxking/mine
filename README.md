# 大模型性能与安全观测平台

## 项目简介
本项目是一个综合性的平台，用于观测和评估大语言模型的性能与安全性。平台提供题库生成、数据审核、结果分析等功能，支持多种调用方式。

## 主要功能
1. 题库生成模块
   - 自动化生成大模型性能观测题库
   - 支持多种题型（选择、简答、判断等）
   - 题库规模不低于500题

2. 题库拓展模块
   - 支持多种题目变形方式
   - 变形题目有效性保证

3. 数据审核模块
   - 自动审核测试结果
   - 多维度结果展示

4. 结果生成模块
   - 性能指标统计
   - 安全性评估
   - 资源消耗分析

5. 自动化报告生成
   - 支持多种报告格式
   - 可下载和审阅

6. 多样化调用支持
   - SDK支持
   - SaaS服务

## 环境要求
- Python 3.8+
- Redis (用于任务队列)
- 各种大模型的 API 密钥

## 安装步骤

1. 克隆项目
```bash
git clone <项目地址>
cd <项目目录>
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件，添加必要的环境变量：
```
# 数据库配置
DATABASE_URL=你的数据库URL

# Redis配置
REDIS_URL=你的Redis URL

# API Keys
OPENAI_API_KEY=你的OpenAI API密钥
DEEPSEEK_API_KEY=你的Deepseek API密钥
DOUBAO_API_KEY=你的豆包API密钥
QWEN_API_KEY=你的通义千问API密钥
LLAMA_API_KEY=你的Llama API密钥
BAICHUAN_API_KEY=你的百川API密钥

# 其他配置
SECRET_KEY=你的密钥
```

## 运行项目

1. 启动 Redis 服务

2. 运行主程序
```bash
python app/main.py
```

3. 运行 API 服务
```bash
python app/api/main.py
```

## 使用说明

1. 准备测试问题
将测试问题保存在 JSON 文件中，格式如下：
```json
[
  {
    "content": "问题内容",
    "type": "问题类型",
    "domain": "领域",
    "difficulty": "难度",
    "choices": ["选项1", "选项2", "选项3", "选项4"]
  }
]
```

2. 运行测试
```bash
python app/main.py --model <模型名称> --questions <问题文件路径>
```

支持的模型：
- openai
- deepseek
- doubao
- qwen
- llama


## 技术架构
- 后端：FastAPI
- 数据库：PostgreSQL
- 前端：Vue.js
- 部署：Docker

## 贡献指南
[待补充]

## 许可证
MIT License 