------

# 🧠 LLM 模型评估 SDK 使用说明

该 SDK 提供了统一的接口封装，用于通过后端 API 调用题库生成、题库变形、模型评估、报告下载与模型对比功能，帮助用户更方便地进行大语言模型能力评估。

## 📦 安装方式

确保你的环境已经安装了 Python 3.7+ 和 `requests` 库：

```bash
pip install requests
```

之后将 `mine_sdk.py` 文件克隆或下载到你的本地目录中。

## 🚀 快速开始

```python
from mine_sdk import MineSDK

sdk = MineSDK(base_url="http://localhost:5000")
```

------

## 🔍 API 使用说明

### 一、题库操作（Question Bank）

#### `list_question_banks()`

获取所有题库（基础题库 + 变形题库）及其元数据。

```python
banks = sdk.list_question_banks()
```

返回的内容包括：

- `baseBanks`: 原始题库列表
- `transformedBanks`: 变形题库列表
- 各题库包含 `id`, `name`, `metadata`（题目数、难度、维度等）

------

#### `create_question_bank(name, dimensions, difficulties, count, distribution="balanced")`

创建新的题库。

```python
sdk.create_question_bank(
    name="SDK创建题库",  # 在此为你创建的题库命名
    dimensions=["语言能力", "推理能力"],  # 可以选择填入的维度包括：
    difficulties=["easy", "medium"],  # 可以选择填入的难度包括：easy/medium/hard
    count=10  # 题目数量
)
```

- `distribution` 可选值：`balanced`, `random`, `custom`

------

#### `preview_question_bank(bank_id)`

获取指定题库的全部题目内容和元信息。

```python
qs = sdk.preview_question_bank("逻辑能力测试_20240413")  # 输入题库名称
```

------

#### `delete_question_bank(bank_id)`

删除指定题库。

```python
sdk.delete_question_bank("逻辑能力测试_20240413")
```

------

### 二、题库变形任务（Transformation）

#### `create_transform_task(task_name, source_file)`

根据已有题库文件创建变形任务。

```python
sdk.create_transform_task("task_01", source_file="逻辑能力测试_20240413.json")
```

------

#### `check_task_status(task_name, timeout=300)`

查询任务状态，直到完成或超时（默认 5 分钟）。

```python
status = sdk.check_task_status("task_01")
```

返回：

- `status`: 任务状态 (`completed`, `running`, `failed` 等)
- `progress`: 完成进度百分比

------

#### `list_all_tasks()`

列出所有任务及其状态。

```python
tasks = sdk.list_all_tasks()
```

------

#### `delete_transform_task(task_id)`

删除任务及生成的文件。

```python
sdk.delete_transform_task("task_01")
```

------

### 三、模型评估（Evaluation）

#### `evaluate_model(model_name, questions, dataset_path="")`

对模型进行评估，返回报告路径。

```python
report = sdk.evaluate_model("deepseek-v3", questions, dataset_path="逻辑能力测试_20240413")
```

- `questions`: 题库中的题目列表（通常来自 `preview_question_bank`）
- `dataset_path`: 使用的题库 ID（用于报告命名）

------

#### `get_report_content(report_filename)`

获取 JSON 报告文件内容。

```python
sdk.get_report_content("deepseek-v3_domains.json")
```

------

#### `download_report(report_filename, save_dir="./reports")`

下载 JSON 与 PDF 格式的评估报告到本地目录。

```python
sdk.download_report("deepseek-v3_domains.json")
```

返回路径：

```python
{
  "json": "./reports/deepseek-v3_domains.json",
  "pdf": "./reports/deepseek-v3_report.pdf"
}
```

------

### 四、模型对比（Model Comparison）

#### `compare_models()`

获取所有模型在各领域的横向对比评估结果。

```python
compare = sdk.compare_models()
```

返回示例：

```json
{
  "domains": ["语言能力", "知识能力"],
  "models": ["deepseek-v3", "gpt-4"],
  "scores": {
    "deepseek-v3": {
      "语言能力": {"average_score": 0.82, "total_evaluations": 100},
      ...
    }
  }
}
```

------

## 📑 示例文件

更多使用示例请参考项目中的 [`sdk_use.py`](https://chatgpt.com/c/sdk_use.py) 文件。

------

## 📬 联系我们

如有问题，请联系项目维护者或提交 Issue。

------

